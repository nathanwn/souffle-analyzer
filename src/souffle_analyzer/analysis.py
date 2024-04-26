from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import lsprotocol.types as lsptypes

from souffle_analyzer.ast import BUILTIN_TYPES, ErrorNode, File, Position, Range
from souffle_analyzer.logging import logger
from souffle_analyzer.parser import Parser
from souffle_analyzer.sourceutil import (
    get_before_token,
    get_bracket_scores,
    get_words_in_consecutive_block_at_line,
)
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
    root_uri: Optional[str] = field(default=None)

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

    def get_completion_items(
        self,
        uri: str,
        position: lsptypes.Position,
        context: Optional[lsptypes.CompletionContext],
    ) -> List[lsptypes.CompletionItem]:
        code = self.documents[uri].code
        code_lines = code.splitlines()
        if context is None:
            return []
        if context.trigger_character == ".":
            if position.character == 1 or (
                position.character >= 2
                and code_lines[position.line][position.character - 2].isspace()
            ):
                return [
                    lsptypes.CompletionItem(
                        label="input",
                        documentation="input directive",
                    ),
                    lsptypes.CompletionItem(
                        label="output",
                        documentation="output directive",
                    ),
                    lsptypes.CompletionItem(
                        label="decl",
                        documentation="relation declaration directive",
                    ),
                    lsptypes.CompletionItem(
                        label="type",
                        documentation="type declaration directive",
                    ),
                ]
            else:
                return []
        else:
            bracket_scores = get_bracket_scores(code)
            before_token = get_before_token(
                code,
                position.line,
                position.character,
            )
            if before_token.endswith(":"):
                return self.get_type_name_completion_items(uri)
            elif (
                # This is essentially the score on the position before this.
                # See the property of the get_bracket_scores function.
                bracket_scores[position.line][position.character] == 0
                and (
                    before_token in [".input", ".output"]
                    or before_token.endswith(",")
                    or before_token.endswith(":-")
                    or before_token.endswith(".")
                    or before_token.endswith(")")
                )
            ):
                return self.get_relation_name_completion_items(uri)
            else:
                identifiers = {
                    *[item.label for item in self.get_type_name_completion_items(uri)],
                    *[
                        item.label
                        for item in self.get_relation_name_completion_items(uri)
                    ],
                }
                words = get_words_in_consecutive_block_at_line(code, position.line)
                suggested_words = []
                for word in words:
                    if word not in identifiers:
                        suggested_words.append(word)
                return [lsptypes.CompletionItem(label=word) for word in suggested_words]

    def get_type_name_completion_items(self, uri: str) -> List[lsptypes.CompletionItem]:
        completions = []
        for builtin_type in BUILTIN_TYPES:
            completions.append(
                lsptypes.CompletionItem(
                    label=builtin_type.name,
                    kind=lsptypes.CompletionItemKind.Reference,
                    documentation=builtin_type.doc,
                ),
            )
        for type_declaration in self.documents[uri].type_declarations:
            type_name = type_declaration.name.inner
            if isinstance(type_name, ErrorNode):
                continue
            completions.append(
                lsptypes.CompletionItem(
                    label=type_name.val,
                    kind=lsptypes.CompletionItemKind.Reference,
                    documentation="type",
                ),
            )
        return completions

    def get_relation_name_completion_items(
        self, uri: str
    ) -> List[lsptypes.CompletionItem]:
        completions = []
        for relation_declaration in self.documents[uri].relation_declarations:
            relation_name = relation_declaration.name.inner
            if isinstance(relation_name, ErrorNode):
                continue
            relation_declaration.get_doc()
            completions.append(
                lsptypes.CompletionItem(
                    label=relation_name.val,
                    kind=lsptypes.CompletionItemKind.Reference,
                    documentation=relation_declaration.get_doc(),
                ),
            )
        return completions

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
        if result is None:
            return None
        return [
            lsptypes.TextEdit(
                range=range_.to_lsp_type(),
                new_text=new_text,
            )
            for range_, new_text in result
        ]
