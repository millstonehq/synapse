(
  (line_comment)? @comment
  (struct_item
    name: (type_identifier) @name
    body: (_)? @body
  ) @definition
)

(
  (line_comment)? @comment
  (enum_item
    name: (type_identifier) @name
    body: (_)? @body
  ) @definition
)

(
  (line_comment)? @comment
  (function_item
    name: (identifier) @name
    parameters: (parameters) @parameters
    return_type: (_)? @return_type
    body: (_) @body
  ) @definition
)

(
  (line_comment)? @comment
  (impl_item
    trait: (type_identifier)? @trait
    type: (type_identifier) @name
    body: (declaration_list) @body
  ) @definition
)

(
  (line_comment)? @comment
  (trait_item
    name: (type_identifier) @name
    body: (_) @body
  ) @definition
)
