(
  (comment)? @comment
  (class_declaration
    name: (identifier) @name
    body: (class_body) @body
  ) @definition
)

(
  (comment)? @comment
  (interface_declaration
    name: (identifier) @name
    body: (interface_body) @body
  ) @definition
)

(
  (comment)? @comment
  (method_declaration
    name: (identifier) @name
    parameters: (formal_parameters) @parameters
    type: (_)? @return_type
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (constructor_declaration
    name: (identifier) @name
    parameters: (formal_parameters) @parameters
    body: (_) @body
  ) @definition
)
