#ifndef TREE_SITTER_SOUFFLE_H_
#define TREE_SITTER_SOUFFLE_H_

typedef struct TSLanguage TSLanguage;

#ifdef __cplusplus
extern "C" {
#endif

const TSLanguage *tree_sitter_souffle(void);

#ifdef __cplusplus
}
#endif

#endif // TREE_SITTER_SOUFFLE_H_
