import collections
import lark
import rich

# version 4 [nested functions]
grammar = r"""
program:     item* 

?item: function

function:    "fn" NAME "()" block

block: "{" statement* "}" 

?statement:  definition | attribution | call


definition: "let" MUT? NAME ":" type? "="  expression ";"
attribution: NAME "=" NUMBER ";"
call:        NAME "()" ";"



?expression: reference | NAME | NUMBER
reference: REF MUT? NAME
?type: REF MUT? BASE_TYPES | BASE_TYPES

BASE_TYPES: "i32" | "f64" | "bool" | "str"
REF:    "&"
MUT:    "mut"
NAME:   /\w+/
NUMBER: /\d+/
%ignore /[ \t\n\r]+/
%ignore /\/\/[^\n]*/
"""

program = """
fn main() {
let a = 20;
a = "ola";

}

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

  def definition(self, *args):
    is_mut = len(args) == 3
    name = args[-2]
    value = args[-1]


    if name not in symbol_table.maps[0]:
      symbol_table.maps[0][name] = {'type': 'int', 'mut': is_mut}
      print(f"let {'mut ' if is_mut else ''}{name} = {value}")
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
