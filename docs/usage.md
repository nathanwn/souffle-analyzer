# Using souffle-analyzer

To try using souffle-analyzer, you need two things:

* The server, which is a souffle-analyzer executable.
* The client, which is a compatible text editor.

## The language server executable

You can access the pre-built executables in the project's [Release page](https://github.com/nathanwn/souffle-analyzer/releases/tag/nightly). Note: At the moment, we only offer the pre-release/nightly version.

Alternatively, you can build the server from source if you choose to. Just clone the project, create a virtual environment, and do `pip install .`.

## Text editors

### VS Code

We offer a `.vsix` VS Code extension that wires the language server to VS Code, which could also be found in the project's [Release page](https://github.com/nathanwn/souffle-analyzer/releases/tag/nightly).

To install the plugin from the `.vsix` file in VS Code: `Extensions` -> `Views and More Actions` (the three-dot button) -> `Install from VSIX...`, and choose the `.vsix` file you downloaded.

### Neovim

For Neovim, there should be multiple ways to do it. The following is just one of the methods that has been working well for me. (Note: requires Neovim >= 0.8)

1. Add the `souffle` filetype. In your `filetype.lua` file:

```lua
vim.filetype.add({
  extension = {
    dl = "souffle",
  },
})
```

2. Create an auto command triggered on the `FileType` event to start souffle-analyzer:

```lua
vim.api.nvim_create_autocmd("FileType", {
    pattern = { "souffle" },
    callback = function()
        vim.lsp.start({
            name = "souffle-analyzer",
            cmd = {
                "souffle-analyzer",  -- or path to the executable if it is not in PATH
                "server",
            },
            root_dir = vim.fs.dirname(vim.fs.find({ ".git" }, { upward = true })[1]),
        })
    end,
})
```

## Other text editors

As long as your text editor supports LSP, you will probably have no problem using `souffle-analyzer` once you figure out how to configure LSP for your editor.
