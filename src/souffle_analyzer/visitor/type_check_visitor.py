from typing import List

from lsprotocol.types import Diagnostic

from souffle_analyzer.ast import (
    Atom,
    ErrorNode,
    Fact,
    Node,
    RelationReference,
    UnresolvedType,
    Workspace,
)
from souffle_analyzer.visitor.visitor import Visitor


class TypeInferVisitor(Visitor[None]):
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self.diagnostics: List[Diagnostic] = []

    def process(self) -> None:
        for document in self.workspace.documents.values():
            document.accept(self)

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
            # This should be already been checked and reported.
            return
        if len(relation.attributes) != len(atom.arguments):
            # This should be already been checked and reported.
            return
        for attribute, argument in zip(relation.attributes, atom.arguments):
            if not isinstance(argument.ty, UnresolvedType):
                continue
            type_reference = attribute.type_.inner
            if isinstance(type_reference, ErrorNode):
                continue
            type_name = type_reference.name.inner
            if isinstance(type_name, ErrorNode):
                continue
            ty = self.workspace.get_type_declaration_with_name(type_name)
            if ty is not None:
                argument.ty = ty

    def generic_visit(self, node: Node) -> None:
        for child in node.children_sorted_by_range:
            child.accept(self)
