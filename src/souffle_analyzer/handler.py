from importlib import metadata as importlib_metadata

from lsprotocol.types import (
    CodeAction,
    DiagnosticOptions,
    Hover,
    InitializeRequest,
    InitializeResponse,
    InitializeResult,
    InitializeResultServerInfoType,
    MarkupContent,
    MarkupKind,
    OptionalVersionedTextDocumentIdentifier,
    PublishDiagnosticsParams,
    ServerCapabilities,
    TextDocumentCodeActionRequest,
    TextDocumentCodeActionResponse,
    TextDocumentDefinitionRequest,
    TextDocumentDefinitionResponse,
    TextDocumentDidChangeNotification,
    TextDocumentDidOpenNotification,
    TextDocumentEdit,
    TextDocumentHoverRequest,
    TextDocumentHoverResponse,
    TextDocumentPublishDiagnosticsNotification,
    TextDocumentSyncKind,
    TextDocumentTypeDefinitionRequest,
    TextDocumentTypeDefinitionResponse,
    WorkspaceEdit,
)

from souffle_analyzer.analysis import AnalysisContext
from souffle_analyzer.logging import logger
from souffle_analyzer.metadata import PROG


def handle_initialize_request(request: InitializeRequest) -> InitializeResponse:
    client_info = request.params.client_info
    log_msg = ["Connecting to client"]

    if client_info is not None:
        log_msg.append(client_info.name)
        if client_info.version is not None:
            log_msg.extend(["version", client_info.version])

    logger.info(" ".join(log_msg))

    return InitializeResponse(
        id=request.id,
        result=InitializeResult(
            capabilities=ServerCapabilities(
                text_document_sync=TextDocumentSyncKind.Full,
                hover_provider=True,
                definition_provider=True,
                type_definition_provider=True,
                code_action_provider=True,
                diagnostic_provider=DiagnosticOptions(
                    # TODO: update this once the server support these capabilities.
                    inter_file_dependencies=False,
                    workspace_diagnostics=False,
                ),
            ),
            server_info=InitializeResultServerInfoType(
                name=PROG,
                version=importlib_metadata.version(PROG),
            ),
        ),
    )


def handle_text_document_did_open_notification(
    request: TextDocumentDidOpenNotification,
    ctx: AnalysisContext,
) -> TextDocumentPublishDiagnosticsNotification:
    uri = request.params.text_document.uri
    diagnostics = ctx.open_document(
        uri=uri,
        text=request.params.text_document.text,
    )
    return TextDocumentPublishDiagnosticsNotification(
        params=PublishDiagnosticsParams(uri=uri, diagnostics=diagnostics),
    )


def handle_text_document_did_change_notification(
    request: TextDocumentDidChangeNotification,
    ctx: AnalysisContext,
) -> TextDocumentPublishDiagnosticsNotification:
    uri = request.params.text_document.uri
    diagnostics = ctx.update_document(
        uri=uri,
        changes=request.params.content_changes,
    )
    return TextDocumentPublishDiagnosticsNotification(
        params=PublishDiagnosticsParams(uri=uri, diagnostics=diagnostics),
    )


def handle_text_document_hover_request(
    request: TextDocumentHoverRequest,
    ctx: AnalysisContext,
) -> TextDocumentHoverResponse:
    document_uri = request.params.text_document.uri
    position = request.params.position
    hover_result = ctx.hover(uri=document_uri, position=position)

    if hover_result is None:
        result = None
        logger.debug("No hover result.")
    else:
        contents, range_ = hover_result
        result = Hover(
            contents=MarkupContent(kind=MarkupKind.Markdown, value=contents),
            range=range_.to_lsp_type(),
        )
        logger.debug("Hover result found: %s", result)

    return TextDocumentHoverResponse(
        id=request.id,
        result=result,
    )


def handle_text_document_definition_request(
    request: TextDocumentDefinitionRequest,
    ctx: AnalysisContext,
) -> TextDocumentDefinitionResponse:
    document_uri = request.params.text_document.uri
    position = request.params.position
    definition_result = ctx.get_definition(uri=document_uri, position=position)

    if definition_result is None:
        logger.debug("No definition result.")
    else:
        logger.debug("Definition result found: %s", definition_result)

    return TextDocumentDefinitionResponse(
        id=request.id,
        result=definition_result,
    )


def handle_text_document_type_definition_request(
    request: TextDocumentTypeDefinitionRequest,
    ctx: AnalysisContext,
) -> TextDocumentTypeDefinitionResponse:
    document_uri = request.params.text_document.uri
    position = request.params.position
    type_definition_result = ctx.get_type_definition(
        uri=document_uri, position=position
    )
    return TextDocumentTypeDefinitionResponse(
        id=request.id,
        result=type_definition_result,
    )


def handle_text_document_code_action_request(
    request: TextDocumentCodeActionRequest,
    ctx: AnalysisContext,
) -> TextDocumentCodeActionResponse:
    uri = request.params.text_document.uri
    # Only support position-based code action for now
    position = request.params.range.start
    edits = ctx.get_code_actions(uri, position)
    if edits is None:
        result = []
    else:
        result = [
            CodeAction(
                title="Generate doc comment",
                edit=WorkspaceEdit(
                    document_changes=[
                        TextDocumentEdit(
                            text_document=OptionalVersionedTextDocumentIdentifier(
                                uri=request.params.text_document.uri,
                            ),
                            edits=list(edits),
                        ),
                    ]
                ),
            )
        ]
    return TextDocumentCodeActionResponse(
        id=request.id,
        result=list(result),
    )
