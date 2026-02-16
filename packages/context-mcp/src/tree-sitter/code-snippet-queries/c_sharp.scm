(
  (comment)? @comment
  (class_declaration
    name: (identifier) @name
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (interface_declaration
    name: (identifier) @name
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (struct_declaration
    name: (identifier) @name
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (method_declaration
    name: (identifier) @name
    parameters: (parameter_list) @parameters
    type: (_)? @return_type
    body: (_)? @body
  ) @definition
)

(
  (comment)? @comment
  (constructor_declaration
    name: (identifier) @name
    parameters: (parameter_list) @parameters
    body: (_) @body
  ) @definition
)
