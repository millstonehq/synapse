(
  (comment)? @comment
  (class_declaration
    name: (_) @name
    body: (class_body) @body
  ) @definition
)

(
  (comment)? @comment
  (function_declaration
    name: (_) @name
    parameters: (_) @parameters
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (method_definition
    name: (_) @name
    parameters: (_) @parameters
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (interface_declaration
    name: (_) @name
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (type_alias_declaration
    name: (_) @name
    value: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (lexical_declaration
    (variable_declarator
      name: (_) @name
      value: (arrow_function
        parameters: (_) @parameters
        body: (_) @body
      )
    )
  ) @definition
)
