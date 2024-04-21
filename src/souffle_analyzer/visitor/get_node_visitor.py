from typing import Callable, Optional

from souffle_analyzer.ast import File, Node, Position
from souffle_analyzer.visitor.visitor import Visitor

T = Optional[Node]


class GetNodeUnderCursorVisitor(Visitor[T]):
    def __init__(
        self,
        file: File,
        position: Position,
        to_accept: Callable[[Node], bool],
        to_continue: Callable[[Node], bool],
    ) -> None:
        self.position = position
        self.to_accept = to_accept
        self.to_continue = to_continue
        super().__init__(file)

    def process(self) -> T:
        return self.file.accept(self)

    def generic_visit(self, node: Node) -> T:
        for child in node.children_sorted_by_range:
            if child.covers_position(self.position):
                if self.to_continue(child):
                    return child.accept(self)
                if self.to_accept(child):
                    return child
        return None
