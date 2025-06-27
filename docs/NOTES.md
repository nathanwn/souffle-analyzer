## Philosophy

The project was initially built with the following criteria in mind:

* Ensure support for all 3 operating systems Windows, Linux, and MacOS to certain extends: all tests should pass and the project should build successfully on any supposedly supported platform.
* Ensure easy dev setup. Support almost [all supported Python versions still currently under LTS](https://devguide.python.org/versions/#supported-versions).
* Ensure extensive testing.
* Aim for reasonably good performance.

Usability remains the most important criteria in most cases.


## Roadmap

In the near future, the following will be focused on:

* Obtaining higher support coverage over the syntax of the Souffle language. Although the tree-sitter parser works quite well, we have not fully support every construct of the language within the language server itself.
* Investigating the well-known [UTF-16 encoding-related issue](https://github.com/Microsoft/language-server-protocol/issues/376), which is likely to cause some bugs.
* Stabilizing and enhancing the currently-available capabilities. A reasonable amount of effort will be spent in:
  * Type inference and semantic checking for better diagnostics and hover.
  * Handle import relationship between files.
  * More accurate and faster code completion.

Some other features that may be consider:

* Support for more complex but reasonably useful capabilities, especially refactoring-related ones such as rename.
* Support for C-style macros, which is in and of itself an interesting technical problem.


## Author's note

1. Why Python?

At the time this project was started, the author was the most comfortable with Python and want to embark on a challenge of making the most out of the language.

The original parser is a tree-sitter parser, which allows for implementing the language server in a few other languages. The closest contender was Rust. It may become a candidate language in case of a rewrite (if there will ever be one).

2. Why may the project be not super active?

The author of this project no longer work day to day with the Souffle language and it has been hard at times to find motivation maintaining this project.
