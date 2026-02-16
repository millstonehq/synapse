(
  (comment)? @comment
  (function_declaration
    name: (simple_identifier) @name
    parameters: (parameter_clause) @parameters
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (class_declaration
    name: (type_identifier) @name
    body: (class_body)? @body
  ) @definition
)

(
  (comment)? @comment
  (struct_declaration
    name: (type_identifier) @name
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (protocol_declaration
    name: (type_identifier) @name
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (enum_declaration
    name: (type_identifier) @name
    body: (_)? @body
  ) @definition
)
