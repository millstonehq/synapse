(
  (comment)? @comment
  (contract_declaration
    name: (identifier) @name
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (interface_declaration
    name: (identifier) @name
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (library_declaration
    name: (identifier) @name
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (function_definition
    name: (identifier) @name
    parameters: (parameter_list) @parameters
    returns: (_)? @return_type
    body: (_)? @body
  ) @definition
)
