(
  (comment)? @comment
  (value_definition
    (let_binding
      pattern: (value_name) @name
      body: (_) @body
    )
  ) @definition
)

(
  (comment)? @comment
  (type_definition
    (type_binding
      name: (type_constructor) @name
      body: (_) @body
    )
  ) @definition
)

(
  (comment)? @comment
  (module_definition
    name: (module_name) @name
    body: (_)? @body
  ) @definition
)
