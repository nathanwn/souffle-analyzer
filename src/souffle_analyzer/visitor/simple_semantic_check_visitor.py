from lsprotocol.types import Diagnostic

from souffle_analyzer.ast import (
    Atom,
    ErrorNode,
    Fact,
    Node,
    RelationReference,
    Workspace,
)
from souffle_analyzer.visitor.visitor import Visitor


class SimpleSemanticCheckVisitor(Visitor[None]):
    def __init__(self, workspace: Workspace, uri: str) -> None:
        self.uri = uri
        self.diagnostics: list[Diagnostic] = []
        super().__init__(workspace)

    def process(self) -> list[Diagnostic]:
        self.workspace.documents[self.uri].accept(self)
        return self.diagnostics

    def visit_fact(self, fact: Fact) -> None:
        return self.visit_atom(fact)

    def visit_relation_reference(self, relation_reference: RelationReference) -> None:
        return self.visit_atom(relation_reference)

    def visit_atom(self, atom: Atom) -> None:
        relation_name = atom.name.inner
        if isinstance(relation_name, ErrorNode):
            return
        relation = self.workspace.get_relation_declaration_with_name(relation_name)
        if not relation:
            return
        if len(relation.attributes) != len(atom.arguments):
            self.diagnostics.append(
                Diagnostic(
                    range=atom.range_.to_lsp_type(),
                    message=(
                        "Number of arguments: "
                        f"have {len(atom.arguments)}, "
                        f"want {len(relation.attributes)}."
                    ),
                )
            )
            return

    def generic_visit(self, node: Node) -> None:
        for child in node.children_sorted_by_range:
            child.accept(self)
