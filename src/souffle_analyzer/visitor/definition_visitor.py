from typing import Optional

from souffle_analyzer.ast import (
    BranchInitName,
    Location,
    Node,
    Position,
    RelationReferenceName,
    TypeReferenceName,
    Workspace,
)
from souffle_analyzer.visitor.visitor import Visitor

DefinitionResult = Optional[Location]


class DefinitionVisitor(Visitor[DefinitionResult]):
    def __init__(self, workspace: Workspace, uri: str, position: Position) -> None:
        self.uri = uri
        self.position = position
        super().__init__(workspace)

    def process(self) -> DefinitionResult:
        return self.workspace.documents[self.uri].accept(self)

    def visit_relation_reference_name(
        self, relation_reference_name: RelationReferenceName
    ) -> DefinitionResult:
        if relation_reference_name.declaration is not None:
            return relation_reference_name.declaration.name.location
        return None

    def visit_type_reference_name(
        self, type_reference_name: TypeReferenceName
    ) -> DefinitionResult:
        if type_reference_name.declaration is not None:
            return type_reference_name.declaration.name.location
        return None

    def visit_branch_init_name(
        self, branch_init_name: BranchInitName
    ) -> DefinitionResult:
        if branch_init_name.declaration is not None:
            return branch_init_name.declaration.name.location
        return None

    def generic_visit(self, node: Node) -> DefinitionResult:
        for child in node.children_sorted_by_range:
            if child.covers_position(self.position):
                return child.accept(self)
        return None
