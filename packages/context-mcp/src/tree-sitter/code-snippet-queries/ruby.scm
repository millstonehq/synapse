(
  (comment)? @comment
  (method
    name: (_) @name
    parameters: (method_parameters)? @parameters
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (singleton_method
    name: (_) @name
    parameters: (method_parameters)? @parameters
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (class
    name: (constant) @name
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (module
    name: (constant) @name
    body: (_)? @body
  ) @definition
)
