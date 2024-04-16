import { ExtensionContext, workspace } from 'vscode';

import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions
} from 'vscode-languageclient/node';

let client: LanguageClient;

export function activate(context: ExtensionContext) {
    const command: string = workspace.getConfiguration("souffleAnalyzer").get("command");
    const logPath: string = workspace.getConfiguration("souffleAnalyzer").get("logPath");
    const serverOptions: ServerOptions = {
        command: command,
        args: ['server', '--verbose', '--log-file', logPath],
    };

    // Options to control the language client
    const clientOptions: LanguageClientOptions = {
        documentSelector: [{ scheme: 'file', language: 'souffle' }]
    };

    // Create the language client and start the client.
    client = new LanguageClient(
        'souffle-analyzer',
        serverOptions,
        clientOptions
    );

    // Start the client. This will also launch the server
    client.start();
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}
