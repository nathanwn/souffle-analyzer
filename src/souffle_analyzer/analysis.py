import os
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

import lsprotocol.types as lsptypes

from souffle_analyzer.ast import BUILTIN_TYPES, ErrorNode, Position, Range, Workspace
from souffle_analyzer.logging import logger
from souffle_analyzer.parser import Parser
from souffle_analyzer.sourceutil import (
    get_before_token,
    get_pair_symbol_score,
    get_words_in_consecutive_block_at_line,
)
from souffle_analyzer.visitor.code_action_visitor import CodeActionVisitor
from souffle_analyzer.visitor.definition_visitor import DefinitionVisitor
from souffle_analyzer.visitor.find_references_visitor import (
    FindDeclarationReferencesVisitor,
)
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
    workspace: Workspace = field(default_factory=lambda: Workspace())
    root_uri: str | None = field(default=None)

    def load_workspace(self, root_uri: str) -> None:
        self.root_uri = root_uri
        logger.info("Root URI provided: %s. Started loading workspace.", self.root_uri)
        if self.root_uri is None:
            return
        root_path = urlsplit(self.root_uri).path
        for path in Path(root_path).rglob("*.dl"):
            uri = Path(os.path.abspath(path)).as_uri()
            with open(path, encoding="utf-8") as f:
                text = f.read()
            self.load_document(uri, text)
        resolve_reference_visitor = ResolveDeclarationVisitor(self.workspace)
        resolve_reference_visitor.transform()

    def sync_workspace(self) -> None:
        resolve_reference_visitor = ResolveDeclarationVisitor(self.workspace)
        resolve_reference_visitor.transform()
        type_check_visitor = TypeInferVisitor(self.workspace)
        type_check_visitor.process()

    def load_document(self, uri: str, text: str) -> None:
        logger.debug("loading document %s", uri)
        parser = Parser(uri=uri, code=text.encode())
        document = parser.parse()
        self.workspace.documents[uri] = document

    def sync_document(self, uri, text: str) -> list[lsptypes.Diagnostic]:
        self.load_document(uri, text)
        self.sync_workspace()
        simple_semantic_check_visitor = SimpleSemanticCheckVisitor(
            self.workspace,
            uri,
        )
        diagnostics = simple_semantic_check_visitor.process()
        return diagnostics

    def open_document(self, uri: str, text: str) -> list[lsptypes.Diagnostic]:
        return self.sync_document(uri, text)

    def update_document(
        self, uri: str, changes: Sequence[lsptypes.TextDocumentContentChangeEvent]
    ) -> list[lsptypes.Diagnostic]:
        diagnostics: list[lsptypes.Diagnostic] = []
        for change in changes:
            if isinstance(change, lsptypes.TextDocumentContentChangePartial):
                pass
            if isinstance(change, lsptypes.TextDocumentContentChangeWholeDocument):
                logger.debug("update document")
                diagnostics.extend(self.sync_document(uri, change.text))
        return diagnostics

    def hover(self, uri: str, position: lsptypes.Position) -> tuple[str, Range] | None:
        hover_visitor = HoverVisitor(
            workspace=self.workspace,
            uri=uri,
            position=Position(
                line=position.line,
                character=position.character,
            ),
        )
        return hover_visitor.process()

    def get_definition(
        self, uri: str, position: lsptypes.Position
    ) -> lsptypes.Location | None:
        definition_visitor = DefinitionVisitor(
            workspace=self.workspace,
            uri=uri,
            position=Position(
                line=position.line,
                character=position.character,
            ),
        )
        location = definition_visitor.process()
        if location is None:
            return None
        return location.to_lsp_type()

    def get_references(
        self, uri: str, position: lsptypes.Position
    ) -> list[lsptypes.Location]:
        find_references_visitor = FindDeclarationReferencesVisitor(
            workspace=self.workspace,
            uri=uri,
            position=Position.from_lsp_type(position),
        )
        return [_.to_lsp_type() for _ in find_references_visitor.process()]

    def get_type_definition(
        self, uri: str, position: lsptypes.Position
    ) -> lsptypes.Location | None:
        type_definition_visitor = TypeDefinitionVisitor(
            workspace=self.workspace,
            uri=uri,
            position=Position(
                line=position.line,
                character=position.character,
            ),
        )
        location = type_definition_visitor.process()
        if location is None:
            return None
        return location.to_lsp_type()

    def get_completion_items(
        self,
        uri: str,
        position: lsptypes.Position,
        context: lsptypes.CompletionContext | None,
    ) -> list[lsptypes.CompletionItem]:
        code = self.workspace.documents[uri].code
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
            paren_scores = get_pair_symbol_score(code, ("(", ")"))
            curly_bracket_scores = get_pair_symbol_score(code, ("{", "}"))
            square_bracket_scores = get_pair_symbol_score(code, ("{", "}"))
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
                paren_scores[position.line][position.character] == 0
                and curly_bracket_scores[position.line][position.character] == 0
                and square_bracket_scores[position.line][position.character] == 0
                and (
                    before_token in [".input", ".output", ".printsize"]
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

    def get_type_name_completion_items(self, uri: str) -> list[lsptypes.CompletionItem]:
        completions = []
        for builtin_type in BUILTIN_TYPES:
            completions.append(
                lsptypes.CompletionItem(
                    label=builtin_type.name,
                    kind=lsptypes.CompletionItemKind.Reference,
                    documentation=builtin_type.doc,
                ),
            )
        for type_declaration in self.workspace.documents[uri].type_declarations:
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
    ) -> list[lsptypes.CompletionItem]:
        completions = []
        for relation_declaration in self.workspace.documents[uri].relation_declarations:
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
    ) -> list[lsptypes.TextEdit] | None:
        code_actions_visitor = CodeActionVisitor(
            workspace=self.workspace,
            uri=uri,
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
