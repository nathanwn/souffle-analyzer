from abc import abstractmethod
from typing import Generic, Optional, TypeVar

from souffle_analyzer.ast import (
    AbstractDataTypeBranch,
    AbstractDataTypeExpression,
    Argument,
    Atom,
    Attribute,
    BinaryConstraint,
    BinaryConstraintOp,
    BlockComment,
    Conjunction,
    Directive,
    Disjunction,
    Fact,
    File,
    Identifier,
    LineComment,
    NegOp,
    Node,
    PreprocInclude,
    QualifiedName,
    RecordTypeExpression,
    RelationDeclaration,
    RelationReference,
    RelationReferenceClause,
    Rule,
    RuleHead,
    SubsumptionHead,
    TypeDeclaration,
    TypeDeclarationOp,
    TypeReference,
    UnionTypeExpression,
    Variable,
)

T = TypeVar("T")


class Visitor(Generic[T]):
    def __init__(self, file: File) -> None:
        self.file = file

    def visit_file(self, file: File) -> T:
        return self.generic_visit(file)

    def visit_type_declaration(self, type_declaration: TypeDeclaration) -> T:
        return self.generic_visit(type_declaration)

    def visit_type_declaration_op(self, type_relation_op: TypeDeclarationOp) -> T:
        return self.generic_visit(type_relation_op)

    def visit_union_type_expression(
        self, union_type_expression: UnionTypeExpression
    ) -> T:
        return self.generic_visit(union_type_expression)

    def visit_record_type_expression(
        self, record_type_expression: RecordTypeExpression
    ) -> T:
        return self.generic_visit(record_type_expression)

    def visit_abstract_data_type_expression(
        self, abstract_data_type_expression: AbstractDataTypeExpression
    ) -> T:
        return self.generic_visit(abstract_data_type_expression)

    def visit_abstract_data_type_branch(
        self, abstract_data_type_branch: AbstractDataTypeBranch
    ) -> T:
        return self.generic_visit(abstract_data_type_branch)

    def visit_rule(self, rule: Rule) -> T:
        return self.generic_visit(rule)

    def visit_rule_head(self, rule_head: RuleHead) -> T:
        return self.generic_visit(rule_head)

    def visit_subsumption_head(self, subsumption_head: SubsumptionHead) -> T:
        return self.generic_visit(subsumption_head)

    def visit_relation_reference(self, relation_reference: RelationReference) -> T:
        return self.generic_visit(relation_reference)

    def visit_relation_declaration(
        self, relation_declaration: RelationDeclaration
    ) -> T:
        return self.generic_visit(relation_declaration)

    def visit_fact(self, fact: Fact) -> T:
        return self.generic_visit(fact)

    def visit_disjunction(self, disjunction: Disjunction) -> T:
        return self.generic_visit(disjunction)

    def visit_conjunction(self, conjunction: Conjunction) -> T:
        return self.generic_visit(conjunction)

    def visit_attribute(self, attribute: Attribute) -> T:
        return self.generic_visit(attribute)

    def visit_variable(self, variable: Variable) -> T:
        return self.generic_visit(variable)

    def visit_type_reference(self, type_reference: TypeReference) -> T:
        return self.generic_visit(type_reference)

    def visit_identifier(self, identifier: Identifier) -> T:
        return self.generic_visit(identifier)

    def visit_qualified_name(self, qualified_name: QualifiedName) -> T:
        return self.generic_visit(qualified_name)

    def visit_argument(self, argument: Argument) -> T:
        return self.generic_visit(argument)

    def visit_atom(self, atom: Atom) -> T:
        return self.generic_visit(atom)

    def visit_directive(self, directive: Directive) -> T:
        return self.generic_visit(directive)

    def visit_relation_reference_clause(
        self,
        relation_reference_clause: RelationReferenceClause,
    ) -> T:
        return self.generic_visit(relation_reference_clause)

    def visit_binary_constraint(self, binary_constraint: BinaryConstraint) -> T:
        return self.generic_visit(binary_constraint)

    def visit_binary_constraint_op(self, binary_constraint_op: BinaryConstraintOp) -> T:
        return self.generic_visit(binary_constraint_op)

    def visit_neg_op(self, neg_op: NegOp) -> T:
        return self.generic_visit(neg_op)

    def visit_preproc_include(self, preproc_include: PreprocInclude) -> T:
        return self.generic_visit(preproc_include)

    def visit_line_comment(self, line_comment: LineComment) -> T:
        return self.generic_visit(line_comment)

    def visit_block_comment(self, block_comment: BlockComment) -> T:
        return self.generic_visit(block_comment)

    def get_relation_declaration_with_name(
        self, name: str
    ) -> Optional[RelationDeclaration]:
        for relation_declaration in self.file.relation_declarations:
            if relation_declaration.name.val == name:
                return relation_declaration
        return None

    @abstractmethod
    def generic_visit(self, node: Node) -> T:
        raise NotImplementedError()
