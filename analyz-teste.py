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
            if info['mut']:
                print(f'att: {NAME} = {NUMBER}')
            else:
                rich.print(f'[red]error: cannot assing to immutable variable "{NAME}"[/red]')
        else:
            rich.print(f'[red]error: unknown variable', NAME)


    def definition_let(self, *args):
        is_mut = True if args[0] == 'mut' else False
        name = args[-2]
        value = args[-1]

        if name not in symbol_table.maps[0]:
            symbol_table.maps[0][name] = {'type': 'int', 'mut': is_mut}
            print(f'let {'mut ' if is_mut else ''}{name} = {value}')
        else:
            rich.print('[red]error: redefined variable', NAME)

    def definition_const():
        is_const = True if args[0] == 'const' else False # Checa se a definicao comeca com const
        name = args[-2]
        value = args[-1]

        if name not in symbol_table.maps[0]:
            symbol_table.maps[0][name] = {'type': 'int', 'const': is_const}
            print(f'let {'const ' if is_const else ''}{name} = {value}')
        else:
            rich.print(f'[red]error: the name `{NAME}` is defined multiple times')

    def println(self, arg):
        rich.print(f'[blue]{arg}')

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