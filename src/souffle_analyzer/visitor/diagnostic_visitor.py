from typing import Optional

from souffle_analyzer.ast import (
    Atom,
    Fact,
    File,
    Node,
    Position,
    Range,
    RelationReference,
)
from souffle_analyzer.visitor.visitor import Visitor

T = Optional[Range]


class DiagnosticVisitor(Visitor[T]):
    def __init__(self, file: File, position: Position) -> None:
        self.position = position
        super().__init__(file)

    def process(self) -> T:
        return self.file.accept(self)

    def visit_fact(self, fact: Fact) -> None:
        return self.visit_atom(fact)

    def visit_relation_reference(self, relation_reference: RelationReference) -> None:
        return self.visit_atom(relation_reference)

    def visit_atom(self, atom: Atom) -> None:
        if len(atom.name.parts) > 1:
            # TODO
            return
        name = atom.name.parts[0].val
        relation = self.file.get_relation_declaration_with_name(name)
        if not relation:
            # TODO: handle this, but probably in a different step/another visitor?
            return
        if len(relation.attributes) != len(atom.arguments):
            # TODO: handle this, but probably in a different step/another visitor?
            return

    def generic_visit(self, node: Node) -> None:
        for child in node.children_sorted_by_range:
            child.accept(self)
