"""Runtime observation. Three hooks and a context variable.

A data hook, which every ORM has. A request hook, which every web framework has.
And a context variable correlating them -- which is the part that turns two
independent streams into a BINDING rather than two coverage numbers.

What leaves the process is route templates, table names and SQL verbs. No
parameters, no rows, no values. That is not a nicety: it is what makes this
something a third party will agree to run against a system you do not own,
because they can read the whole output file before they send it back.
"""
