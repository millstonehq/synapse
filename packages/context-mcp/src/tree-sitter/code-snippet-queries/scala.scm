(
  (comment)? @comment
  (class_definition
    name: (identifier) @name
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (object_definition
    name: (identifier) @name
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (trait_definition
    name: (identifier) @name
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (function_definition
    name: (identifier) @name
    parameters: (parameters) @parameters
    body: (_)? @body
  ) @definition
)
