(
  (unary_operator
    operator: "@"
    operand: (call) @comment
  )?
  (call
    target: (identifier) @_def
    (arguments
      (alias) @name
    )
    (do_block)? @body
  ) @definition
  (#match? @_def "^(defmodule|defprotocol)$")
)

(
  (unary_operator
    operator: "@"
    operand: (call) @comment
  )?
  (call
    target: (identifier) @_def
    (arguments
      (call
        target: (identifier) @name
        (arguments) @parameters
      )
    )
    (do_block)? @body
  ) @definition
  (#match? @_def "^(def|defp|defmacro|defmacrop)$")
)
