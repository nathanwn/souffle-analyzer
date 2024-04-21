from abc import abstractmethod
from typing import Optional

from souffle_analyzer.ast import File, Node, Position
from souffle_analyzer.visitor.visitor import Visitor

T = Optional[Node]


class GetNodeUnderCursorVisitor(Visitor[T]):
    def __init__(
        self,
        file: File,
        position: Position,
    ) -> None:
        self.position = position
        super().__init__(file)

    def process(self) -> T:
        return self.file.accept(self)

    @abstractmethod
    def to_continue(self, node: Node) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def to_accept(self, node: Node) -> bool:
        raise NotImplementedError()

    def generic_visit(self, node: Node) -> T:
        for child in node.children_sorted_by_range:
            if child.covers_position(self.position):
                if self.to_continue(child):
                    return child.accept(self)
                if self.to_accept(child):
                    return child
                else:
                    return None
        return None
