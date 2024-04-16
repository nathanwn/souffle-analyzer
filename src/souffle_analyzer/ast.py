from __future__ import annotations

import re
from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from souffle_analyzer.visitor.visitor import Visitor


T = TypeVar("T")


@dataclass
class Position:
    line: int
    char: int

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Position):
            raise TypeError()
        return (self.line, self.char) < (other.line, other.char)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Position):
            raise TypeError()
        return (self.line, self.char) == (other.line, other.char)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Position):
            raise TypeError()
        return (self.line, self.char) < (other.line, other.char) or (
            self.line,
            self.char,
        ) == (other.line, other.char)

    def __repr__(self) -> str:
        return f"{self.line}:{self.char}"


@dataclass
class Range:
    start: Position
    end: Position

    def __repr__(self) -> str:
        return f"[{self.start}-{self.end}]"

    def covers(self, position: Position) -> bool:
        # Range-end character on a line is always exclusive.
        # This is the convention of both tree-sitter and vscode.
        return self.start <= position < self.end


@dataclass
class SyntaxIssue:
    range_: Range
    message: str | None


@dataclass
class Node:
    range_: Range
    syntax_issues: list[SyntaxIssue] = field(repr=False)

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


@dataclass
class Atom(Node):
    name: QualifiedName
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
class File(Node):
    code: bytes
    relation_declarations: list[RelationDeclaration]
    type_declarations: list[TypeDeclaration]
    facts: list[Fact]
    rules: list[Rule]
    directives: list[Directive]
    preprocessor_directives: list[Node]
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


@dataclass
class TypeDeclaration(Node):
    name: Identifier
    op: TypeDeclarationOp
    expression: TypeExpression

    @property
    def children(self) -> list[Node]:
        return [
            self.name,
            self.op,
            self.expression,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_type_declaration(self)


@dataclass
class TypeExpression(Node):
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


@dataclass
class AbstractDataTypeBranch(Node):
    name: Identifier
    attributes: list[Attribute]

    @property
    def children(self) -> list[Node]:
        return [
            self.name,
            *self.attributes,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_abstract_data_type_branch(self)


@dataclass
class TypeDeclarationOp(Node):
    op: TypeRelationOpKind

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_type_declaration_op(self)


class TypeRelationOpKind(Enum):
    SUBTYPE = "<:"
    EQ = "="

    def __repr__(self) -> str:
        return f"{self.name}({self.value})"


@dataclass
class Rule(Node):
    heads: list[RuleHead | SubsumptionHead]
    body: Disjunction

    @property
    def children(self) -> list[Node]:
        return [
            *self.heads,
            self.body,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_rule(self)


@dataclass
class RuleHead(Node):
    relation_references: list[RelationReference]

    @property
    def children(self) -> list[Node]:
        return [
            *self.relation_references,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_rule_head(self)


@dataclass
class SubsumptionHead(Node):
    first: RelationReference
    second: RelationReference

    @property
    def children(self) -> list[Node]:
        return [
            self.first,
            self.second,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_subsumption_head(self)


@dataclass
class NegOp(Node):
    is_neg: bool

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_neg_op(self)


@dataclass
class Clause(Node):
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
class Conjunction(Node):
    clauses: list[Clause]
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
    relation_reference: RelationReference

    @property
    def children(self) -> list[Node]:
        return [
            self.relation_reference,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_relation_reference_clause(self)


@dataclass
class BinaryConstraint(Clause):
    lhs: Argument | None
    op: BinaryConstraintOp
    rhs: Argument | None

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
class BinaryConstraintOp(Node):
    op: str

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_binary_constraint_op(self)


@dataclass
class RelationReference(Atom):
    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_relation_reference(self)


@dataclass
class RelationDeclaration(Node):
    name: Identifier
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

    def get_attribute_hover_text(self, attribute_idx: int) -> str:
        return f"{self.attributes[attribute_idx].get_hover_result()}"

    def get_signature(self) -> str:
        builder: list[str] = []
        builder.append(self.name.val)
        builder.append("(")
        for i, attribute in enumerate(self.attributes):
            if i != 0:
                builder.append(", ")
            builder.append(attribute.get_signature())
        builder.append(")")
        return "".join(builder)

    def get_attribute_signature(self, attribute_idx: int) -> str:
        return self.attributes[attribute_idx].get_signature()

    def parse_doc_comment(self, comment: Comment) -> None:
        current_attribute = None
        for line in comment.get_text():
            marker, _, remain = line.partition(" ")
            if marker == "@attribute":
                attribute_name, _, remain = remain.partition(" ")
                if remain is None:
                    continue
                for attribute in self.attributes:
                    if attribute_name == attribute.name.val:
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

    def get_hover_result(self) -> str:
        doc_lines = []
        doc_lines.append("```")
        doc_lines.append(self.get_signature())
        doc_lines.append("```")
        doc_lines.append("")
        if self.doc_text is not None:
            doc_lines.extend(self.doc_text)

        attribute_doc_lines = []

        for attribute_idx, attribute in enumerate(self.attributes):
            if attribute.doc_text:
                for i, line in enumerate(attribute.doc_text):
                    if i == 0:
                        attribute_doc_lines.append(f"`{attribute.name.val}`: {line}")
                    else:
                        attribute_doc_lines.append(line)
                if attribute_idx < len(self.attributes) - 1:
                    attribute_doc_lines.append("")

        if len(attribute_doc_lines) > 0:
            doc_lines.append("")
        doc_lines.extend(attribute_doc_lines)

        return "\n".join(doc_lines)


@dataclass
class Fact(Atom):
    name: QualifiedName
    arguments: list[Argument]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_fact(self)


@dataclass
class Directive(Node):
    relation_names: list[QualifiedName]

    @property
    def children(self) -> list[Node]:
        return [
            *self.relation_names,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_directive(self)


@dataclass
class Attribute(Node):
    name: Identifier
    type_: TypeReference
    doc_text: list[str] | None = None

    @property
    def children(self) -> list[Node]:
        return [
            self.name,
            self.type_,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_attribute(self)

    def get_signature(self) -> str:
        return f"{self.name.val}: {'.'.join(self.type_.names)}"

    def get_hover_result(self) -> str:
        doc_lines = []
        doc_lines.append("```")
        doc_lines.append(self.get_signature())
        doc_lines.append("```")
        if self.doc_text is not None:
            doc_lines.extend(self.doc_text)
        return "\n".join(doc_lines)


@dataclass
class TypeReference(TypeExpression):
    # A sequence of dot-separated names
    names: list[str]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_type_reference(self)


@dataclass
class Identifier(Node):
    val: str

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_identifier(self)


@dataclass
class QualifiedName(Node):
    parts: list[Identifier]

    @property
    def children(self) -> list[Node]:
        return [
            *self.parts,
        ]

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_qualified_name(self)


@dataclass
class Argument(Node):
    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_argument(self)


@dataclass
class Constant(Argument):
    pass


@dataclass
class Variable(Argument):
    name: str

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_variable(self)


@dataclass
class StringConstant(Constant):
    val: str


@dataclass
class NumberConstant(Constant):
    val: int | float


@dataclass
class PreprocInclude(Node):
    path: StringConstant

    @property
    def children(self) -> list[Node]:
        return [self.path]

    def accept(self, visitor: Visitor):
        return visitor.visit_preproc_include(self)


@dataclass
class Comment(Node):
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
            syntax_issues=[*self.syntax_issues, *other.syntax_issues],
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
