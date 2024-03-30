from typing import Optional

from souffle_analyzer.ast import (
    Directive,
    Fact,
    File,
    Node,
    Position,
    Range,
    RelationReference,
    TypeReference,
)
from souffle_analyzer.language import BUILTIN_TYPES
from souffle_analyzer.visitor.visitor import Visitor

T = Optional[Range]


class DefinitionVisitor(Visitor[T]):
    def __init__(self, file: File, position: Position) -> None:
        self.position = position
        super().__init__(file)

    def process(self) -> T:
        return self.visit_file(self.file)

    def visit_directive(self, directive: Directive) -> T:
        qualified_relation_name = next(
            (
                qualified_relation_name
                for qualified_relation_name in directive.relation_names
                if qualified_relation_name.range_.covers(self.position)
            ),
            None,
        )
        if qualified_relation_name is None:
            return None
        if len(qualified_relation_name.parts) != 1:
            return None
        relation_name = qualified_relation_name.parts[0].val
        for relation_declaration in self.file.relation_declarations:
            if relation_declaration.name.val == relation_name:
                return relation_declaration.name.range_
        return None

    def visit_relation_reference(self, relation_reference: RelationReference) -> T:
        if relation_reference.name.covers_position(self.position):
            for relation_declaration in self.file.relation_declarations:
                if (
                    relation_declaration.name.val
                    == relation_reference.name.parts[-1].val
                ):
                    return relation_declaration.name.range_
        return None

    def visit_type_reference(self, type_reference: TypeReference) -> T:
        if not type_reference.covers_position(self.position):
            return None
        if len(type_reference.names) == 1:
            type_name = type_reference.names[0]
            if type_name in [_.name for _ in BUILTIN_TYPES]:
                return None
            for type_declaration in self.file.type_declarations:
                if type_name == type_declaration.name.val:
                    return type_declaration.name.range_
        return None

    def visit_fact(self, fact: Fact) -> T:
        if len(fact.name.parts) != 1:
            # Note: only support simple relations now.
            return None

        relation_name = fact.name.parts[0].val
        matching_relation_declaration = self.get_relation_declaration_with_name(
            relation_name
        )
        if matching_relation_declaration is None:
            return None

        if fact.name.covers_position(self.position):
            return matching_relation_declaration.name.range_

        return None

    def generic_visit(self, node: Node) -> T:
        for child in node.children_sorted_by_range:
            if child.covers_position(self.position):
                return child.accept(self)
        return None
