from typing import List, Optional, Tuple

from souffle_analyzer.ast import File, Node, Position, Range, RelationDeclaration
from souffle_analyzer.visitor.visitor import Visitor

T = Optional[List[Tuple[Range, str]]]


class CodeActionVisitor(Visitor[T]):
    def __init__(self, file: File, position: Position) -> None:
        self.file = file
        self.position = position

    def process(self) -> T:
        return self.visit_file(self.file)

    def visit_relation_declaration(
        self, relation_declaration: RelationDeclaration
    ) -> T:
        if relation_declaration.doc_text is not None:
            return None
        doc_text_template = []
        doc_text_template.append("///")
        for attribute in relation_declaration.attributes:
            doc_text_template.append(f"/// @attribute {attribute.name.val}")
        doc_text_template.append("")
        pos = relation_declaration.range_.start
        return [(Range(pos, pos), "\n".join(doc_text_template))]

    def generic_visit(self, node: Node) -> T:
        for child in node.children_sorted_by_range:
            if child.covers_position(self.position):
                return child.accept(self)
        return None