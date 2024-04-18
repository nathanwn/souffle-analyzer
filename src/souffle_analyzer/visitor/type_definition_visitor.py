from typing import Optional

from souffle_analyzer.ast import (
    Atom,
    Constant,
    Fact,
    File,
    Node,
    Position,
    Range,
    RelationReference,
    TypeDeclaration,
    Variable,
)
from souffle_analyzer.visitor.visitor import Visitor

T = Optional[Range]


class TypeDefinitionVisitor(Visitor[T]):
    def __init__(self, file: File, position: Position) -> None:
        self.position = position
        super().__init__(file)

    def process(self) -> T:
        return self.file.accept(self)

    def visit_fact(self, fact: Fact) -> T:
        return self.visit_atom(fact)

    def visit_relation_reference(self, relation_reference: RelationReference) -> T:
        return self.visit_atom(relation_reference)

    def visit_atom(self, atom: Atom) -> T:
        for argument in atom.arguments:
            # Only Constant and Variable are worth going to type definition.
            # For other types of argument, it is almost impossible to
            # figure out what a single cursor position is pointing at.
            if not (isinstance(argument, Constant) or isinstance(argument, Variable)):
                continue
            if argument.covers_position(self.position):
                if isinstance(argument.ty, TypeDeclaration):
                    return argument.ty.name.range_
        return None

    def generic_visit(self, node: Node) -> T:
        for child in node.children_sorted_by_range:
            if child.covers_position(self.position):
                return child.accept(self)
        return None
