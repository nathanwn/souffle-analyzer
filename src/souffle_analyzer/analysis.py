from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import lsprotocol.types as lsptypes

from souffle_analyzer.ast import File, Position, Range
from souffle_analyzer.logging import logger
from souffle_analyzer.parser import Parser
from souffle_analyzer.visitor.code_action_visitor import CodeActionVisitor
from souffle_analyzer.visitor.definition_visitor import DefinitionVisitor
from souffle_analyzer.visitor.find_references_visitor import FindReferencesVisitor
from souffle_analyzer.visitor.hover_visitor import HoverVisitor
from souffle_analyzer.visitor.resolve_declaration_visitor import (
    ResolveDeclarationVisitor,
)
from souffle_analyzer.visitor.simple_semantic_check_visitor import (
    SimpleSemanticCheckVisitor,
)
from souffle_analyzer.visitor.type_check_visitor import TypeInferVisitor
from souffle_analyzer.visitor.type_definition_visitor import TypeDefinitionVisitor


@dataclass
class AnalysisContext:
    documents: Dict[str, File] = field(default_factory=dict)

    def load_document(self, uri: str, text: str) -> List[lsptypes.Diagnostic]:
        for line in text.splitlines():
            logger.debug(line)
        parser = Parser()
        file = parser.parse(text.encode())
        resolve_reference_visitor = ResolveDeclarationVisitor(file)
        resolve_reference_visitor.transform()
        simple_semantic_check_visitor = SimpleSemanticCheckVisitor(file)
        diagnostics = simple_semantic_check_visitor.process()
        self.documents[uri] = file
        return diagnostics

    def open_document(self, uri: str, text: str) -> List[lsptypes.Diagnostic]:
        logger.debug("open document")
        return self.load_document(uri, text)

    def update_document(
        self, uri: str, changes: List[lsptypes.TextDocumentContentChangeEvent]
    ) -> List[lsptypes.Diagnostic]:
        diagnostics: List[lsptypes.Diagnostic] = []
        for change in changes:
            if isinstance(change, lsptypes.TextDocumentContentChangeEvent_Type1):
                pass
            if isinstance(change, lsptypes.TextDocumentContentChangeEvent_Type2):
                logger.debug("update document")
                self.load_document(uri, change.text)
        return diagnostics

    def hover(
        self, uri: str, position: lsptypes.Position
    ) -> Optional[Tuple[str, Range]]:
        hover_visitor = HoverVisitor(
            file=self.documents[uri],
            position=Position(
                line=position.line,
                character=position.character,
            ),
        )
        return hover_visitor.process()

    def get_definition(
        self, uri: str, position: lsptypes.Position
    ) -> Optional[lsptypes.Location]:
        definition_visitor = DefinitionVisitor(
            file=self.documents[uri],
            position=Position(
                line=position.line,
                character=position.character,
            ),
        )
        range_ = definition_visitor.process()
        if range_ is None:
            return None
        return lsptypes.Location(uri=uri, range=range_.to_lsp_type())

    def get_references(
        self, uri: str, position: lsptypes.Position
    ) -> List[lsptypes.Location]:
        find_references_visitor = FindReferencesVisitor(
            file=self.documents[uri],
            position=Position.from_lsp_type(position),
        )
        ranges = find_references_visitor.process()
        locations = []
        for range_ in ranges:
            locations.append(lsptypes.Location(uri=uri, range=range_.to_lsp_type()))
        return locations

    def get_type_definition(
        self, uri: str, position: lsptypes.Position
    ) -> Optional[lsptypes.Location]:
        file = self.documents[uri]
        type_check_visitor = TypeInferVisitor(file=file)
        type_check_visitor.process()
        type_definition_visitor = TypeDefinitionVisitor(
            file=file,
            position=Position(
                line=position.line,
                character=position.character,
            ),
        )
        range_ = type_definition_visitor.process()
        if range_ is None:
            return None
        return lsptypes.Location(uri=uri, range=range_.to_lsp_type())

    def get_code_actions(
        self, uri: str, position: lsptypes.Position
    ) -> Optional[List[lsptypes.TextEdit]]:
        code_actions_visitor = CodeActionVisitor(
            file=self.documents[uri],
            position=Position(
                line=position.line,
                character=position.character,
            ),
        )
        result = code_actions_visitor.process()
        logger.debug("Code action result: %s", result)
        if result is None:
            return None
        return [
            lsptypes.TextEdit(
                range=range_.to_lsp_type(),
                new_text=new_text,
            )
            for range_, new_text in result
        ]
