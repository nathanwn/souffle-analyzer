from typing import List, Optional

from souffle_analyzer.ast import (
    AbstractDataTypeBranch,
    BranchInitName,
    File,
    Node,
    Position,
    Range,
    RelationDeclaration,
    RelationReferenceName,
    TypeDeclaration,
    TypeReferenceName,
)
from souffle_analyzer.visitor.collect_references_visitor import CollectReferencesVisitor
from souffle_analyzer.visitor.visitor import Visitor

T = Optional[Node]


class FindReferencesVisitor(Visitor[T]):
    def __init__(self, file: File, position: Position) -> None:
        self.position = position
        super().__init__(file)

    def process(self) -> List[Range]:
        declaration = self.file.accept(self)
        if declaration is not None:
            return CollectReferencesVisitor(self.file, declaration).process()
        return []

    def visit_relation_declaration(
        self,
        relation_declaration: RelationDeclaration,
    ) -> T:
        if relation_declaration.name.covers_position(self.position):
            return relation_declaration
        return None

    def visit_relation_reference_name(
        self, relation_reference_name: RelationReferenceName
    ) -> T:
        if relation_reference_name.declaration is not None:
            return relation_reference_name.declaration
        return None

    def visit_type_declaration(self, type_declaration: TypeDeclaration) -> T:
        if type_declaration.name.covers_position(self.position):
            return type_declaration
        return None

    def visit_type_reference_name(self, type_reference_name: TypeReferenceName) -> T:
        if type_reference_name.declaration is not None:
            return type_reference_name.declaration
        return None

    def visit_abstract_data_type_branch(
        self, abstract_data_type_branch: AbstractDataTypeBranch
    ) -> T:
        if abstract_data_type_branch.name.covers_position(self.position):
            return abstract_data_type_branch
        return None

    def visit_branch_init_name(self, branch_init_name: BranchInitName) -> T:
        if branch_init_name.declaration is not None:
            return branch_init_name.declaration
        return None

    def generic_visit(self, node: Node) -> T:
        for child in node.children_sorted_by_range:
            if child.covers_position(self.position):
                return child.accept(self)
        return None
