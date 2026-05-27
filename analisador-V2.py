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


class Definer(lark.visitors.Interpreter):
    def __init__(self):
        super().__init__()
        self.functions = {}

    def function(self, node):
        name = str(node.children[0])
        if name in self.functions:
            rich.print(f'[red]error[E0428]: the name `{name}` is defined multiple times')
            sys.exit()

        params = []
        for child in node.children:
            if isinstance(child, lark.Tree) and child.data == 'parameters':
                for param_node in child.children:
                    params.append(str(param_node.children[0]))
        
        
        self.functions[name] = {"node": node, "params": params}
        print('TESTE: DEFININDO FUNCAO', name, f"com parâmetros {params}")



class Walker(lark.visitors.Interpreter):
    def __init__(self, functions):
        super().__init__()
        self.functions = functions

    def function(self, node):
        pass

    def block(self, node):
        self.visit_children(node)

    def call(self, node):
        name = str(node.children[0])
        
        if name not in self.functions:
            rich.print(f"[red]error: cannot find function `{name}` in this scope[/red]")
            sys.exit()
            return
        
        print(f'Chamando função: {name}()')
        
        arg_values = []
        for child in node.children:
            if isinstance(child, lark.Tree) and child.data == 'arguments':
                for arg in child.children:
                    val = str(arg.children[0]) if isinstance(arg, lark.Tree) else str(arg)
                    info = self.look(val)
                    if info:
                        arg_values.append(info.get('value'))
                    else:
                        arg_values.append(val)

        func_info = self.functions[name]
        param_names = func_info["params"]
        
        if len(arg_values) != len(param_names):
            rich.print(f"[red]error: function `{name}` expected {len(param_names)} arguments, found {len(arg_values)}[/red]")
            return

        local_scope = {'scope': name, 'type': 'function'}
        
        for param, value in zip(param_names, arg_values):
            local_scope[param] = {'type': 'i32', 'value': value, 'mut': False}
        
        symbol_table.maps.insert(0, local_scope)
        
        f_node = func_info["node"]
        for child in f_node.children:
            if isinstance(child, lark.Tree) and child.data == 'block':
                self.visit(child) 
        
        symbol_table.maps.pop(0)

    def attribution(self, node):
        tokens = [x.value for x in node.children if isinstance(x, lark.Token)]
        name, value = tokens[0], tokens[1]
        info = self.look(name)
        if info:
            if info.get('mut'):
                symbol_table[name]['value'] = value
                rich.print(f'[green]att: {name} = {value}[/green]')
            else:
                rich.print(f'[red]error: cannot assign to immutable variable "{name}"[/red]')
        else:
            rich.print(f'[red]error: unknown variable {name}[/red]')

    def definition_let(self, node):
        tokens = [x.value for x in node.children if isinstance(x, lark.Token)]
        is_mut = 'mut' in tokens
        name = tokens[1] if is_mut else tokens[0]
        value = tokens[-1]
        
        var_type = 'i32'
        for x in tokens:
            if x in ('i32', 'bool'): var_type = x

        symbol_table.maps[0][name] = {'type': var_type, 'value': value, 'mut': is_mut}
        rich.print(f'[green]let {"mut " if is_mut else ""}{name} = {value}[/green]')

    def definition_const(self, node):
        tokens = [x.value for x in node.children if isinstance(x, lark.Token)]
        if tokens:
            name, const_type, value = tokens[0], tokens[1], tokens[-1]
            if name not in symbol_table:
                symbol_table.maps[0][name] = {'type': const_type, 'value': value, 'const': True}
                rich.print(f'[green]const {name}: {const_type} = {value}')

    def end(self, node):
        pass
    
    def println(self, node):
        
        name = str(node.children[-1]) 
        info = self.look(name)
        if info:
            rich.print(f'[blue][Output] {info.get("value")}[/blue]')
        else:
            rich.print(f'[red]error: cannot find value "{name}" in this scope[/red]')

    def look(self, name):
        if name in symbol_table:
            return symbol_table[name]
        return None
    

def main():
    parser = lark.Lark(grammar, start='start')
    tree = parser.parse(program)
    rich.print(tree)
    definer = Definer()
    definer.visit(tree)
    
    walker = Walker(functions=definer.functions)
    walker.visit(tree)
    if 'main' in definer.functions:
        walker.call(lark.Tree('call', [lark.Token('NAME', 'main')]))

if __name__ == '__main__':
    main()