import * as vscode from 'vscode';
import { ExtensionContext, workspace } from 'vscode';

import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions
} from 'vscode-languageclient/node';

let client: LanguageClient;

export function activate(context: ExtensionContext) {
    let command = workspace
        .getConfiguration('souffleAnalyzer')
        .get<string>('command');
    const logFile = workspace
        .getConfiguration('souffleAnalyzer')
        .get<string>('logFile');
    const args = ['server', '--verbose'];
    if (command === undefined) {
        command = 'souffle-analyzer';
    }
    if (typeof logFile === 'string') {
        args.push('--log-file', logFile);
    }
    const serverOptions: ServerOptions = {
        command: command,
        args: args
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
    client
        .start()
        .catch(err => vscode.window.showErrorMessage(`Cannot start server: ${err}`));
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}
