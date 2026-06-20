const PREC = {
    or: 10,
    and: 11,
    not: 12,
    compare: 13,
    bitwise_or: 14,
    bitwise_and: 15,
    xor: 16,
    shift: 17,
    add: 18,
    mul: 19,
    unary: 20,
    power: 21,
    paren_exp: 22,
    fun_call: 23,
};

module.exports = grammar({
    name: "souffle",

    externals: ($) => [
        $.decl_kw,
        $.input_kw,
        $.output_kw,
        $.type_kw,
        $.functor_kw,
        $.include_kw,
        $.printsize_kw,
        $.limitsize_kw,
        $.plan_kw,
        $.comp_kw,
        $.init_kw,
        $.override_kw,
        /// deprecated keywords
        $.number_type_kw,
        $.symbol_type_kw,
        // $.max_aggregator_kw,
        // $.min_aggregator_kw,
    ],

    extras: ($) => [$.line_comment, $.block_comment, /\s/],

    conflicts: ($) => [
        // `max(...)` and `min(...)` can either be an aggregator head, or
        // a functor invocation. Distinguishing between the two requires multiple
        // lookaheads.
        // Tree-sitter, being a GLR parser, can handle this case with the conflicts
        // list.
        [$.aggregator_head, $.intrinsic_functor_name],
    ],

    rules: {
        source_file: ($) => repeat($._element),
        _element: ($) =>
            choice(
                $.directive,
                $.include_directive,
                $.relation_decl,
                $.rule,
                $.fact,
                $.type_decl,
                $.deprecated_type_decl,
                $.functor_decl,
                $.component_decl,
                $.component_init,
                $.preproc_directive,
                $.pragma,
            ),
        preproc_directive: ($) =>
            choice(
                $.preproc_include,
                $.preproc_if,
                $.preproc_elif,
                $.preproc_else,
                $.preproc_ifdef,
                $.preproc_ifndef,
                $.preproc_endif,
                $.preproc_define,
            ),
        preproc_include: ($) =>
            seq("#include", alias($.string_literal, $.path_spec)),
        preproc_if: ($) => seq("#if", $._preproc_exp),
        preproc_elif: ($) => seq("#elif", $._preproc_exp),
        preproc_else: (_) => "#else",
        preproc_ifdef: ($) => seq("#ifdef", $.identifier),
        preproc_ifndef: ($) => seq("#ifndef", $.identifier),
        preproc_endif: (_) => "#endif",
        preproc_define: ($) => seq("#define", $.preproc_macro),
        preproc_macro: (_) => /\S([^\n]|\\\r?\n)*/,
        _preproc_exp: ($) =>
            choice(
                $.identifier,
                $._integer,
                $.preproc_binary_exp,
                $.preproc_defined_exp,
            ),
        preproc_defined_exp: ($) =>
            prec(
                PREC.fun_call,
                seq(
                    "defined",
                    choice($._preproc_exp, seq("(", $._preproc_exp, ")")),
                ),
            ),
        preproc_binary_exp: ($) => {
            const table = [
                [prec.left, "+", PREC.add],
                [prec.left, "-", PREC.add],
                [prec.left, "*", PREC.mul],
                [prec.left, "/", PREC.mul],
                [prec.left, "<", PREC.compare],
                [prec.left, "<=", PREC.compare],
                [prec.left, ">", PREC.compare],
                [prec.left, ">=", PREC.compare],
                [prec.left, "==", PREC.compare],
                [prec.left, "&&", PREC.and],
                [prec.left, "||", PREC.or],
                [prec.left, "<<", PREC.shift],
                [prec.left, ">>", PREC.shift],
            ];

            return choice(
                ...table.map(([fn, operator, precedence]) =>
                    fn(
                        precedence,
                        seq(
                            field("lhs", $._preproc_exp),
                            field("op", operator),
                            field("rhs", $._preproc_exp),
                        ),
                    ),
                ),
            );
        },
        ifdefine_preproc_directive: ($) =>
            seq("#if", "define", "(", $.identifier, ")"),
        relation_decl: ($) =>
            seq(
                $.decl_kw,
                field("name", commaSep1($.identifier)),
                "(",
                optional(commaSep1($.attribute)),
                ")",
                repeat($.relation_qualifier),
                optional($.choice_domain),
            ),
        relation_qualifier: (_) =>
            choice(
                "eqrel",
                "btree",
                "btree_delete",
                "brie",
                "no_magic",
                "magic",
                "no_inline",
                "inline",
                "override",
                "overridable",
                // legacy syntax
                "input",
                "output",
                "printsize",
            ),
        choice_domain: ($) =>
            seq("choice-domain", commaSep1($.choice_domain_attribute)),
        choice_domain_attribute: ($) =>
            choice(
                alias($.identifier, $.choice_domain_single_attribute),
                $.choice_domain_tuple_attribute,
            ),
        choice_domain_tuple_attribute: ($) =>
            seq("(", commaSep1($.identifier), ")"),
        rule: ($) =>
            seq(
                field("head", choice($.rule_head, $.subsumption_head)),
                ":-",
                field("body", $.disjunction),
                ".",
                optional($.query_plan),
            ),
        rule_head: ($) => commaSep1($.atom),
        subsumption_head: ($) =>
            seq(field("first", $.atom), "<=", field("second", $.atom)),
        disjunction: ($) => sep1($.conjunction, ";"),
        conjunction: ($) => commaSep1($.conjunction_clause),
        conjunction_clause: ($) =>
            seq(
                alias(repeat("!"), $.neg),
                choice($.atom, $.constraint, seq("(", $.disjunction, ")")),
            ),
        constraint: ($) =>
            choice(
                $.binary_constraint,
                $.boolean_literal,
                // TODO: match and contains
            ),
        binary_constraint: ($) =>
            seq(
                field("lhs", $.argument),
                field("op", choice("<", ">", "<=", ">=", "=", "!=")),
                field("rhs", $.argument),
            ),
        query_plan: ($) =>
            seq(
                $.plan_kw,
                commaSep1(
                    seq(
                        $._number,
                        ":",
                        "(",
                        optional(commaSep1($._number)),
                        ")",
                    ),
                ),
            ),
        directive: ($) =>
            seq(
                $.directive_qualifier,
                commaSep1($.qualified_name),
                optional(
                    seq(
                        "(",
                        optional(commaSep1($.directive_attribute_assignment)),
                        ")",
                    ),
                ),
            ),
        directive_qualifier: ($) =>
            choice($.input_kw, $.output_kw, $.printsize_kw, $.limitsize_kw),
        directive_attribute_assignment: ($) =>
            seq(
                field("directive_attribute", $.identifier),
                "=",
                field("directive_value", $.directive_value),
            ),
        directive_value: ($) =>
            choice(
                $.string_literal,
                $.identifier,
                $.boolean_literal,
                $._number,
            ),
        include_directive: ($) => seq($.include_kw, $.string_literal),
        qualified_name: ($) => sep1($.identifier, "."),
        argument: ($) =>
            choice(
                $.constant,
                $.variable,
                alias("nil", $.nil),
                $.record_init,
                $.branch_init,
                $.unary_operation,
                $.binary_operation,
                $.type_conversion,
                $.aggregator,
                $.range_expression,
                $.functor_invocation,
                $.paren_argument,
            ),
        constant: ($) => choice($.string_literal, $._number),
        variable: ($) => choice($.identifier, "_"),
        record_init: ($) => seq("[", optional(commaSep1($.argument)), "]"),
        branch_init: ($) =>
            seq(
                "$",
                field("name", $.qualified_name),
                "(",
                field("args", optional(commaSep1($.argument))),
                ")",
            ),
        unary_operation: ($) =>
            prec(6, seq(alias(choice("-", "bnot", "lnot"), $.op), $.argument)),
        binary_operation: ($) =>
            choice(
                prec.left(
                    5,
                    seq(
                        alias($.argument, $.lhs),
                        alias("^", $.op),
                        alias($.argument, $.rhs),
                    ),
                ),
                prec.left(
                    4,
                    seq(
                        alias($.argument, $.lhs),
                        alias(choice("*", "/", "%"), $.op),
                        alias($.argument, $.rhs),
                    ),
                ),
                prec.left(
                    3,
                    seq(
                        alias($.argument, $.lhs),
                        alias(choice("+", "-"), $.op),
                        alias($.argument, $.rhs),
                    ),
                ),
                prec.left(
                    2,
                    seq(
                        alias($.argument, $.lhs),
                        alias(choice("land", "lor", "lxor"), $.op),
                        alias($.argument, $.rhs),
                    ),
                ),
                prec.left(
                    1,
                    seq(
                        alias($.argument, $.lhs),
                        alias(
                            choice(
                                "band",
                                "bor",
                                "bxor",
                                "bshl",
                                "bshr",
                                "bshru",
                            ),
                            $.op,
                        ),
                        alias($.argument, $.rhs),
                    ),
                ),
            ),
        type_conversion: ($) =>
            seq("as", "(", $.argument, ",", $.type_name, ")"),
        aggregator: ($) => seq($.aggregator_head, ":", $.aggregator_body),
        aggregator_head: ($) =>
            choice(
                seq(
                    alias(
                        choice(
                            // $.max_aggregator_kw,
                            // $.min_aggregator_kw,
                            "max",
                            "min",
                            "mean",
                            "sum",
                        ),
                        $.aggregate_op,
                    ),
                    $.argument,
                ),
                "count",
            ),
        aggregator_body: ($) => choice(seq("{", $.disjunction, "}"), $.atom),
        range_expression: ($) =>
            seq(
                "range",
                "(",
                field("range_from", $.argument),
                ",",
                field("range_to", $.argument),
                optional(seq(",", field("range_step", optional($.argument)))),
                ")",
            ),
        functor_invocation: ($) =>
            seq(
                field(
                    "name",
                    choice(
                        $.user_defined_functor_name,
                        $.intrinsic_functor_name,
                    ),
                ),
                "(",
                field("args", optional(commaSep1($.argument))),
                ")",
            ),
        user_defined_functor_name: ($) => seq("@", $.qualified_name),
        intrinsic_functor_name: ($) =>
            choice(
                "ord",
                "to_float",
                "to_number",
                "to_string",
                "to_unsigned",
                "cat",
                "strlen",
                "substr",
                "autoinc",
                "min",
                "max",
                "sin",
                "cos",
                "tan",
                "asin",
                "acos",
                "atan",
                "sinh",
                "cosh",
                "tanh",
                "asinh",
                "acosh",
                "atanh",
                "log",
                "exp",
            ),
        paren_argument: ($) => seq("(", $.argument, ")"),
        attribute: ($) =>
            seq(field("name", $.identifier), ":", field("type", $.type_name)),
        fact: ($) => seq($.atom, "."),
        type_decl: ($) =>
            seq(
                $.type_kw,
                field("name", $.identifier),
                optional(choice($.subtype_decl, $.eq_type_decl)),
            ),
        deprecated_type_decl: ($) =>
            seq(choice($.number_type_kw, $.symbol_type_kw), $.type_name),
        subtype_decl: ($) => seq(field("type_relation_op", "<:"), $.type_name),
        eq_type_decl: ($) =>
            seq(
                field("type_relation_op", "="),
                choice(
                    $.union_type,
                    $.type_name,
                    $.record_type,
                    $.abstract_data_type,
                ),
            ),
        union_type: ($) => prec(2, sep2($.type_name, "|")),
        type_name: ($) =>
            choice(
                $.primitive_type,
                alias($.qualified_name, $.user_defined_type_name),
            ),
        record_type: ($) => seq("[", optional(commaSep1($.attribute)), "]"),
        abstract_data_type: ($) => sep1($.adt_branch, "|"),
        adt_branch: ($) =>
            seq($.identifier, "{", optional(commaSep1($.attribute)), "}"),
        primitive_type: (_) => choice("number", "symbol", "unsigned", "float"),
        functor_decl: ($) =>
            seq(
                $.functor_kw,
                field("name", $.identifier),
                "(",
                optional(commaSep1($.functor_attribute)),
                ")",
                ":",
                $.type_name,
                optional(field("stateful", $.stateful)),
            ),
        functor_attribute: ($) => choice($.attribute, $.type_name),
        stateful: (_) => token("stateful"),
        component_decl: ($) =>
            seq(
                $.comp_kw,
                sep1($.component_type, choice(":", ",")),
                "{",
                repeat(
                    choice(
                        $.type_decl,
                        $.relation_decl,
                        $.rule,
                        $.fact,
                        $.directive,
                        $.component_override,
                        $.component_init,
                        $.component_decl,
                    ),
                ),
                "}",
            ),
        component_type: ($) =>
            seq($.identifier, optional(seq("<", commaSep1($.identifier), ">"))),
        component_override: ($) => seq($.override_kw, $.identifier),
        component_init: ($) =>
            seq($.init_kw, $.identifier, "=", $.component_type),
        pragma: ($) =>
            seq(
                ".pragma",
                field("flag_name", $.string_literal),
                field("flag_value", optional($.string_literal)),
            ),
        atom: ($) =>
            seq(
                field("name", $.qualified_name),
                "(",
                field("args", optional(commaSep1($.argument))),
                ")",
            ),
        boolean_literal: (_) => choice("true", "false"),
        string_literal: (_) =>
            token(seq('"', repeat(choice(/[^\\"\n]/, /\\(.|\n)/)), '"')),
        line_comment: (_) => token(seq("//", /[^\n]*/)),
        block_comment: (_) => token(seq("/*", /[^*]*\*+([^/*][^*]*\*+)*/, "/")),
        identifier: (_) => /[\?a-zA-Z_][\?a-zA-Z0-9_]*/,
        hex: (_) => /0x([0-9]|[A-F]|[a-f])+/,
        binary: (_) => /0b[0-1]+/,
        decimal: (_) => /[0-9]+/,
        unsigned: (_) => /[0-9]+u/,
        float: (_) => {
            const decimal = /[0-9]+/;
            const exponent = seq(/[eE][\+-]?/, decimal);
            return token(seq(decimal, ".", decimal, optional(exponent)));
        },
        _integer: ($) => choice($.hex, $.binary, $.decimal, $.unsigned),
        _number: ($) => choice($._integer, $.float),
    },
});

function commaSep1(rule) {
    return sep1(rule, ",");
}

function sep2(rule, separator) {
    return seq(rule, separator, rule, repeat(seq(separator, rule)));
}

function sep1(rule, separator) {
    return seq(rule, repeat(seq(separator, rule)));
}
