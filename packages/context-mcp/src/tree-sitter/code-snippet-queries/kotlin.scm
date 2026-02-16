(
  (comment)? @comment
  (class_declaration
    (type_identifier) @name
    body: (class_body)? @body
  ) @definition
)

(
  (comment)? @comment
  (object_declaration
    (type_identifier) @name
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (function_declaration
    (simple_identifier) @name
    (function_value_parameters) @parameters
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (interface_declaration
    (type_identifier) @name
    body: (_)? @body
  ) @definition
)
