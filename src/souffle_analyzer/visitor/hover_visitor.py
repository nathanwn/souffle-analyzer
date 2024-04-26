from typing import Optional, Tuple

from souffle_analyzer.ast import (
    BUILTIN_TYPES,
    BranchInitName,
    File,
    Node,
    Position,
    Range,
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
            matching_relation_declaration.get_doc() or "",
            relation_reference_name.range_,
        )

    def visit_branch_init_name(self, branch_init_name: BranchInitName) -> T:
        matching_branch_init_declaration = self.file.get_adt_branch_with_name(
            branch_init_name
        )
        if matching_branch_init_declaration is None:
            return None
        return (
            matching_branch_init_declaration.get_doc() or "",
            branch_init_name.range_,
        )

    def generic_visit(self, node: Node) -> T:
        for child in node.children_sorted_by_range:
            if child.covers_position(self.position):
                return child.accept(self)
        return None
