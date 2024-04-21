from typing import List, Optional

from souffle_analyzer.ast import (
    AbstractDataTypeBranch,
    BranchInitName,
    File,
    IsDeclarationNode,
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

T = Optional[IsDeclarationNode]


class FindReferencesVisitor(Visitor[T]):
    def __init__(self, file: File, position: Position) -> None:
        self.position = position
        super().__init__(file)

    def process(self) -> List[Range]:
        declaration = self.file.accept(self)
        references = []
        if declaration is not None:
            declaration_name_range = declaration.get_declaration_name_range()
            if declaration_name_range is not None:
                references.append(declaration_name_range)
            references.extend(
                CollectReferencesVisitor(
                    file=self.file, declaration=declaration
                ).process()
            )
        return references

    def visit_relation_declaration(
        self,
        relation_declaration: RelationDeclaration,
    ) -> T:
        if relation_declaration.name.covers_position(self.position):
            return relation_declaration
        return self.generic_visit(relation_declaration)

    def visit_relation_reference_name(
        self, relation_reference_name: RelationReferenceName
    ) -> T:
        if relation_reference_name.declaration is not None:
            return relation_reference_name.declaration
        return self.generic_visit(relation_reference_name)

    def visit_type_declaration(self, type_declaration: TypeDeclaration) -> T:
        if type_declaration.name.covers_position(self.position):
            return type_declaration
        return self.generic_visit(type_declaration)

    def visit_type_reference_name(self, type_reference_name: TypeReferenceName) -> T:
        if type_reference_name.declaration is not None:
            return type_reference_name.declaration
        return self.generic_visit(type_reference_name)

    def visit_abstract_data_type_branch(
        self, abstract_data_type_branch: AbstractDataTypeBranch
    ) -> T:
        if abstract_data_type_branch.name.covers_position(self.position):
            return abstract_data_type_branch
        return self.generic_visit(abstract_data_type_branch)

    def visit_branch_init_name(self, branch_init_name: BranchInitName) -> T:
        if branch_init_name.declaration is not None:
            return branch_init_name.declaration
        return self.generic_visit(branch_init_name)

    def generic_visit(self, node: Node) -> T:
        for child in node.children_sorted_by_range:
            if child.covers_position(self.position):
                return child.accept(self)
        return None
