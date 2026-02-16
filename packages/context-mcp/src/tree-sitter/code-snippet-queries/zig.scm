(
  (LINECOMMENT)? @comment
  (FnProto
    (IDENTIFIER) @name
    (ParamDeclList) @parameters
    body: (_)? @body
  ) @definition
)

(
  (LINECOMMENT)? @comment
  (VarDecl
    (IDENTIFIER) @name
    value: (ContainerDecl) @body
  ) @definition
)
