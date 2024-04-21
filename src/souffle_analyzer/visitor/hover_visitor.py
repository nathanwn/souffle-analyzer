from typing import Optional, Tuple

from souffle_analyzer.ast import (
    BUILTIN_TYPES,
    ErrorNode,
    Fact,
    File,
    Node,
    Position,
    Range,
    RelationReference,
    RelationReferenceName,
    TypeReferenceName,
)
from souffle_analyzer.visitor.visitor import Visitor

T = Optional[Tuple[str, Range]]


class HoverVisitor(Visitor[T]):
    def __init__(self, file: File, position: Position) -> None:
        self.position = position
        super().__init__(file)

    def process(self) -> T:
        return self.visit_file(self.file)

    def visit_type_reference_name(self, type_reference_name: TypeReferenceName) -> T:
        if len(type_reference_name.parts) == 1:
            for builtin_type in BUILTIN_TYPES:
                if type_reference_name.parts[0].val == builtin_type.name:
                    return builtin_type.doc, type_reference_name.range_
        return None

    def visit_relation_reference_name(
        self, relation_reference_name: RelationReferenceName
    ) -> T:
        matching_relation_declaration = self.file.get_relation_declaration_with_name(
            relation_reference_name
        )
        if matching_relation_declaration is None:
            return None
        return (
            matching_relation_declaration.get_hover_result() or "",
            relation_reference_name.range_,
        )

    def visit_relation_reference(self, relation_reference: RelationReference) -> T:
        if relation_reference.name.covers_position(self.position):
            return relation_reference.name.accept(self)
        arguments = relation_reference.arguments

        relation_reference_name = relation_reference.name.inner
        if isinstance(relation_reference_name, ErrorNode):
            return None

        declaration = relation_reference_name.declaration

        if declaration is None:
            return None

        for i, argument in enumerate(arguments):
            if argument.covers_position(self.position):
                return (
                    declaration.get_attribute_hover_text(i) or "",
                    argument.range_,
                )
        return None

    def visit_fact(self, fact: Fact) -> T:
        fact_name = fact.name.inner
        if isinstance(fact_name, ErrorNode):
            return None

        relation_declaration = self.file.get_relation_declaration_with_name(fact_name)
        if relation_declaration is None:
            return None

        if fact.name.covers_position(self.position):
            return fact.name.accept(self)

        for i, argument in enumerate(fact.arguments):
            if argument.covers_position(self.position):
                return (
                    relation_declaration.get_attribute_hover_text(i) or "",
                    argument.range_,
                )

        return None

    def generic_visit(self, node: Node) -> T:
        for child in node.children_sorted_by_range:
            if child.covers_position(self.position):
                return child.accept(self)
        return None
