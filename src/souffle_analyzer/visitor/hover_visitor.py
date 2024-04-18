from typing import Optional, Tuple

from souffle_analyzer.ast import (
    BUILTIN_TYPES,
    Directive,
    Fact,
    File,
    Node,
    Position,
    Range,
    RelationReference,
    TypeReference,
)
from souffle_analyzer.logging import logger
from souffle_analyzer.visitor.visitor import Visitor

T = Optional[Tuple[str, Range]]


class HoverVisitor(Visitor[T]):
    def __init__(self, file: File, position: Position) -> None:
        self.position = position
        super().__init__(file)

    def process(self) -> T:
        logger.debug("start hover visitor")
        for line in self.file.code.decode().splitlines():
            logger.debug("line: %s", line)
        return self.visit_file(self.file)

    def visit_type_reference(self, type_reference: TypeReference) -> T:
        if len(type_reference.names) == 1:
            for builtin_type in BUILTIN_TYPES:
                if type_reference.names[0] == builtin_type.name:
                    return builtin_type.doc, type_reference.range_
        return None

    def visit_relation_reference(self, relation_reference: RelationReference) -> T:
        logger.debug(relation_reference)
        if len(relation_reference.name.parts) != 1:
            # TODO: support more complex relation references.
            return None
        matching_relation_declaration = None
        for relation_declaration in self.file.relation_declarations:
            if relation_declaration.name.val == relation_reference.name.parts[0].val:
                matching_relation_declaration = relation_declaration
        if matching_relation_declaration is None:
            return None

        if relation_reference.name.covers_position(self.position):
            return (
                matching_relation_declaration.get_hover_result(),
                relation_reference.name.range_,
            )

        arguments = relation_reference.arguments

        for i, argument in enumerate(arguments):
            if argument.covers_position(self.position):
                return (
                    matching_relation_declaration.get_attribute_hover_text(i),
                    argument.range_,
                )
        return None

    def visit_directive(self, directive: Directive) -> T:
        relation_name_covering_position = next(
            (
                qualified_relation_name
                for qualified_relation_name in directive.relation_names
                if qualified_relation_name.range_.covers(self.position)
            ),
            None,
        )
        if relation_name_covering_position is None:
            return None
        if len(relation_name_covering_position.parts) != 1:
            # TODO: support more complex relation references.
            return None
        relation_name = relation_name_covering_position.parts[0].val
        matching_relation_declaration = self.file.get_relation_declaration_with_name(
            relation_name
        )
        if matching_relation_declaration is None:
            return None
        return (
            matching_relation_declaration.get_hover_result(),
            relation_name_covering_position.range_,
        )

    def visit_fact(self, fact: Fact) -> T:
        if len(fact.name.parts) != 1:
            # Note: only support simple relations now.
            return None

        relation_name = fact.name.parts[0].val
        matching_relation_declaration = self.file.get_relation_declaration_with_name(
            relation_name
        )
        if matching_relation_declaration is None:
            return None

        if fact.name.covers_position(self.position):
            return (
                matching_relation_declaration.get_hover_result(),
                fact.name.range_,
            )

        for i, argument in enumerate(fact.arguments):
            if argument.covers_position(self.position):
                return (
                    matching_relation_declaration.get_attribute_hover_text(i),
                    argument.range_,
                )

        return None

    def generic_visit(self, node: Node) -> T:
        logger.debug("inside %s", node.__class__.__name__)
        for child in node.children_sorted_by_range:
            if child.covers_position(self.position):
                return child.accept(self)
        return None
