from typing import Optional

from souffle_analyzer.ast import (
    BranchInitName,
    File,
    Node,
    Position,
    Range,
    RelationReferenceName,
    TypeReferenceName,
)
from souffle_analyzer.visitor.visitor import Visitor

T = Optional[Range]


class DefinitionVisitor(Visitor[T]):
    def __init__(self, file: File, position: Position) -> None:
        self.position = position
        super().__init__(file)

    def process(self) -> T:
        return self.file.accept(self)

    def visit_relation_reference_name(
        self, relation_reference_name: RelationReferenceName
    ) -> T:
        if relation_reference_name.declaration is not None:
            return relation_reference_name.declaration.name.range_
        return None

    def visit_type_reference_name(self, type_reference_name: TypeReferenceName) -> T:
        if type_reference_name.declaration is not None:
            return type_reference_name.declaration.name.range_
        return None

    def visit_branch_init_name(self, branch_init_name: BranchInitName) -> T:
        if branch_init_name.declaration is not None:
            return branch_init_name.declaration.name.range_
        return None

    def generic_visit(self, node: Node) -> T:
        for child in node.children_sorted_by_range:
            if child.covers_position(self.position):
                return child.accept(self)
        return None
