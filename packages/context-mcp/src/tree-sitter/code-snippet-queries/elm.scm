(
  (line_comment)? @comment
  (value_declaration
    (function_declaration_left
      (lower_case_identifier) @name
    )
    body: (_) @body
  ) @definition
)

(
  (line_comment)? @comment
  (type_declaration
    (upper_case_identifier) @name
    body: (_) @body
  ) @definition
)
