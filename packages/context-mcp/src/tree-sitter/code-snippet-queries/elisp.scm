(
  (comment)? @comment
  (list
    .
    (symbol) @_defun
    (symbol) @name
    (_)* @body
  ) @definition
  (#match? @_defun "^(defun|defmacro|defsubst|cl-defun|cl-defmacro)$")
)

(
  (comment)? @comment
  (list
    .
    (symbol) @_defvar
    (symbol) @name
    (_)? @body
  ) @definition
  (#match? @_defvar "^(defvar|defconst|defcustom)$")
)
