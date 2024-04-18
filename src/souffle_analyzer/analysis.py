from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import lsprotocol.types as lsptypes

from souffle_analyzer.ast import Position, Range
from souffle_analyzer.logging import logger
from souffle_analyzer.lsp import to_lsp_range
from souffle_analyzer.parser import Parser
from souffle_analyzer.visitor.code_action_visitor import CodeActionVisitor
from souffle_analyzer.visitor.definition_visitor import DefinitionVisitor
from souffle_analyzer.visitor.hover_visitor import HoverVisitor
from souffle_analyzer.visitor.type_definition_visitor import TypeDefinitionVisitor
from souffle_analyzer.visitor.type_infer_visitor import TypeInferVisitor


@dataclass
class AnalysisContext:
    documents: Dict[str, str] = field(default_factory=dict)

    def open_document(self, uri: str, text: str) -> None:
        self.documents[uri] = text
        logger.debug("open document")
        for line in text.splitlines():
            logger.debug(line)

    def update_document(
        self, uri: str, changes: List[lsptypes.TextDocumentContentChangeEvent]
    ) -> None:
        for change in changes:
            # Only handle whole-document change
            logger.info("change event: %s", change)
            if isinstance(change, lsptypes.TextDocumentContentChangeEvent_Type1):
                pass
            if isinstance(change, lsptypes.TextDocumentContentChangeEvent_Type2):
                self.documents[uri] = change.text
                logger.debug("update document")
                for line in change.text.splitlines():
                    logger.debug(line)

    def hover(
        self, uri: str, position: lsptypes.Position
    ) -> Optional[Tuple[str, Range]]:
        parser = Parser()
        file = parser.parse(self.documents[uri].encode())
        hover_visitor = HoverVisitor(
            file=file,
            position=Position(
                line=position.line,
                char=position.character,
            ),
        )
        return hover_visitor.process()

    def get_definition(
        self, uri: str, position: lsptypes.Position
    ) -> Optional[lsptypes.Location]:
        parser = Parser()
        file = parser.parse(self.documents[uri].encode())
        definition_visitor = DefinitionVisitor(
            file=file,
            position=Position(
                line=position.line,
                char=position.character,
            ),
        )
        range_ = definition_visitor.process()
        if range_ is None:
            return None
        return lsptypes.Location(uri=uri, range=to_lsp_range(range_))

    def get_type_definition(
        self, uri: str, position: lsptypes.Position
    ) -> Optional[lsptypes.Location]:
        parser = Parser()
        file = parser.parse(self.documents[uri].encode())
        type_infer_visitor = TypeInferVisitor(file=file)
        type_infer_visitor.process()
        type_definition_visitor = TypeDefinitionVisitor(
            file=file,
            position=Position(
                line=position.line,
                char=position.character,
            ),
        )
        range_ = type_definition_visitor.process()
        if range_ is None:
            return None
        return lsptypes.Location(uri=uri, range=to_lsp_range(range_))

    def get_code_actions(
        self, uri: str, position: lsptypes.Position
    ) -> Optional[List[lsptypes.TextEdit]]:
        parser = Parser()
        program = parser.parse(self.documents[uri].encode())
        code_actions_visitor = CodeActionVisitor(
            file=program,
            position=Position(
                line=position.line,
                char=position.character,
            ),
        )
        result = code_actions_visitor.process()
        logger.debug("Code action result: %s", result)
        if result is None:
            return None
        return [
            lsptypes.TextEdit(
                range=to_lsp_range(range_),
                new_text=new_text,
            )
            for range_, new_text in result
        ]
