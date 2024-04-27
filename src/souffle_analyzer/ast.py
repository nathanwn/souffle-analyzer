from __future__ import annotations

import os
import re
from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Generic, Protocol, TypeVar

import lsprotocol.types as lsptypes

if TYPE_CHECKING:
    from souffle_analyzer.visitor.visitor import Visitor


T = TypeVar("T")


@dataclass
class SouffleType:
    pass


@dataclass
class UnresolvedType(SouffleType):
    pass


@dataclass
class ErroneousType(SouffleType):
    pass


@dataclass
class BuiltinType(SouffleType):
    name: str
    doc: str


class BuiltinTypes:
    SYMBOL = BuiltinType(
        name="symbol",
        doc="Type `symbol`. Each value is a string.",
    )
    NUMBER = BuiltinType(
        name="number",
        doc="Type `number`. Each value is a signed integer.",
    )
    UNSIGNED = BuiltinType(
        name="unsigned",
        doc="Type `unsigned`. Each value is a non-negative integer.",
    )
    FLOAT = BuiltinType(
        name="float",
        doc="Type `float`. Each value is a floating-point number.",
    )


BUILTIN_TYPES = [
    BuiltinTypes.SYMBOL,
    BuiltinTypes.NUMBER,
    BuiltinTypes.UNSIGNED,
    BuiltinTypes.FLOAT,
]


@dataclass
class Position:
    line: int
    character: int

    @classmethod
    def from_lsp_type(cls, position: lsptypes.Position) -> Position:
        return Position(
            line=position.line,
            character=position.character,
        )

    def to_lsp_type(self) -> lsptypes.Position:
        return lsptypes.Position(line=self.line, character=self.character)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Position):
            raise TypeError()
        return (self.line, self.character) < (other.line, other.character)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Position):
            raise TypeError()
        return (self.line, self.character) == (other.line, other.character)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Position):
            raise TypeError()
        return (self.line, self.character) < (other.line, other.character) or (
            self.line,
            self.character,
        ) == (other.line, other.character)

    def __repr__(self) -> str:
        return f"{self.line}:{self.character}"


@dataclass
class Range:
    start: Position
    end: Position

    @classmethod
    def from_single_position(cls, position: Position) -> Range:
        return Range(
            start=position,
            end=position,
        )

    @classmethod
    def from_lsp_type(cls, range_: lsptypes.Range) -> Range:
        return Range(
            start=Position.from_lsp_type(range_.start),
            end=Position.from_lsp_type(range_.end),
        )

    def to_lsp_type(self) -> lsptypes.Range:
        return lsptypes.Range(
            start=self.start.to_lsp_type(), end=self.end.to_lsp_type()
        )

    def __repr__(self) -> str:
        return f"[{self.start}-{self.end}]"

    def is_single_position(self) -> bool:
        return self.start == self.end

    def covers(self, position: Position) -> bool:
        # Range-end character on a line is always exclusive.
        # This is the convention of both tree-sitter and vscode.
        return self.start <= position < self.end


@dataclass
class Location:
    uri: str
    range_: Range

    @classmethod
    def from_lsp_type(cls, loc: lsptypes.Location) -> Location:
        return cls(uri=loc.uri, range_=Range.from_lsp_type(loc.range))

    def to_lsp_type(self) -> lsptypes.Location:
        return lsptypes.Location(uri=self.uri, range=self.range_.to_lsp_type())


@dataclass
class SyntaxIssue:
    range_: Range
    message: str | None


@dataclass
class Node:
    range_: Range

    @property
    def children_sorted_by_range(self) -> list[Node]:
        return sorted(self.children, key=lambda child: child.range_.start)

    def covers_position(self, position: Position) -> bool:
        return self.range_.covers(position)

    @property
    def children(self) -> list[Node]:
        return []

    @abstractmethod
    def accept(self, visitor: Visitor):
        raise NotImplementedError()


class IsDeclarationNode(Protocol):
    def get_declaration_name_range(self) -> Range | None: ...


@dataclass
class ErrorNode(Node):
    msg: str

    @property
    def children(self) -> list[Node]:
        return []

    def accept(self, visitor: Visitor):
        return visitor.visit_error_node(self)


@dataclass
class ValidNode(Node):
    pass


ValidNodeT = TypeVar("ValidNodeT", bound=ValidNode, covariant=True)


@dataclass
class ResultNode(Generic[ValidNodeT], Node):
    inner: ValidNodeT | ErrorNode

    @property
    def children(self) -> list[Node]:
        return [self.inner]

    def accept(self, visitor: Visitor):
        return visitor.visit_result_node(self)


@dataclass
class Atom(ValidNode):
    name: ResultNode[RelationReferenceName]
    arguments: list[Argument]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_atom(self)

    @property
    def children(self) -> list[Node]:
        return [
            self.name,
            *self.arguments,
        ]


@dataclass
class File(ValidNode):
    code: str
    relation_declarations: list[RelationDeclaration]
    type_declarations: list[TypeDeclaration]
    facts: list[ResultNode[Fact]]
    rules: list[Rule]
    directives: list[Directive]
    preprocessor_directives: list[ValidNode]
    comments: list[Comment]

    @property
    def children(self) -> list[Node]:
        return [
            *self.relation_declarations,
            *self.type_declarations,
            *self.facts,
            *self.rules,
            *self.directives,
            *self.preprocessor_directives,
            *self.comments,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_file(self)

    def get_relation_declaration_with_name(
        self,
        name: RelationReferenceName,
    ) -> RelationDeclaration | None:
        if len(name.parts) != 1:
            # TODO: support more complex names
            return None
        for relation_declaration in self.relation_declarations:
            relation_declaration_name = relation_declaration.name.inner
            if isinstance(relation_declaration_name, ErrorNode):
                continue
            if relation_declaration_name.val == name.parts[0].val:
                return relation_declaration
        return None

    def get_type_declaration_with_name(
        self,
        name: TypeReferenceName,
    ) -> TypeDeclaration | None:
        if len(name.parts) != 1:
            # TODO: support more complex names
            return None
        for type_declaration in self.type_declarations:
            type_declaration_name = type_declaration.name.inner
            if not isinstance(type_declaration_name, ValidNode):
                continue
            if type_declaration_name.val == name.parts[0].val:
                return type_declaration
        return None

    def get_adt_branch_with_name(
        self,
        name: BranchInitName,
    ) -> AbstractDataTypeBranch | None:
        if len(name.parts) != 1:
            # TODO: support more complex names
            return None
        for type_declaration in self.type_declarations:
            type_expression_node = type_declaration.expression
            if not isinstance(type_expression_node.inner, AbstractDataTypeExpression):
                continue
            type_expression = type_expression_node.inner
            adt_branch = type_expression.get_branch_with_name(name.parts[0].val)
            if adt_branch is not None:
                return adt_branch
        return None


@dataclass
class TypeDeclaration(SouffleType, ValidNode):
    name: ResultNode[Identifier]
    op: ResultNode[TypeDeclarationOp]
    expression: ResultNode[TypeExpression]

    @property
    def children(self) -> list[Node]:
        return [
            self.name,
            self.op,
            self.expression,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_type_declaration(self)

    def get_declaration_name_range(self) -> Range | None:
        if isinstance(self.name.inner, ErrorNode):
            return None
        return self.name.inner.range_


@dataclass
class SubsetType(TypeDeclaration):
    pass


@dataclass
class AliasType(TypeDeclaration):
    pass


@dataclass
class TypeExpression(ValidNode):
    pass


@dataclass
class UnionTypeExpression(TypeExpression):
    types: list[TypeReference]

    @property
    def children(self) -> list[Node]:
        return [
            *self.types,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_union_type_expression(self)


@dataclass
class RecordTypeExpression(TypeExpression):
    attributes: list[Attribute]

    @property
    def children(self) -> list[Node]:
        return [
            *self.attributes,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_record_type_expression(self)


@dataclass
class AbstractDataTypeExpression(TypeExpression):
    branches: list[AbstractDataTypeBranch]

    @property
    def children(self) -> list[Node]:
        return [
            *self.branches,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_abstract_data_type_expression(self)

    def get_branch_with_name(self, name: str) -> AbstractDataTypeBranch | None:
        for branch in self.branches:
            branch_name = branch.name.inner
            if isinstance(branch_name, ErrorNode):
                continue
            if branch_name.val == name:
                return branch
        return None


@dataclass
class AbstractDataTypeBranch(ValidNode):
    name: ResultNode[Identifier]
    attributes: list[Attribute]

    @property
    def children(self) -> list[Node]:
        return [
            self.name,
            *self.attributes,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_abstract_data_type_branch(self)

    def get_declaration_name_range(self) -> Range | None:
        if isinstance(self.name.inner, ErrorNode):
            return None
        return self.name.inner.range_

    def get_signature(self) -> str | None:
        builder: list[str] = []
        if isinstance(self.name.inner, ErrorNode):
            return None
        name = self.name.inner
        attributes: list[Attribute] = []
        for attribute in self.attributes:
            attributes.append(attribute)

        builder.append(name.val)
        builder.append(" {")
        for i, attribute in enumerate(attributes):
            if i != 0:
                builder.append(", ")
            signature = attribute.get_signature()
            if signature is None:
                return None
            builder.append(signature)
        builder.append("}")
        return "".join(builder)

    def get_doc(self) -> str | None:
        signature = self.get_signature()
        if signature is None:
            return None
        doc_lines = ["```", signature, "```"]
        return os.linesep.join(doc_lines)


@dataclass
class TypeDeclarationOp(ValidNode):
    op: TypeRelationOpKind

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_type_declaration_op(self)


class TypeRelationOpKind(Enum):
    SUBTYPE = "<:"
    EQUIVALENT_TYPE = "="

    def __repr__(self) -> str:
        return f"{self.name}({self.value})"


@dataclass
class Rule(ValidNode):
    heads: list[RuleHead | SubsumptionHead]
    body: ResultNode[Disjunction]

    @property
    def children(self) -> list[Node]:
        return [
            *self.heads,
            self.body,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_rule(self)


@dataclass
class RuleHead(ValidNode):
    relation_references: list[ResultNode[RelationReference]]

    @property
    def children(self) -> list[Node]:
        return [
            *self.relation_references,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_rule_head(self)


@dataclass
class SubsumptionHead(ValidNode):
    first: ResultNode[RelationReference]
    second: ResultNode[RelationReference]

    @property
    def children(self) -> list[Node]:
        return [
            self.first,
            self.second,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_subsumption_head(self)


@dataclass
class NegOp(ValidNode):
    is_neg: bool

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_neg_op(self)


@dataclass
class Clause(ValidNode):
    pass


@dataclass
class Disjunction(Clause):
    conjunctions: list[Conjunction]

    @property
    def children(self) -> list[Node]:
        return [
            *self.conjunctions,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_disjunction(self)


@dataclass
class Conjunction(ValidNode):
    clauses: list[ResultNode[Clause]]
    neg: NegOp | None

    @property
    def children(self) -> list[Node]:
        children: list[Node] = []
        if self.neg is not None:
            children.append(self.neg)
        children.extend(self.clauses)
        return children

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_conjunction(self)


@dataclass
class RelationReferenceClause(Clause):
    relation_reference: ResultNode[RelationReference]

    @property
    def children(self) -> list[Node]:
        return [
            self.relation_reference,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_relation_reference_clause(self)


@dataclass
class BinaryConstraint(Clause):
    lhs: ResultNode[Argument]
    op: ResultNode[BinaryConstraintOp]
    rhs: ResultNode[Argument]

    @property
    def children(self) -> list[Node]:
        children: list[Node] = []
        if self.lhs is not None:
            children.append(self.lhs)
        children.append(self.op)
        if self.rhs is not None:
            children.append(self.rhs)
        return children

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_binary_constraint(self)


@dataclass
class BinaryConstraintOp(ValidNode):
    op: str

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_binary_constraint_op(self)


@dataclass
class RelationReference(Atom):
    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_relation_reference(self)


@dataclass
class RelationDeclaration(ValidNode):
    name: ResultNode[Identifier]
    attributes: list[Attribute]
    doc_text: list[str] | None = None

    @property
    def children(self) -> list[Node]:
        return [
            self.name,
            *self.attributes,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_relation_declaration(self)

    def get_declaration_name_range(self) -> Range | None:
        if isinstance(self.name.inner, ErrorNode):
            return None
        return self.name.inner.range_

    def get_signature(self) -> str | None:
        builder: list[str] = []
        if isinstance(self.name.inner, ErrorNode):
            return None
        name = self.name.inner
        attributes: list[Attribute] = []
        for attribute in self.attributes:
            attributes.append(attribute)

        builder.append(name.val)
        builder.append("(")
        for i, attribute in enumerate(attributes):
            if i != 0:
                builder.append(", ")
            signature = attribute.get_signature()
            if signature is None:
                return None
            builder.append(signature)
        builder.append(")")
        return "".join(builder)

    def get_attribute_hover_text(self, attribute_idx: int) -> str | None:
        attribute = self.attributes[attribute_idx]
        return attribute.get_hover_result()

    def get_attribute_signature(self, attribute_idx: int) -> str | None:
        attribute = self.attributes[attribute_idx]
        return attribute.get_signature()

    def parse_doc_comment(self, comment: Comment) -> None:
        if isinstance(self.name.inner, ErrorNode):
            return None

        attributes = {}
        for attribute in self.attributes:
            if isinstance(attribute.name.inner, ErrorNode):
                return None
            attributes[attribute.name.inner.val] = attribute

        current_attribute = None
        for line in comment.get_text():
            marker, _, remain = line.partition(" ")
            if marker == "@attribute":
                doc_attribute_name, _, remain = remain.partition(" ")
                if remain is None:
                    continue
                for attribute_name, attribute in attributes.items():
                    if doc_attribute_name == attribute_name:
                        current_attribute = attribute
                        attribute.doc_text = [remain]
                        break
            else:
                if current_attribute is None:
                    if self.doc_text is None:
                        self.doc_text = []
                    self.doc_text.append(line)
                else:
                    if current_attribute.doc_text is None:
                        raise AssertionError("unreachable")
                    current_attribute.doc_text.append(line)

    def get_doc(self) -> str | None:
        if isinstance(self.name.inner, ErrorNode):
            return None

        doc_lines = []
        signature = self.get_signature()
        if signature is None:
            return None
        doc_lines.append("```")
        doc_lines.append(signature)
        doc_lines.append("```")

        if self.doc_text is not None:
            doc_lines.append("")
            doc_lines.extend(self.doc_text)

        attribute_doc_lines = []

        for attribute in self.attributes:
            if isinstance(attribute.name.inner, ErrorNode):
                return None
            attribute_name = attribute.name.inner.val
            if attribute.doc_text:
                attribute_doc_lines.append(
                    f"* `{attribute_name}`: {' '.join(attribute.doc_text)}"
                )

        if len(attribute_doc_lines) > 0:
            doc_lines.append("")
        doc_lines.extend(attribute_doc_lines)

        return os.linesep.join(doc_lines)


@dataclass
class Fact(Atom):
    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_fact(self)


@dataclass
class DirectiveQualifier(ValidNode):
    keyword: str

    def accept(self, visitor: Visitor):
        return visitor.visit_directive_qualifier(self)


@dataclass
class Directive(ValidNode):
    qualifier: DirectiveQualifier
    relation_names: list[RelationReferenceName]

    @property
    def children(self) -> list[Node]:
        return [
            self.qualifier,
            *self.relation_names,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_directive(self)


@dataclass
class Attribute(ValidNode):
    name: ResultNode[Identifier]
    type_: ResultNode[TypeReference]
    doc_text: list[str] | None = None

    @property
    def children(self) -> list[Node]:
        return [
            self.name,
            self.type_,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_attribute(self)

    def get_signature(self) -> str | None:
        name = self.name.inner
        if isinstance(name, ErrorNode):
            return None
        type_reference = self.type_.inner
        if isinstance(type_reference, ErrorNode):
            return None
        type_reference_name = type_reference.name.inner
        if isinstance(type_reference_name, ErrorNode):
            return None
        type_name_parts = type_reference_name.parts
        type_name = ".".join(map(lambda part: part.val, type_name_parts))
        return f"{name.val}: {type_name}"

    def get_hover_result(self) -> str | None:
        signature = self.get_signature()
        if signature is None:
            return None
        doc_lines = []
        doc_lines.append("```")
        doc_lines.append(signature)
        doc_lines.append("```")
        if self.doc_text is not None:
            doc_lines.extend(self.doc_text)
        return os.linesep.join(doc_lines)


@dataclass
class QualifiedName(ValidNode):
    parts: list[Identifier]

    @property
    def children(self) -> list[Node]:
        return [
            *self.parts,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_qualified_name(self)


@dataclass
class TypeReference(TypeExpression):
    # A sequence of dot-separated names
    name: ResultNode[TypeReferenceName]

    @property
    def children(self) -> list[Node]:
        return [
            self.name,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_type_reference(self)


@dataclass
class RelationReferenceName(QualifiedName):
    declaration: RelationDeclaration | None = field(default=None)

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_relation_reference_name(self)


@dataclass
class TypeReferenceName(QualifiedName):
    declaration: TypeDeclaration | None = field(default=None)

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_type_reference_name(self)


@dataclass
class BranchInitName(QualifiedName):
    declaration: AbstractDataTypeBranch | None = field(default=None)

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_branch_init_name(self)


@dataclass
class Identifier(ValidNode):
    val: str

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_identifier(self)


@dataclass
class Argument(ValidNode):
    ty: SouffleType
    # parent: ValidNode | None


@dataclass
class Constant(Argument):
    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_constant(self)


@dataclass
class Variable(Argument):
    name: str

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_variable(self)


@dataclass
class RecordInit(Argument):
    arguments: list[Argument]
    definition: TypeDeclaration | None = field(default=None)

    @property
    def children(self) -> list[Node]:
        return [
            *self.arguments,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_record_init(self)


@dataclass
class BranchInit(Argument):
    name: ResultNode[BranchInitName]
    arguments: list[Argument]

    @property
    def children(self) -> list[Node]:
        return [
            self.name,
            *self.arguments,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_branch_init(self)


@dataclass
class BinaryOperation(Argument):
    lhs: ResultNode[Argument]
    op: ResultNode[BinaryOperator]
    rhs: ResultNode[Argument]

    @property
    def children(self) -> list[Node]:
        return [
            self.lhs,
            self.op,
            self.rhs,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_binary_operation(self)


@dataclass
class BinaryOperator(ValidNode):
    op: str

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_binary_operator(self)


@dataclass
class StringConstant(Constant):
    val: str


@dataclass
class NumberConstant(Constant):
    val: int | float


@dataclass
class PreprocInclude(ValidNode):
    path: ResultNode[StringConstant]

    @property
    def children(self) -> list[Node]:
        return [self.path]

    def accept(self, visitor: Visitor):
        return visitor.visit_preproc_include(self)


@dataclass
class Comment(ValidNode):
    @abstractmethod
    def get_text(self) -> list[str]:
        raise NotImplementedError()


@dataclass
class BlockComment(Comment):
    content: str

    def accept(self, visitor: Visitor) -> None:
        return visitor.visit_block_comment(self)

    def get_text(self) -> list[str]:
        last_line_pattern = re.compile(r"^[\s]*[*]+\/.*$")
        text_pattern = re.compile(r"^[\s]*[\/]?[*]*[\s]*(.*?)(\s*\*\/)?$")
        text_lines = []
        for line in self.content.splitlines():
            if last_line_pattern.match(line):
                break
            res = text_pattern.match(line)
            if res is None:
                continue
            text_line = res.group(1)
            text_lines.append(text_line)

        start = 0
        for i in range(len(text_lines)):
            if len(text_lines[i]) != 0:
                break
            start = i + 1
        end = len(text_lines)
        for i in range(len(text_lines) - 1, -1, -1):
            if len(text_lines[i]) != 0:
                break
            end = i
        return text_lines[start:end]


@dataclass
class LineComment(Comment):
    content: list[str]

    def accept(self, visitor: Visitor):
        return visitor.visit_line_comment(self)

    def merge(self, other: LineComment) -> LineComment:
        return LineComment(
            range_=Range(self.range_.start, other.range_.end),
            # syntax_issues=[*self.syntax_issues, *other.syntax_issues],
            content=[*self.content, *other.content],
        )

    def get_text(self) -> list[str]:
        text_pattern = re.compile(r"^[\s]*\/\/[\/]*[\s]*(.*)$")
        text_lines = []
        for line in self.content:
            res = text_pattern.match(line)
            if res is None:
                continue
            text_lines.append(res.group(1))

        start = 0
        for i in range(len(text_lines)):
            if len(text_lines[i]) != 0:
                break
            start = i + 1
        end = len(text_lines)
        for i in range(len(text_lines) - 1, -1, -1):
            if len(text_lines[i]) != 0:
                break
            end = i
        return text_lines[start:end]
