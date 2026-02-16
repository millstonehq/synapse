(
  (comment)? @comment
  (class_definition
    name: (identifier) @name
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (function_definition
    name: (identifier) @name
    parameters: (parameters) @parameters
    return_type: (_)? @return_type
    body: (_) @body
  ) @definition
)
