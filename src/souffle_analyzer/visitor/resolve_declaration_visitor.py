from souffle_analyzer.ast import (
    BranchInitName,
    Node,
    RelationReferenceName,
    TypeReferenceName,
)
from souffle_analyzer.visitor.visitor import Visitor


class ResolveDeclarationVisitor(Visitor[None]):
    def transform(self) -> None:
        return self.file.accept(self)

    def visit_relation_reference_name(
        self, relation_reference_name: RelationReferenceName
    ) -> None:
        relation_reference_name.declaration = (
            self.file.get_relation_declaration_with_name(
                name=relation_reference_name,
            )
        )

    def visit_type_reference_name(self, type_reference_name: TypeReferenceName) -> None:
        type_reference_name.declaration = self.file.get_type_declaration_with_name(
            name=type_reference_name
        )

    def visit_branch_init_name(self, branch_init_name: BranchInitName) -> None:
        branch_init_name.declaration = self.file.get_adt_branch_with_name(
            branch_init_name
        )

    def generic_visit(self, node: Node) -> None:
        for child in node.children_sorted_by_range:
            child.accept(self)
        return None
