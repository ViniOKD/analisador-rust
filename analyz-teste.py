import collections
import sys
import lark
import rich

with open("rust-analyzer.lark", 'r') as file:
    grammar = file.read()

if len(sys.argv) > 1:
    with open(sys.argv[1], 'r') as f:
        program = f.read()
else:
    print("usage: program.py instructions.txt")
    sys.exit()

symbol_table = collections.ChainMap({'scope': 'global'})

class Walker:
    def function(self, NAME):
        symbol_table.maps.insert(0, {'scope': NAME + '()'})
    
    def end(self):
        rich.print(symbol_table)
        symbol_table.maps.pop(0)
    
    def attribution(self, NAME, NUMBER):
        if NAME in symbol_table:
            info = symbol_table[NAME]
            print(symbol_table)
            if info.get('mut'):
                symbol_table[NAME]['value'] = NUMBER
                print(f'att: {NAME} = {NUMBER}')
            else:
                if info.get('const'):
                    rich.print(f'[red]error: invalid left-hand side of assignment')
                else:
                    rich.print(f'[red]error: cannot assign to immutable variable "{NAME}"[/red]')
        else:
            rich.print(f'[red]error: unknown variable', NAME)

    def definition_let(self, *args):
        # Unpack depending on which optional tokens are present
        mut = None
        name = None
        var_type = None
        value = None

        for arg in args:
            if arg == 'mut':
                mut = arg
            elif str(arg).isdigit():
                value = arg
            elif arg in ('i32', 'f64', 'bool', 'str'):
                var_type = arg
            else:
                name = arg

        is_mut = mut == 'mut'
        if var_type is None:
            var_type = 'i32'

        if name in symbol_table and symbol_table[name].get('const'):
            rich.print('[red]error: refutable pattern in local binding')
        else:
            symbol_table.maps[0][name] = {'type': var_type, 'value': value, 'mut': is_mut}
            print(f'let {"mut " if is_mut else ""}{name} = {value}')

    def definition_const(self, *args):
        name = args[0]
        const_type = args[1]
        value = args[2]
        
        if name not in symbol_table.maps[0]:
            symbol_table.maps[0][name] = {'type': 'int','value': value, 'const': True}
            print(f'const {name} :{const_type} = {value}')
        else:
            rich.print(f'[red]error: the name `{name}` is defined multiple times')


    def println(self, arg):
        if arg in symbol_table:
            rich.print(f'[blue]{symbol_table[arg].get('value')}')
        else:
            rich.print(f'[red]error: cannot find value "{arg}" in this scope')

    def visit(self, node):
        ''' Implementa um padrão de Recursive Tree traversal (Percorrimento transversal de árvore) com Dispatch Dinâmico
        '''
        vals = [x.value for x in node.children if type(x) is lark.Token]
        if hasattr(self, node.data):        # Le o nome da regra da gramatica e verifica se o Walker possui um metodo de mesmo nome
            getattr(self, node.data)(*vals) # Se tiver, ele chama o metodo passando os valores coletados como argumento
        for child in node.children: # Olha para todos os filhos do nó atual recursivamente
            if type(child) is lark.Tree:
                self.visit(child)

def main():
    parser = lark.Lark(grammar, start='start')
    tree = parser.parse(program)
    rich.print(tree)
    Walker().visit(tree)

if __name__ == "__main__":
    main()