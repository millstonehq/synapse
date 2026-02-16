(
  (comment)? @comment
  (function_declaration
    name: (_) @name
    parameters: (parameters) @parameters
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (function_definition
    name: (_) @name
    parameters: (parameters) @parameters
    body: (_) @body
  ) @definition
)

(
  (comment)? @comment
  (variable_declaration
    (assignment_statement
      (variable_list
        name: (_) @name
      )
      (expression_list
        value: (function_definition
          parameters: (parameters) @parameters
          body: (_) @body
        )
      )
    )
  ) @definition
)
