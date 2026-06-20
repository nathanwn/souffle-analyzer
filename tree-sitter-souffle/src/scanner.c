#include <stdio.h>
#include <string.h>

#include "tree_sitter/parser.h"

enum TokenType {
    DECL_KW,
    INPUT_KW,
    OUTPUT_KW,
    TYPE_KW,
    FUNCTOR_KW,
    INCLUDE_KW,
    PRINTSIZE_KW,
    LIMITSIZE_KW,
    PLAN_KW,
    COMP_KW,
    INIT_KW,
    OVERRIDE_KW,
    NUMBER_TYPE_KW,
    SYMBOL_TYPE_KW,
    // MAX_AGGREGATOR_KW,
    // MIN_AGGREGATOR_KW,
};

static bool is_whitespace(int32_t c) {
    return c == ' ' || c == '\t' || c == '\n' || c == '\r';
}

static inline int32_t advance(TSLexer *lexer) {
    lexer->advance(lexer, false);
    return lexer->lookahead;
}

static inline int32_t skip(TSLexer *lexer) {
    lexer->advance(lexer, true);
    return lexer->lookahead;
}

void *tree_sitter_souffle_external_scanner_create() {
    return NULL;
}

void tree_sitter_souffle_external_scanner_destroy(void *payload) {
}

unsigned tree_sitter_souffle_external_scanner_serialize(void *payload,
                                                        char *buffer) {
    return 0;
}

void tree_sitter_souffle_external_scanner_deserialize(void *payload,
                                                      const char *buffer,
                                                      unsigned length) {
}

static void skip_whitespaces(TSLexer *lexer) {
    for (int32_t c = lexer->lookahead; !lexer->eof(lexer) && is_whitespace(c);
         c = skip(lexer)) {
    }
}

static char *next_token(TSLexer *lexer) {
    skip_whitespaces(lexer);
    if (lexer->eof(lexer)) return NULL;

    int buf_limit = 256;
    char *buf = (char *)malloc((buf_limit + 1) * sizeof(char));
    int32_t i = 0;

    for (int32_t c = lexer->lookahead;
         !lexer->eof(lexer) && !is_whitespace(c) && i < buf_limit;
         c = advance(lexer)) {
        buf[i] = c;
        i++;
    }
    buf[i] = '\0';
    return buf;
}

bool tree_sitter_souffle_external_scanner_scan(void *payload, TSLexer *lexer,
                                               const bool *valid_symbols) {
    char *token = next_token(lexer);
    if (token == NULL) return false;

    // Use mark_end to stop consuming new characters.
    // See: https://github.com/tree-sitter/tree-sitter/issues/281
    lexer->mark_end(lexer);
    bool matched = false;

    if (valid_symbols[DECL_KW] && strcmp(token, ".decl") == 0) {
        lexer->result_symbol = DECL_KW;
        matched = true;
    }
    if (valid_symbols[INPUT_KW] && strcmp(token, ".input") == 0) {
        lexer->result_symbol = INPUT_KW;
        matched = true;
    }
    if (valid_symbols[OUTPUT_KW] && strcmp(token, ".output") == 0) {
        lexer->result_symbol = OUTPUT_KW;
        matched = true;
    }
    if (valid_symbols[TYPE_KW] && strcmp(token, ".type") == 0) {
        lexer->result_symbol = TYPE_KW;
        matched = true;
    }
    if (valid_symbols[FUNCTOR_KW] && strcmp(token, ".functor") == 0) {
        lexer->result_symbol = FUNCTOR_KW;
        matched = true;
    }
    if (valid_symbols[INCLUDE_KW] && strcmp(token, ".include") == 0) {
        lexer->result_symbol = INCLUDE_KW;
        matched = true;
    }
    if (valid_symbols[PRINTSIZE_KW] && strcmp(token, ".printsize") == 0) {
        lexer->result_symbol = PRINTSIZE_KW;
        matched = true;
    }
    if (valid_symbols[LIMITSIZE_KW] && strcmp(token, ".limitsize") == 0) {
        lexer->result_symbol = LIMITSIZE_KW;
        matched = true;
    }
    if (valid_symbols[PLAN_KW] && strcmp(token, ".plan") == 0) {
        lexer->result_symbol = PLAN_KW;
        matched = true;
    }
    if (valid_symbols[COMP_KW] && strcmp(token, ".comp") == 0) {
        lexer->result_symbol = COMP_KW;
        matched = true;
    }
    if (valid_symbols[INIT_KW] && strcmp(token, ".init") == 0) {
        lexer->result_symbol = INIT_KW;
        matched = true;
    }
    if (valid_symbols[OVERRIDE_KW] && strcmp(token, ".override") == 0) {
        lexer->result_symbol = OVERRIDE_KW;
        matched = true;
    }
    if (valid_symbols[NUMBER_TYPE_KW] && strcmp(token, ".number_type") == 0) {
        lexer->result_symbol = NUMBER_TYPE_KW;
        matched = true;
    }
    if (valid_symbols[SYMBOL_TYPE_KW] && strcmp(token, ".symbol_type") == 0) {
        lexer->result_symbol = SYMBOL_TYPE_KW;
        matched = true;
    }

    // This issue now being handled using the `conflicts` feature of
    // tree-sitter. This snippet of code is just kept here for future reference.
    //
    // if (valid_symbols[MAX_AGGREGATOR_KW] || valid_symbols[MIN_AGGREGATOR_KW])
    // {
    //     enum TokenType token_type = -1;
    //     if (strcmp(token, "max") == 0) {
    //         token_type = MAX_AGGREGATOR_KW;
    //     } else if (strcmp(token, "min") == 0) {
    //         token_type = MIN_AGGREGATOR_KW;
    //     }

    //     if (token_type != -1) {
    //         skip_whitespaces(lexer);

    //         if (lexer->lookahead == '(') {
    //             // Handle `max ( argument ) :`.
    //             // If `max ( argument )` is followed by a `:`, then this
    //             // should be an aggregator.

    //             // We first try to skip `( argument )`.
    //             int32_t paren = 1;
    //             advance(lexer);

    //             for (int32_t c = lexer->lookahead;
    //                  !lexer->eof(lexer) && paren > 0; c = advance(lexer)) {
    //                 if (c == '(') {
    //                     paren++;
    //                 } else if (c == ')') {
    //                     paren--;
    //                 }
    //             }

    //             // Then, we try to match the colon `:`.
    //             char *maybe_colon = next_token(lexer);

    //             if (strcmp(maybe_colon, ":") == 0) {
    //                 lexer->result_symbol = token_type;
    //                 matched = true;
    //             }

    //             free(maybe_colon);
    //         } else {
    //             // Handle `max argument :`.
    //             // This is simple.
    //             lexer->result_symbol = token_type;
    //             matched = true;
    //         }
    //     }
    // }

    free(token);
    return matched;
}
