package tree_sitter_souffle_test

import (
	"testing"

	tree_sitter "github.com/tree-sitter/go-tree-sitter"
	tree_sitter_souffle "github.com/nathanwn/tree-sitter-souffle/bindings/go"
)

func TestCanLoadGrammar(t *testing.T) {
	language := tree_sitter.NewLanguage(tree_sitter_souffle.Language())
	if language == nil {
		t.Errorf("Error loading Souffle grammar")
	}
}
