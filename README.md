# souffle-analyzer

souffle-analyzer is a [language server](https://microsoft.github.io/language-server-protocol) for the [Souffle logic programming language](https://souffle-lang.github.io/).

![](./docs/img/navigation.gif)

The code in the demonstration GIF above is from the [cclyzer++](https://github.com/galoisinc/cclyzerpp) project.

## Features

It is still early days for the project, so do expect things to be a bit rough around the edges.

The following language server capabilities are currently available at both file level and workspace level:

- Go to defintion
  - for relations and types
- Go to type defintion
  - for constant or variable attributes within relation references or facts
- Go to references
  - for relations
- Basic code completion
- Hover
  - for relations and types
- Code actions
  - generate docstring template for relation declarations
- Basic diagnostics


## Try it out

See [./docs/usage.md](./docs/usage.md).


## Philosophy

The project was initially built with the following criteria in mind:

* **We hope everyone getting to know the project can try it**.
  * For potential users, we try to support all 3 operating systems Windows, Linux, and MacOS to certain extends: all tests should pass and the project should build successfully on any supposedly supported platform.
  * For people wanting to hack on the project, we also make sure the project works on [all supported Python versions still currently under LTS](https://devguide.python.org/versions/#supported-versions) and reasonably easy to set up. Supporting all versions of Python also allow us to think about publishing a library from the project later on.
* **We value user experience and stability**. We aim for extensive testing, minimum amount of bugs, and reasonably good performance.


## Roadmap

In the near future, we will focus on the following items:

* Obtain higher support coverage over the syntax of the Souffle language. Although the tree-sitter parser works quite well, we have not fully support every construct of the language within the language server itself.
* Investigate the well-known [UTF-16 encoding-related issue](https://github.com/Microsoft/language-server-protocol/issues/376), which is likely to cause some bugs.
* Stabilize and enhance the currently-available capabilities. A reasonable amount of effort will be spent in:
  * Type inference and semantic checking for better diagnostics and hover.
  * Handle import relationship between files.
  * More accurate and faster code completion.

Some other features that we will consider:

* Add support for more complex but reasonably useful capabilities, especially refactoring-related ones such as rename.
* Support for C-style macros, which is in and of itself an interesting technical problem.


## You may ask...

See [./docs/faq.md](./docs/faq.md).
