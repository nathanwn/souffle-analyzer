from typing import Optional, TextIO, Tuple

from lsprotocol import converters
from lsprotocol.types import (
    METHOD_TO_TYPES,
    InitializedNotification,
    InitializeRequest,
    TextDocumentCodeActionRequest,
    TextDocumentCompletionRequest,
    TextDocumentDefinitionRequest,
    TextDocumentDidChangeNotification,
    TextDocumentDidOpenNotification,
    TextDocumentHoverRequest,
    TextDocumentReferencesRequest,
    TextDocumentTypeDefinitionRequest,
)

from souffle_analyzer import handler
from souffle_analyzer.analysis import AnalysisContext
from souffle_analyzer.logging import logger
from souffle_analyzer.rpc import JsonRpcNode


class LanguageServer(JsonRpcNode):
    def __init__(self, in_stream: TextIO, out_stream: TextIO):
        self.converter = converters.get_converter()
        self.ctx = AnalysisContext()
        super().__init__(in_stream, out_stream)

    def write_server_response(self, message: object) -> None:
        self.write_message(self.converter.unstructure(message))

    def handle_incoming_message(self, message: dict) -> None:
        method = message["method"]
        logger.debug('Got request with method: "%s"', method)

        request_type = get_request_type_from_method(method)

        if request_type is None:
            return None

        request = self.converter.structure(message, request_type)

        if isinstance(request, InitializeRequest):
            response = handler.handle_initialize_request(request, self.ctx)
            self.write_server_response(response)
        elif isinstance(request, InitializedNotification):
            logger.info("Connection established successfully.")
        elif isinstance(request, TextDocumentDidOpenNotification):
            diagnostic_notification = (
                handler.handle_text_document_did_open_notification(request, self.ctx)
            )
            logger.info("Opened: %s", request.params.text_document.uri)
            self.write_server_response(diagnostic_notification)
        elif isinstance(request, TextDocumentDidChangeNotification):
            diagnostic_notification = (
                handler.handle_text_document_did_change_notification(request, self.ctx)
            )
            logger.info("Changed: %s", request.params.text_document.uri)
            self.write_server_response(diagnostic_notification)
        elif isinstance(request, TextDocumentHoverRequest):
            response = handler.handle_text_document_hover_request(request, self.ctx)
            self.write_server_response(response)
        elif isinstance(request, TextDocumentDefinitionRequest):
            response = handler.handle_text_document_definition_request(
                request, self.ctx
            )
            self.write_server_response(response)
        elif isinstance(request, TextDocumentReferencesRequest):
            response = handler.handle_text_document_reference_request(
                request,
                self.ctx,
            )
            self.write_server_response(response)
        elif isinstance(request, TextDocumentTypeDefinitionRequest):
            response = handler.handle_text_document_type_definition_request(
                request, self.ctx
            )
            self.write_server_response(response)
        elif isinstance(request, TextDocumentCompletionRequest):
            response = handler.handle_text_document_completion_request(
                request, self.ctx
            )
            self.write_server_response(response)
        elif isinstance(request, TextDocumentCodeActionRequest):
            response = handler.handle_text_document_code_action_request(
                request, self.ctx
            )
            self.write_server_response(response)
        else:
            logger.debug('Request: "%s"', request)

    def serve(self) -> None:
        while msg := self.read_message():
            self.handle_incoming_message(msg)


def get_lsp_types_from_method(method: str) -> Optional[Tuple[type, ...]]:
    return METHOD_TO_TYPES.get(method)


def get_request_type_from_method(method: str) -> Optional[type]:
    types = get_lsp_types_from_method(method)
    if types is None:
        return None
    return types[0]


def get_response_type_from_method(method: str) -> Optional[type]:
    types = get_lsp_types_from_method(method)
    if types is None:
        return None
    return types[1]
