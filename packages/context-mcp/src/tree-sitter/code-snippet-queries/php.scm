(
  (comment)? @comment
  (function_definition
    name: (name) @name
    parameters: (formal_parameters) @parameters
    return_type: (_)? @return_type
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (method_declaration
    name: (name) @name
    parameters: (formal_parameters) @parameters
    return_type: (_)? @return_type
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (class_declaration
    name: (name) @name
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (interface_declaration
    name: (name) @name
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (trait_declaration
    name: (name) @name
    body: (_) @body
  ) @definition
)
