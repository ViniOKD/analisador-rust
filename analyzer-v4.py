import collections
import lark
import rich

# version 4 [nested functions]
grammar = r"""
program:     definition* function* call*
function:    NAME "{" statement* "}" end
end:
?statement:  definition | attribution | function | call
definition:  "var" NAME
attribution: NAME "=" NUMBER
call:        NAME "()"

NAME:   /\w+/
NUMBER: /\d+/
%ignore /[ \t\n\r]+/
"""

program = """
var a
f {
  var c
  g {
     var e
     c = 1
  }
  g()
}
f()
"""

parser = lark.Lark(grammar, start='program')
tree = parser.parse(program)
rich.print(tree)
symbol_table = collections.ChainMap({'scope': 'global'})

class Walker:
  def function(self, NAME):
    symbol_table.maps.insert(0, {'scope': NAME+'()'})

  def end(self):
    rich.print(symbol_table)
    symbol_table.maps.pop(0)

  def definition(self, NAME):
    if NAME not in symbol_table.maps[0]:
      symbol_table[NAME] = 'int'
      print('def:', NAME)
    else:
      rich.print('[red]error: redefined variable', NAME)

  def attribution(self, NAME, NUMBER):
    if NAME in symbol_table:
      print('att:', NAME, NUMBER)
    else:
      rich.print('[red]error: unknown variable', NAME)

  def visit(self, node):
    vals = [t.value for t in node.children if type(t) is lark.Token]
    if hasattr(self, node.data):
        getattr(self, node.data)(*vals)
    for child in node.children:
      if type(child) is lark.Tree:
        self.visit(child)

Walker().visit(tree)
rich.print(symbol_table)
