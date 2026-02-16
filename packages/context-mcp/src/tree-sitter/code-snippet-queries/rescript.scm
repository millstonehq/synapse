(
  (comment)? @comment
  (let_binding
    pattern: (value_identifier) @name
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (type_declaration
    (type_identifier) @name
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (module_declaration
    name: (module_identifier) @name
    body: (_)? @body
  ) @definition
)
