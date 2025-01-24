from souffle_analyzer.ast import (
    BranchInitName,
    ErrorNode,
    IsDeclarationNode,
    Location,
    Node,
    RelationReferenceName,
    TypeReferenceName,
    Workspace,
)
from souffle_analyzer.visitor.visitor import Visitor


class CollectDeclarationReferencesVisitor(Visitor[None]):
    def __init__(self, workspace: Workspace, declaration: IsDeclarationNode) -> None:
        self.declaration = declaration
        self.references: list[Location] = []
        super().__init__(workspace)

    def process(self) -> list[Location]:
        for document in self.workspace.documents.values():
            document.accept(self)
        return self.references

    def visit_relation_reference_name(
        self, relation_reference_name: RelationReferenceName
    ) -> None:
        if relation_reference_name.declaration is None:
            return None
        relation_declaration = relation_reference_name.declaration
        relation_declaration_name = relation_declaration.name.inner
        if isinstance(relation_declaration_name, ErrorNode):
            return None
        if relation_reference_name.declaration == self.declaration:
            self.references.append(relation_reference_name.location)
        return None

    def visit_type_reference_name(self, type_reference_name: TypeReferenceName) -> None:
        if type_reference_name.declaration is None:
            return None
        type_declaration = type_reference_name.declaration
        type_declaration_name = type_declaration.name.inner
        if isinstance(type_declaration_name, ErrorNode):
            return None
        if type_reference_name.declaration == self.declaration:
            self.references.append(type_reference_name.location)
        return None

    def visit_branch_init_name(self, branch_init_name: BranchInitName) -> None:
        if branch_init_name.declaration is None:
            return None
        branch_declaration_name = branch_init_name.declaration.name.inner
        if isinstance(branch_declaration_name, ErrorNode):
            return None
        if branch_init_name.declaration == self.declaration:
            self.references.append(branch_init_name.location)
        return None

    def generic_visit(self, node: Node) -> None:
        for child in node.children_sorted_by_range:
            child.accept(self)
        return None
