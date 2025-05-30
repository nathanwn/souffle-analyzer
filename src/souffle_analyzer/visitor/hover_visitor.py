from typing import Optional

from souffle_analyzer.ast import (
    BUILTIN_TYPES,
    BranchInitName,
    Node,
    Position,
    Range,
    RelationReferenceName,
    TypeReferenceName,
    Workspace,
)
from souffle_analyzer.visitor.visitor import Visitor

HoverResult = Optional[tuple[str, Range]]


class HoverVisitor(Visitor[HoverResult]):
    def __init__(self, workspace: Workspace, uri: str, position: Position) -> None:
        self.position = position
        self.uri = uri
        super().__init__(workspace)

    def process(self) -> HoverResult:
        return self.workspace.documents[self.uri].accept(self)

    def visit_type_reference_name(
        self, type_reference_name: TypeReferenceName
    ) -> HoverResult:
        if len(type_reference_name.parts) == 1:
            for builtin_type in BUILTIN_TYPES:
                if type_reference_name.parts[0].val == builtin_type.name:
                    return builtin_type.doc, type_reference_name.range_
        return None

    def visit_relation_reference_name(
        self, relation_reference_name: RelationReferenceName
    ) -> HoverResult:
        matching_relation_declaration = (
            self.workspace.get_relation_declaration_with_name(relation_reference_name)
        )
        if matching_relation_declaration is None:
            return None
        return (
            matching_relation_declaration.get_doc() or "",
            relation_reference_name.range_,
        )

    def visit_branch_init_name(self, branch_init_name: BranchInitName) -> HoverResult:
        matching_branch_init_declaration = self.workspace.get_adt_branch_with_name(
            branch_init_name
        )
        if matching_branch_init_declaration is None:
            return None
        return (
            matching_branch_init_declaration.get_doc() or "",
            branch_init_name.range_,
        )

    def generic_visit(self, node: Node) -> HoverResult:
        for child in node.children_sorted_by_range:
            if child.covers_position(self.position):
                return child.accept(self)
        return None
