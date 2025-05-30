from typing import Optional

from souffle_analyzer.ast import (
    Atom,
    Constant,
    Fact,
    Location,
    Node,
    Position,
    RelationReference,
    TypeDeclaration,
    Variable,
    Workspace,
)
from souffle_analyzer.visitor.visitor import Visitor

TypeDefinitionResult = Optional[Location]


class TypeDefinitionVisitor(Visitor[TypeDefinitionResult]):
    def __init__(self, workspace: Workspace, uri: str, position: Position) -> None:
        self.uri = uri
        self.position = position
        super().__init__(workspace)

    def process(self) -> TypeDefinitionResult:
        return self.workspace.documents[self.uri].accept(self)

    def visit_fact(self, fact: Fact) -> TypeDefinitionResult:
        return self.visit_atom(fact)

    def visit_relation_reference(
        self, relation_reference: RelationReference
    ) -> TypeDefinitionResult:
        return self.visit_atom(relation_reference)

    def visit_atom(self, atom: Atom) -> TypeDefinitionResult:
        for argument in atom.arguments:
            # Only Constant and Variable are worth going to type definition.
            # For other types of argument, it is almost impossible to
            # figure out what a single cursor position is pointing at.
            if not (isinstance(argument, Constant) or isinstance(argument, Variable)):
                continue
            if argument.covers_position(self.position):
                if isinstance(argument.ty, TypeDeclaration):
                    return argument.ty.name.location
        return None

    def generic_visit(self, node: Node) -> TypeDefinitionResult:
        for child in node.children_sorted_by_range:
            if child.covers_position(self.position):
                return child.accept(self)
        return None
