(
  (comment)? @comment
  (function_definition
    declarator: (function_declarator
      declarator: (_) @name
      parameters: (parameter_list) @parameters
    )
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (class_specifier
    name: (type_identifier) @name
    body: (field_declaration_list)? @body
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
  (namespace_definition
    name: (identifier) @name
    body: (_) @body
  ) @definition
)
