import os
from typing import Optional

from souffle_analyzer.ast import (
    ErrorNode,
    Node,
    Position,
    Range,
    RelationDeclaration,
    Workspace,
)
from souffle_analyzer.visitor.visitor import Visitor

T = Optional[list[tuple[Range, str]]]


class CodeActionVisitor(Visitor[T]):
    def __init__(self, workspace: Workspace, uri: str, position: Position) -> None:
        self.uri = uri
        self.position = position
        super().__init__(workspace)

    def process(self) -> T:
        return self.workspace.documents[self.uri].accept(self)

    def visit_relation_declaration(
        self, relation_declaration: RelationDeclaration
    ) -> T:
        if relation_declaration.doc_text is not None:
            return None
        doc_text_template = []
        doc_text_template.append("///")
        for attribute in relation_declaration.attributes:
            attribute_name = attribute.name.inner
            if isinstance(attribute_name, ErrorNode):
                return None
            doc_text_template.append(f"/// @attribute {attribute_name.val}")
        doc_text_template.append("")
        pos = relation_declaration.range_.start
        return [(Range(pos, pos), os.linesep.join(doc_text_template))]

    def generic_visit(self, node: Node) -> T:
        for child in node.children_sorted_by_range:
            if child.covers_position(self.position):
                return child.accept(self)
        return None
