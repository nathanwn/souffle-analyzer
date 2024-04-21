from typing import List

from souffle_analyzer.ast import (
    BranchInitName,
    File,
    Node,
    Range,
    RelationReferenceName,
    TypeReferenceName,
)
from souffle_analyzer.visitor.visitor import Visitor


class CollectReferencesVisitor(Visitor[None]):
    def __init__(self, file: File, declaration: Node) -> None:
        self.declaration = declaration
        self.references: List[Range] = []
        super().__init__(file)

    def process(self) -> List[Range]:
        self.file.accept(self)
        return self.references

    def visit_relation_reference_name(
        self, relation_reference_name: RelationReferenceName
    ) -> None:
        if relation_reference_name.declaration is not None:
            if relation_reference_name.declaration == self.declaration:
                self.references.append(relation_reference_name.range_)
        return None

    def visit_type_reference_name(self, type_reference_name: TypeReferenceName) -> None:
        if type_reference_name.declaration is not None:
            if type_reference_name.declaration == self.declaration:
                self.references.append(type_reference_name.range_)
        return None

    def visit_branch_init_name(self, branch_init_name: BranchInitName) -> None:
        if branch_init_name.declaration is not None:
            if branch_init_name.declaration == self.declaration:
                self.references.append(branch_init_name.range_)
        return None

    def generic_visit(self, node: Node) -> None:
        for child in node.children_sorted_by_range:
            child.accept(self)
        return None
