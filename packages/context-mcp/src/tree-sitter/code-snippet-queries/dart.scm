(
  (comment)? @comment
  (class_definition
    name: (identifier) @name
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (mixin_declaration
    name: (identifier) @name
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (function_signature
    name: (identifier) @name
    parameters: (formal_parameter_list) @parameters
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (method_signature
    name: (identifier) @name
    parameters: (formal_parameter_list) @parameters
    body: (_)? @body
  ) @definition
)
