from typing import List

from lsprotocol.types import Diagnostic

from souffle_analyzer.ast import (
    Atom,
    Fact,
    File,
    Node,
    RelationReference,
    UnresolvedType,
)
from souffle_analyzer.visitor.visitor import Visitor


class TypeInferVisitor(Visitor[None]):
    def __init__(self, file: File) -> None:
        self.file = file
        self.diagnostics: List[Diagnostic] = []

    def process(self) -> None:
        return self.file.accept(self)

    def visit_fact(self, fact: Fact) -> None:
        return self.visit_atom(fact)

    def visit_relation_reference(self, relation_reference: RelationReference) -> None:
        return self.visit_atom(relation_reference)

    def visit_atom(self, atom: Atom) -> None:
        relation = self.file.get_relation_declaration_with_name(atom.name)
        if not relation:
            # This should be already been checked and reported.
            return
        if len(relation.attributes) != len(atom.arguments):
            # This should be already been checked and reported.
            return
        for attribute, argument in zip(relation.attributes, atom.arguments):
            if isinstance(argument.ty, UnresolvedType):
                ty = self.file.get_type_declaration_with_name(attribute.type_.name)
                if ty is not None:
                    argument.ty = ty

    def generic_visit(self, node: Node) -> None:
        for child in node.children_sorted_by_range:
            child.accept(self)
