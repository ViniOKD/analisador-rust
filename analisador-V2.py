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
bytecode = collections.defaultdict(str)

class Definer(lark.visitors.Interpreter):
    def __init__(self):
        super().__init__()
        self.functions = collections.ChainMap()

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
        
        
        func_info = {"node": node, "params": params, "local_fn": {}}

  

        self.functions.maps[0][name] = func_info
        
        self.functions.maps.insert(0, func_info["local_fn"])
        self.visit_children(node)
        self.functions.maps.pop(0)

class Walker(lark.visitors.Interpreter):
    def __init__(self, functions):
        super().__init__()
        self.functions = functions


    def block(self, node):
        self.visit_children(node)

    def function(self, node):
        pass

    def call(self, node):
        name = str(node.children[0])
        fn = self.look(name)
        
        if fn and fn.get('type') == 'closure':
            body = fn['value']['body']
            print(f'Chamando closure: {name}()')
            emit(f'sub {name}()')

            return
        if fn is None or fn.get('type') != 'function':
            rich.print(f"[red]error: cannot find function `{name}` in this scope[/red]")
            sys.exit()
        
        fn_info = fn['info']
        
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
        param_names = fn_info["params"]
        
        if len(arg_values) != len(param_names):
            rich.print(f"[red]error: function `{name}` expected {len(param_names)} arguments, found {len(arg_values)}[/red]")
            sys.exit()

        local_scope = {'scope': name, 'type': 'function'}
        
        for param, value in zip(param_names, arg_values):
            local_scope[param] = {'type': 'i32', 'value': value, 'mut': False}
        
        if "local_fn" in fn_info:
            for local_f_name, local_f_info in fn_info["local_fn"].items():
                local_scope[local_f_name] = {'type': 'function', 'info': local_f_info}


        global_scope = symbol_table.maps[-1]

        new_table = collections.ChainMap(local_scope, global_scope)

        old_table = symbol_table.maps
        symbol_table.maps = new_table.maps

        f_node = fn_info["node"]
        for child in f_node.children:
            if isinstance(child, lark.Tree) and child.data == 'block':
                self.visit(child)

        symbol_table.maps = old_table
        emit(f'sub {name}()')

    def attribution(self, node):
        tokens = [x.value for x in node.children if isinstance(x, lark.Token)]
        name, value = tokens[0], tokens[1]
        info = self.look(name)
        if info:
            if info.get('mut'):
                symbol_table[name]['value'] = value
                rich.print(f'[green]att: {name} = {value}[/green]')
                var_scope = symbol_table.maps[0].get('scope', 'global')
                
                emit(f"set {var_scope}():{name} {value}")
            else:
                rich.print(f'[red]error: cannot assign to immutable variable "{name}"[/red]')
                sys.exit()
        else:
            rich.print(f'[red]error: unknown variable {name}[/red]')
            sys.exit()

    def definition_let(self, node):
        tokens = [x.value for x in node.children if isinstance(x, lark.Token)]
        is_mut = 'mut' in tokens
        name = tokens[1] if is_mut else tokens[0]
        closure_node = None

        for child in node.children:
            if isinstance(child, lark.Tree) and child.data == 'closure':
                closure_node = child
                break
        if closure_node:
            value = {'type': 'closure','name': name, 'body': closure_node}
            var_type = 'closure'
            symbol_table.maps[0][name] = {
                'type': 'closure',
                'body': closure_node
            }

            self.compile_closure(name, closure_node)
        else:
            raw_value = tokens[-1]
            ref = self.look(raw_value)
            if ref is not None and 'value' in ref and not raw_value.isdigit():
                value = ref['value']
            else:
                value = raw_value

            var_type = 'i32'
            for x in tokens:
                if x in ('i32', 'bool'): var_type = x

        if name in symbol_table and name not in symbol_table.maps[0]:
            origin = symbol_table[name].get('scope', 'global')
            rich.print(f'[yellow]warning: variable `{name}` shadows an outer variable from scope `{origin}`[/yellow]')

        current_scope = symbol_table.maps[0].get('scope', 'global')
        symbol_table.maps[0][name] = {'type': var_type, 'value': value, 'mut': is_mut, 'scope': current_scope}
        
        if var_type == 'closure':
            rich.print(f'[green]let {"mut " if is_mut else ""}{name} = <closure>[/green]')
        else:
            rich.print(f'[green]let {"mut " if is_mut else ""}{name} = {value}[/green]')
            emit(f"set {current_scope}():{name} {value}")
    def definition_const(self, node):
        tokens = [x.value for x in node.children if isinstance(x, lark.Token)]
        if tokens:
            name, const_type, value = tokens[0], tokens[1], tokens[-1]
            if name in symbol_table.maps[0]:
                rich.print(f'[red]error[E0428]: the name `{name}` is defined multiple times')
                sys.exit()
            current_scope = symbol_table.maps[0].get('scope', 'global')
            symbol_table.maps[0][name] = {'type': const_type, 'value': value, 'const': True, 'scope' : current_scope}
            rich.print(f'[green]const {name}: {const_type} = {value}')
            emit(f"set {current_scope}():{name} {value}")

    def end(self, node):
        pass

    def compile_closure(self, name, closure_node):
        old_scope = symbol_table.maps[0]['scope']

        symbol_table.maps[0]['scope'] = name

        self.visit(closure_node.children[0])

        symbol_table.maps[0]['scope'] = old_scope

    def println(self, node):
        name = str(node.children[-1]) 
        info = self.look(name)
        if info:
            rich.print(f'[blue][Output] {info.get("value")}[/blue]')
            var_scope = info.get('scope', 'global')

            emit(f'out {var_scope}():{name}')
        else:
            rich.print(f'[red]error: cannot find value "{name}" in this scope[/red]')
            sys.exit()

    def look(self, name):
        if name in symbol_table:
            return symbol_table[name]
        return None
    

def emit(instruction):
    bytecode[symbol_table.maps[0]['scope']] += instruction + '\n'


def main():
    parser = lark.Lark(grammar, start='start')
    tree = parser.parse(program)
    rich.print(tree)
    definer = Definer()
    definer.visit(tree)
    rich.print(definer.functions)
    for f_name, f_info in definer.functions.items():
        symbol_table.maps[-1][f_name] = {'type': 'function', 'info': f_info}

    walker = Walker(functions=definer.functions)
    walker.visit(tree)
    
    # procura se na tabela de simbolos tem a funcao main
    # chama o walker diretamente na main
    main_fn= symbol_table.get('main')

    if main_fn and main_fn.get('type') == 'function':
        walker.call(lark.Tree('call', [lark.Token('NAME', 'main')]))
    
    for k,v in bytecode.items():
        print(f'fun {k}\n{v}ret\n')

  

    bytecode_txt = ''.join(f'fun {k}()\n{v}ret\n\n' for k, v in bytecode.items())
    nome_saida = sys.argv[1].split('.')

    nome_saida = nome_saida[0] + '_bytecode' + '.txt'
    with open(nome_saida, 'w') as arq_saida:
        arq_saida.write(bytecode_txt)

    print(f'bytecode salvo em {nome_saida}')

if __name__ == '__main__':
    main()