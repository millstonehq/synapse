(
  (comment)? @comment
  (function_definition
    declarator: (function_declarator
      declarator: (identifier) @name
      parameters: (parameter_list) @parameters
    )
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (struct_specifier
    name: (type_identifier) @name
    body: (field_declaration_list)? @body
  ) @definition
)

(
  (comment)? @comment
  (enum_specifier
    name: (type_identifier) @name
    body: (enumerator_list)? @body
  ) @definition
)

(
  (comment)? @comment
  (union_specifier
    name: (type_identifier) @name
    body: (field_declaration_list)? @body
  ) @definition
)
