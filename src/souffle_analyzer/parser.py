from __future__ import annotations

from typing import TypeVar

import tree_sitter as ts
import tree_sitter_souffle

from souffle_analyzer.ast import (
    AbstractDataTypeBranch,
    AbstractDataTypeExpression,
    Argument,
    Atom,
    Attribute,
    BinaryConstraint,
    BinaryConstraintOp,
    BinaryOperation,
    BinaryOperator,
    BlockComment,
    BranchInit,
    BranchInitName,
    Clause,
    Comment,
    Conjunction,
    Constant,
    Directive,
    DirectiveQualifier,
    Disjunction,
    Document,
    ErrorNode,
    Fact,
    Identifier,
    LineComment,
    Location,
    NegOp,
    NumberConstant,
    Position,
    PreprocInclude,
    QualifiedName,
    Range,
    RecordInit,
    RecordTypeExpression,
    RelationDeclaration,
    RelationReference,
    RelationReferenceClause,
    RelationReferenceName,
    ResultNode,
    Rule,
    RuleHead,
    StringConstant,
    SubsumptionHead,
    SyntaxIssue,
    TypeDeclaration,
    TypeDeclarationOp,
    TypeExpression,
    TypeReference,
    TypeReferenceName,
    TypeRelationOpKind,
    UnionTypeExpression,
    UnresolvedType,
    ValidNode,
    Variable,
)
from souffle_analyzer.logging import logger


class Parser:
    def __init__(self, uri: str, code: bytes):
        souffle_language = ts.Language(tree_sitter_souffle.language())
        self.parser = ts.Parser(souffle_language)
        self.uri = uri
        self.code = code

    def parse(self) -> Document:
        tree = self.parser.parse(self.code)
        document = self.parse_document(tree.root_node, self.code)
        return document

    def get_text(self, node: ts.Node) -> str:
        return node.text.decode() if node.text else ""

    def get_location(self, node: ts.Node) -> Location:
        return Location(
            uri=self.uri,
            range_=Range(
                start=Position(
                    line=node.start_point[0],
                    character=node.start_point[1],
                ),
                end=Position(
                    line=node.end_point[0],
                    # Tree-sitter range-end character on a line is always exclusive.
                    character=node.end_point[1],
                ),
            ),
        )

    def get_child_of_type(self, node: ts.Node, child_type: str) -> ts.Node | None:
        child = next((_ for _ in node.children if _.type == child_type), None)
        return child

    def get_children_of_type(self, node: ts.Node, child_type: str) -> list[ts.Node]:
        return [_ for _ in node.children if _.type == child_type]

    def collect_syntax_issues(
        self,
        node: ts.Node,
        message: str | None = None,
    ) -> list[SyntaxIssue]:
        syntax_errors = []
        for child in node.children:
            if child.grammar_name == "ERROR":
                syntax_errors.append(
                    SyntaxIssue(
                        location=self.get_location(node),
                        message=message,
                    )
                )
        return syntax_errors

    def parse_document(self, node: ts.Node, code: bytes) -> Document:
        relation_declarations = [
            self.parse_relation_declaration(_)
            for _ in self.get_children_of_type(node, "relation_decl")
        ]
        type_declarations = [
            self.parse_type_declaration(_)
            for _ in self.get_children_of_type(node, "type_decl")
        ]
        facts = [self.parse_fact(_) for _ in self.get_children_of_type(node, "fact")]
        rules = [self.parse_rule(_) for _ in self.get_children_of_type(node, "rule")]
        directives = [
            self.parse_directive(_)
            for _ in self.get_children_of_type(node, "directive")
        ]
        preprocessor_directives = list(
            filter(
                None,
                [
                    self.parse_preprocessor_directive(_)
                    for _ in self.get_children_of_type(node, "preproc_directive")
                ],
            )
        )
        block_comments = [
            self.parse_block_comment(_)
            for _ in self.get_children_of_type(node, "block_comment")
        ]
        line_comments = [
            self.parse_line_comment(_)
            for _ in self.get_children_of_type(node, "line_comment")
        ]
        line_comments = self.chunk_line_comments(line_comments)

        comments: list[Comment] = [*block_comments, *line_comments]

        for relation_declaration in relation_declarations:
            for comment in comments:
                if (
                    comment.range_.end.line + 1
                    == relation_declaration.range_.start.line
                ):
                    relation_declaration.parse_doc_comment(comment)

        return Document(
            code=code.decode(),
            location=self.get_location(node),
            relation_declarations=relation_declarations,
            type_declarations=type_declarations,
            facts=facts,
            rules=rules,
            directives=directives,
            preprocessor_directives=preprocessor_directives,
            comments=comments,
        )

    def parse_relation_declaration(self, node: ts.Node) -> RelationDeclaration:
        name_node = node.child_by_field_name("name")
        if not name_node:
            name: ResultNode[Identifier] = ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing name",
                ),
            )
        else:
            name = ResultNode(
                location=self.get_location(name_node),
                inner=self.parse_identifier(name_node),
            )
        attribute_nodes = [_ for _ in node.named_children if _.type == "attribute"]
        attributes = [self.parse_attribute(_) for _ in attribute_nodes]

        return RelationDeclaration(
            location=self.get_location(node),
            name=name,
            attributes=attributes,
        )

    def parse_type_declaration(self, node: ts.Node) -> TypeDeclaration:
        name_node = self.get_child_of_type(node, "identifier")
        if not name_node:
            name: ResultNode[Identifier] = ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing type name",
                ),
            )
        else:
            name = ResultNode(
                location=self.get_location(name_node),
                inner=self.parse_identifier(name_node),
            )
        subtype_node = self.get_child_of_type(node, "subtype_decl")
        eq_type_node = self.get_child_of_type(node, "eq_type_decl")
        if subtype_node is not None:
            op_node = subtype_node.child_by_field_name("type_relation_op")
            if op_node is None:
                op: ResultNode[TypeDeclarationOp] = ResultNode(
                    location=self.get_location(node),
                    inner=ErrorNode(
                        location=self.get_location(node),
                        msg="Missing type declaration operator",
                    ),
                )
            else:
                op = ResultNode(
                    location=self.get_location(op_node),
                    inner=TypeDeclarationOp(
                        location=self.get_location(op_node),
                        op=TypeRelationOpKind.SUBTYPE,
                    ),
                )

            type_name_node = self.get_child_of_type(subtype_node, "type_name")
            if type_name_node is None:
                type_name: ResultNode[TypeReference] = ResultNode(
                    location=self.get_location(node),
                    inner=ErrorNode(
                        location=self.get_location(node),
                        msg="Missing type declaration operator",
                    ),
                )
            else:
                type_name = ResultNode(
                    location=self.get_location(type_name_node),
                    inner=self.parse_type_reference(type_name_node),
                )

            return TypeDeclaration(
                location=self.get_location(node),
                name=name,
                op=op,
                expression=type_name,
            )
        if eq_type_node is not None:
            op_node = eq_type_node.child_by_field_name("type_relation_op")
            if op_node is None:
                op = ResultNode(
                    location=self.get_location(node),
                    inner=ErrorNode(
                        location=self.get_location(node),
                        msg="Missing type declaration operator",
                    ),
                )
            else:
                op = ResultNode(
                    location=self.get_location(op_node),
                    inner=TypeDeclarationOp(
                        location=self.get_location(op_node),
                        op=TypeRelationOpKind.EQUIVALENT_TYPE,
                    ),
                )

            union_type_node = self.get_child_of_type(eq_type_node, "union_type")
            type_name_node = self.get_child_of_type(eq_type_node, "type_name")
            record_type_node = self.get_child_of_type(eq_type_node, "record_type")
            abstract_data_type_node = self.get_child_of_type(
                eq_type_node, "abstract_data_type"
            )

            if union_type_node is not None:
                type_expression: ResultNode[TypeExpression] = ResultNode(
                    location=self.get_location(union_type_node),
                    inner=self.parse_union_type_expression(union_type_node),
                )
            elif type_name_node is not None:
                type_expression = ResultNode(
                    location=self.get_location(type_name_node),
                    inner=self.parse_type_reference(type_name_node),
                )
            elif record_type_node is not None:
                type_expression = ResultNode(
                    location=self.get_location(record_type_node),
                    inner=self.parse_record_type_expression(record_type_node),
                )
            elif abstract_data_type_node is not None:
                type_expression = ResultNode(
                    location=self.get_location(abstract_data_type_node),
                    inner=self.parse_abstract_data_type_expression(
                        abstract_data_type_node
                    ),
                )
            else:
                type_expression = ResultNode(
                    location=self.get_location(node),
                    inner=ErrorNode(
                        location=self.get_location(node),
                        msg="Missing type expression",
                    ),
                )
            return TypeDeclaration(
                location=self.get_location(node),
                name=name,
                op=op,
                expression=type_expression,
            )
        return TypeDeclaration(
            location=self.get_location(node),
            name=name,
            op=ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing type declaration operator",
                ),
            ),
            expression=ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing type declaration expression",
                ),
            ),
        )

    def parse_directive(self, node: ts.Node) -> Directive:
        qualifier_node = self.get_child_of_type(node, "directive_qualifier")
        if qualifier_node is None:
            raise ParserError()  # should not happen
        relation_name_nodes = self.get_children_of_type(node, "qualified_name")
        relation_names = [
            self.parse_qualified_name(_, RelationReferenceName)
            for _ in relation_name_nodes
        ]
        return Directive(
            location=self.get_location(node),
            qualifier=self.parse_directive_qualifier(qualifier_node),
            relation_names=relation_names,
        )

    def parse_directive_qualifier(self, node: ts.Node) -> DirectiveQualifier:
        keyword = self.get_text(node)
        return DirectiveQualifier(
            location=self.get_location(node),
            keyword=keyword,
        )

    def parse_union_type_expression(self, node: ts.Node) -> UnionTypeExpression:
        type_reference_nodes = self.get_children_of_type(node, "type_name")
        return UnionTypeExpression(
            location=self.get_location(node),
            types=[self.parse_type_reference(_) for _ in type_reference_nodes],
        )

    def parse_record_type_expression(self, node: ts.Node) -> RecordTypeExpression:
        attribute_nodes = self.get_children_of_type(node, "attribute")
        return RecordTypeExpression(
            location=self.get_location(node),
            attributes=[self.parse_attribute(_) for _ in attribute_nodes],
        )

    def parse_abstract_data_type_expression(
        self, node: ts.Node
    ) -> AbstractDataTypeExpression:
        branch_nodes = self.get_children_of_type(node, "adt_branch")
        return AbstractDataTypeExpression(
            location=self.get_location(node),
            branches=[self.parse_abstract_data_type_branch(_) for _ in branch_nodes],
        )

    def parse_abstract_data_type_branch(self, node: ts.Node) -> AbstractDataTypeBranch:
        name_node = self.get_child_of_type(node, "identifier")
        if name_node is None:
            name: ResultNode[Identifier] = ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing name of branch",
                ),
            )
        else:
            name = ResultNode(
                location=self.get_location(name_node),
                inner=self.parse_identifier(name_node),
            )
        attribute_nodes = self.get_children_of_type(node, "attribute")
        return AbstractDataTypeBranch(
            location=self.get_location(node),
            name=name,
            attributes=[self.parse_attribute(_) for _ in attribute_nodes],
        )

    def parse_fact(self, node: ts.Node) -> ResultNode[Fact]:
        atom_node = self.get_child_of_type(node, "atom")
        if not atom_node:
            return ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Fact expected",
                ),
            )
        else:
            return self.parse_atom(atom_node, Fact)

    def parse_rule(self, node: ts.Node) -> Rule:
        heads: list[RuleHead | SubsumptionHead] = []
        for child in node.children_by_field_name("head"):
            if child.type == "rule_head":
                heads.append(self.parse_rule_head(child))
            elif child.type == "subsumption_head":
                heads.append(self.parse_subsumption_head(child))

        body_node = node.child_by_field_name("body")
        if not body_node:
            body: ResultNode[Disjunction] = ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing rule body",
                ),
            )
        else:
            body = ResultNode(
                location=self.get_location(body_node),
                inner=self.parse_disjunction(body_node),
            )

        return Rule(
            location=self.get_location(node),
            heads=heads,
            body=body,
        )

    def parse_disjunction(self, node: ts.Node) -> Disjunction:
        conjunction_nodes = self.get_children_of_type(node, "conjunction")
        conjunctions = [self.parse_conjunction(_) for _ in conjunction_nodes]
        return Disjunction(
            location=self.get_location(node),
            conjunctions=conjunctions,
        )

    def parse_conjunction(self, node: ts.Node) -> Conjunction:
        neg_node = self.get_child_of_type(node, "neg")
        if neg_node is None:
            neg = None
        elif len(self.get_text(neg_node)) % 2 == 0:
            neg = NegOp(
                location=self.get_location(neg_node),
                is_neg=False,
            )
        else:
            neg = NegOp(
                location=self.get_location(neg_node),
                is_neg=True,
            )
        clause_nodes = self.get_children_of_type(node, "conjunction_clause")
        clauses = list(
            filter(None, [self.parse_conjunction_clause(_) for _ in clause_nodes])
        )
        return Conjunction(
            location=self.get_location(node),
            neg=neg,
            clauses=clauses,
        )

    def parse_conjunction_clause(self, node: ts.Node) -> ResultNode[Clause] | None:
        atom_node = self.get_child_of_type(node, "atom")
        if atom_node is not None:
            return ResultNode(
                location=self.get_location(node),
                inner=self.parse_relation_reference_clause(node),
            )
        constraint_node = self.get_child_of_type(node, "constraint")
        if constraint_node is not None:
            return self.parse_constraint(constraint_node)
        disjunction_node = self.get_child_of_type(node, "disjunction")
        if disjunction_node is not None:
            return ResultNode(
                location=self.get_location(node),
                inner=self.parse_disjunction(disjunction_node),
            )
        raise AssertionError("unreachable")

    def parse_relation_reference_clause(self, node: ts.Node) -> RelationReferenceClause:
        atom_node = self.get_child_of_type(node, "atom")
        if not atom_node:
            relation_reference: ResultNode[RelationReference] = ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Relation clause expected",
                ),
            )
        else:
            relation_reference = self.parse_atom(atom_node, RelationReference)
        return RelationReferenceClause(
            location=self.get_location(node),
            relation_reference=relation_reference,
        )

    def parse_constraint(self, node: ts.Node) -> ResultNode[Clause]:
        binary_constraint_node = self.get_child_of_type(node, "binary_constraint")
        if binary_constraint_node:
            return ResultNode(
                location=self.get_location(node),
                inner=self.parse_binary_constraint(binary_constraint_node),
            )
        else:
            # TODO: add support for other constraint types.
            return ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Invalid or unsupported constraint type",
                ),
            )

    def parse_binary_constraint(self, node: ts.Node) -> BinaryConstraint:
        lhs_node = node.child_by_field_name("lhs")
        op_node = node.child_by_field_name("op")
        rhs_node = node.child_by_field_name("rhs")
        if lhs_node is None:
            lhs: ResultNode[Argument] = ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing left-hand-side of binary constraint",
                ),
            )
        else:
            left_argument = self.parse_argument(lhs_node)
            if left_argument is None:
                lhs = ResultNode(
                    location=self.get_location(node),
                    inner=ErrorNode(
                        location=self.get_location(node),
                        msg="Missing left-hand-side of binary constraint",
                    ),
                )
            else:
                lhs = ResultNode(
                    location=self.get_location(node),
                    inner=left_argument,
                )

        if op_node is None:
            op: ResultNode[BinaryConstraintOp] = ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing binary constraint operator",
                ),
            )
        else:
            op = ResultNode(
                location=self.get_location(node),
                inner=self.parse_binary_constraint_op(op_node),
            )

        if rhs_node is None:
            rhs: ResultNode[Argument] = ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing right-hand-side of binary constraint",
                ),
            )
        else:
            right_argument = self.parse_argument(rhs_node)
            if right_argument is None:
                rhs = ResultNode(
                    location=self.get_location(node),
                    inner=ErrorNode(
                        location=self.get_location(node),
                        msg="Missing right-hand-side of binary constraint",
                    ),
                )
            else:
                rhs = ResultNode(
                    location=self.get_location(node),
                    inner=right_argument,
                )
        return BinaryConstraint(
            location=self.get_location(node),
            lhs=lhs,
            op=op,
            rhs=rhs,
        )

    def parse_binary_constraint_op(self, node: ts.Node) -> BinaryConstraintOp:
        return BinaryConstraintOp(
            location=self.get_location(node),
            op=self.get_text(node),
        )

    def parse_rule_head(self, node: ts.Node) -> RuleHead:
        atom_nodes = self.get_children_of_type(node, "atom")
        relation_references = [
            self.parse_atom(_, RelationReference) for _ in atom_nodes
        ]
        return RuleHead(
            location=self.get_location(node),
            relation_references=relation_references,
        )

    def parse_subsumption_head(self, node: ts.Node) -> SubsumptionHead:
        first_node = node.child_by_field_name("first")
        second_node = node.child_by_field_name("second")
        if first_node is None or second_node is None:
            raise ParserError()
        return SubsumptionHead(
            location=self.get_location(node),
            first=self.parse_atom(first_node, RelationReference),
            second=self.parse_atom(second_node, RelationReference),
        )

    def parse_preprocessor_directive(self, node: ts.Node) -> ValidNode | None:
        preproc_include_node = self.get_child_of_type(node, "preproc_include")
        if preproc_include_node:
            return self.parse_preproc_include(preproc_include_node)
        return None

    def parse_preproc_include(self, node: ts.Node) -> PreprocInclude:
        path_node = self.get_child_of_type(node, "path_spec")
        if path_node is None:
            path: ResultNode[StringConstant] = ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing path spec",
                ),
            )
        else:
            path = ResultNode(
                location=self.get_location(node),
                inner=self.parse_string_literal(path_node),
            )
        return PreprocInclude(
            location=self.get_location(node),
            path=path,
        )

    AtomT = TypeVar("AtomT", bound=Atom)

    def parse_atom(self, node: ts.Node, atom_type: type[AtomT]) -> ResultNode[AtomT]:
        name_node = node.child_by_field_name("name")
        if not name_node:
            name: ResultNode[RelationReferenceName] = ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing atom name",
                ),
            )
        else:
            name = ResultNode(
                location=self.get_location(name_node),
                inner=self.parse_qualified_name(name_node, RelationReferenceName),
            )
        argument_nodes = self.get_children_of_type(node, "argument")
        arguments = list(
            filter(
                None,
                [self.parse_argument(_) for _ in argument_nodes],
            )
        )
        return ResultNode(
            location=self.get_location(node),
            inner=atom_type(
                location=self.get_location(node),
                name=name,
                arguments=arguments,
            ),
        )

    def parse_argument(self, node: ts.Node) -> Argument | None:
        constant_node = self.get_child_of_type(node, "constant")
        if constant_node:
            return self.parse_constant(constant_node)
        variable_node = self.get_child_of_type(node, "variable")
        if variable_node:
            return self.parse_variable(variable_node)
        record_init_node = self.get_child_of_type(node, "record_init")
        if record_init_node:
            return self.parse_record_init(record_init_node)
        branch_init_node = self.get_child_of_type(node, "branch_init")
        if branch_init_node:
            return self.parse_branch_init(branch_init_node)
        binary_operation_node = self.get_child_of_type(node, "binary_operation")
        if binary_operation_node:
            return self.parse_binary_operation(binary_operation_node)
        logger.debug("argument %s is not recognized", node)
        return None  # TODO

    def parse_constant(self, node: ts.Node) -> Constant | None:
        decimal_node = self.get_child_of_type(node, "decimal")
        if decimal_node is not None:
            return self.parse_decimal(decimal_node)
        string_literal_node = self.get_child_of_type(node, "string_literal")
        if string_literal_node is not None:
            return self.parse_string_literal(string_literal_node)
        logger.debug("constant %s is not recognized", node)
        return None

    def parse_variable(self, node: ts.Node) -> Variable:
        return Variable(
            location=self.get_location(node),
            name=self.get_text(node),
            ty=UnresolvedType(),
            # parent=None,
        )

    def parse_record_init(self, node: ts.Node) -> RecordInit:
        arg_nodes = self.get_children_of_type(node, "argument")
        arguments = list(filter(None, (self.parse_argument(_) for _ in arg_nodes)))
        return RecordInit(
            location=self.get_location(node),
            arguments=arguments,
            ty=UnresolvedType(),
        )

    def parse_branch_init(self, node: ts.Node) -> BranchInit:
        name_node = self.get_child_of_type(node, "qualified_name")
        if name_node is None:
            name: ResultNode[BranchInitName] = ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing branch name",
                ),
            )
        else:
            name = ResultNode(
                location=self.get_location(name_node),
                inner=self.parse_qualified_name(name_node, BranchInitName),
            )
        arg_nodes = self.get_children_of_type(node, "argument")
        arguments = list(filter(None, (self.parse_argument(_) for _ in arg_nodes)))
        return BranchInit(
            location=self.get_location(node),
            name=name,
            arguments=arguments,
            ty=UnresolvedType(),
            # parent=None,
        )

    def parse_binary_operation(self, node: ts.Node) -> BinaryOperation:
        lhs_node = self.get_child_of_type(node, "lhs")
        op_node = self.get_child_of_type(node, "op")
        rhs_node = self.get_child_of_type(node, "rhs")

        if lhs_node is None:
            lhs: ResultNode[Argument] = ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing left-hand-side of binary constraint",
                ),
            )
        else:
            left_argument = self.parse_argument(lhs_node)
            if left_argument is None:
                lhs = ResultNode(
                    location=self.get_location(node),
                    inner=ErrorNode(
                        location=self.get_location(node),
                        msg="Missing left-hand-side of binary constraint",
                    ),
                )
            else:
                lhs = ResultNode(
                    location=self.get_location(node),
                    inner=left_argument,
                )

        if op_node is None:
            op: ResultNode[BinaryOperator] = ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing binary operator",
                ),
            )
        else:
            op = ResultNode(
                location=self.get_location(node),
                inner=self.parse_binary_operator(op_node),
            )

        if rhs_node is None:
            rhs: ResultNode[Argument] = ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing right-hand-side of binary constraint",
                ),
            )
        else:
            right_argument = self.parse_argument(rhs_node)
            if right_argument is None:
                rhs = ResultNode(
                    location=self.get_location(node),
                    inner=ErrorNode(
                        location=self.get_location(node),
                        msg="Missing right-hand-side of binary constraint",
                    ),
                )
            else:
                rhs = ResultNode(
                    location=self.get_location(node),
                    inner=right_argument,
                )

        return BinaryOperation(
            location=self.get_location(node),
            lhs=lhs,
            op=op,
            rhs=rhs,
            ty=UnresolvedType(),
            # parent=None,
        )

    def parse_binary_operator(self, node: ts.Node) -> BinaryOperator:
        return BinaryOperator(
            location=self.get_location(node),
            op=self.get_text(node),
        )

    def parse_decimal(self, node: ts.Node) -> NumberConstant:
        return NumberConstant(
            location=self.get_location(node),
            val=int(self.get_text(node)),
            ty=UnresolvedType(),
            # parent=None,
        )

    def parse_string_literal(self, node: ts.Node) -> StringConstant:
        return StringConstant(
            location=self.get_location(node),
            val=self.get_text(node),
            ty=UnresolvedType(),
            # parent=None,
        )

    QualifiedNameT = TypeVar("QualifiedNameT", bound=QualifiedName)

    def parse_qualified_name(
        self,
        node: ts.Node,
        qualified_name_type: type[QualifiedNameT],
    ) -> QualifiedNameT:
        identifier_nodes = self.get_children_of_type(node, "identifier")
        return qualified_name_type(
            location=self.get_location(node),
            parts=[self.parse_identifier(_) for _ in identifier_nodes],
        )

    def parse_identifier(self, node: ts.Node) -> Identifier:
        return Identifier(
            location=self.get_location(node),
            val=self.get_text(node),
        )

    def parse_attribute(self, node: ts.Node) -> Attribute:
        name_node = node.child_by_field_name("name")
        if not name_node:
            name: ResultNode[Identifier] = ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing name",
                ),
            )
        else:
            name = ResultNode(
                location=self.get_location(name_node),
                inner=self.parse_identifier(name_node),
            )
        type_node = node.child_by_field_name("type")
        if not type_node:
            type_: ResultNode[TypeReference] = ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing type",
                ),
            )
        else:
            type_ = ResultNode(
                location=self.get_location(type_node),
                inner=self.parse_type_reference(type_node),
            )
        return Attribute(
            location=self.get_location(node),
            name=name,
            type_=type_,
        )

    def parse_type_reference(self, node: ts.Node) -> TypeReference:
        primitive_type_node = self.get_child_of_type(node, "primitive_type")
        if primitive_type_node is not None:
            return self.parse_primitive_type_node(primitive_type_node)
        qualified_name_node = self.get_child_of_type(node, "user_defined_type_name")
        if qualified_name_node is None:
            type_reference_name: ResultNode[TypeReferenceName] = ResultNode(
                location=self.get_location(node),
                inner=ErrorNode(
                    location=self.get_location(node),
                    msg="Missing type name",
                ),
            )
        else:
            type_reference_name = ResultNode(
                location=self.get_location(qualified_name_node),
                inner=self.parse_qualified_name(
                    qualified_name_node,
                    TypeReferenceName,
                ),
            )
        return TypeReference(
            location=self.get_location(node),
            name=type_reference_name,
        )

    def parse_primitive_type_node(self, node: ts.Node) -> TypeReference:
        return TypeReference(
            location=self.get_location(node),
            name=ResultNode(
                location=self.get_location(node),
                inner=TypeReferenceName(
                    location=self.get_location(node),
                    parts=[self.parse_identifier(node)],
                ),
            ),
        )

    def parse_block_comment(self, node: ts.Node) -> BlockComment:
        return BlockComment(
            location=self.get_location(node),
            content=self.get_text(node),
        )

    def parse_line_comment(self, node: ts.Node) -> LineComment:
        return LineComment(
            location=self.get_location(node),
            content=[self.get_text(node)],
        )

    def chunk_line_comments(
        self, line_comments: list[LineComment]
    ) -> list[LineComment]:
        # Chunking line comments on consecutive lines into one single block.
        if len(line_comments) == 0:
            return []
        line_comments.sort(key=lambda comment: comment.range_.start)
        chunked_comments = [line_comments[0]]
        for i in range(1, len(line_comments)):
            if (
                chunked_comments[-1].range_.end.line + 1
                == line_comments[i].range_.start.line
            ):
                chunked_comments[-1] = chunked_comments[-1].merge(line_comments[i])
            else:
                chunked_comments.append(line_comments[i])
        return chunked_comments


class ParserError(RuntimeError):
    pass
