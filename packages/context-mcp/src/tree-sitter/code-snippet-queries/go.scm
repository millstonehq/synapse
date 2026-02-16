(
  (comment)? @comment
  (function_declaration
    name: (identifier) @name
    parameters: (parameter_list) @parameters
    result: (_)? @return_type
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (method_declaration
    receiver: (parameter_list) @receiver
    name: (field_identifier) @name
    parameters: (parameter_list) @parameters
    result: (_)? @return_type
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (type_spec
    name: (type_identifier) @name
    type: (_) @type_def
  ) @definition
)
