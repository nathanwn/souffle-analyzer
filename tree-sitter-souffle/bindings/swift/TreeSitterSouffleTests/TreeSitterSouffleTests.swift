import XCTest
import SwiftTreeSitter
import TreeSitterSouffle

final class TreeSitterSouffleTests: XCTestCase {
    func testCanLoadGrammar() throws {
        let parser = Parser()
        let language = Language(language: tree_sitter_souffle())
        XCTAssertNoThrow(try parser.setLanguage(language),
                         "Error loading Souffle grammar")
    }
}
