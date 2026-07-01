import sys

def ler_bytecode(linhas):
    funcoes = {}
    nome_funcao = None
    corpo_funcao = []

    for i in range(len(linhas)):
        linha = linhas[i].strip()
        partes = linha.split()
        if not linha:
            continue
        operacao = partes[0]
        
        if operacao == "fun":
            nome_funcao = partes[1].strip("()")
            
            if nome_funcao in funcoes:
                raise Exception(f"error: the name `{nome_funcao}` is defined multiple times")
            corpo_funcao = []
        elif operacao == "ret":
            if nome_funcao is None:
                continue 
            funcoes[nome_funcao] = corpo_funcao # atribui todo o corpo da funcao no nome da funcao 
            nome_funcao = None # reseta o nome
            corpo_funcao = [] # reseta o corpo
        else:
            if nome_funcao is None:
                continue 
            corpo_funcao.append(ler_instrucoes(operacao, partes, linha, i))

    if nome_funcao is not None:
        raise Exception(f"error: funcao {nome_funcao} nao foi fechada com ret")
    return funcoes

def ler_instrucoes(operacao, partes, linha, indice):
    if operacao == "set":
        escopo, variavel = partes[1].split(":", 1)
        escopo = escopo.strip("()")
        valor = partes[2]
        return(operacao, (escopo, variavel, valor), linha, indice)
    elif operacao == "sub":
        funcao = partes[1].strip("()")
        return(operacao, funcao, linha, indice)
    elif operacao == "out":
        escopo, variavel = partes[1].split(":", 1)
        escopo = escopo.strip("()")
        return (operacao, (escopo, variavel), linha, indice)
    else:
        raise Exception(f"error: {operacao} desconhecida")

def executar_bytecode(funcoes, ponto_entrada = "global"):
    if ponto_entrada not in funcoes:
        raise Exception(f"bytecode não contém a função de entrada '{ponto_entrada}'")
    
    pilha_chamadas = [
        {
            "funcao": ponto_entrada,
            "pc": 0,
            "variaveis": {}
        }
    ]
    while len(pilha_chamadas) > 0:
        contexto = pilha_chamadas[-1]
        funcao = contexto["funcao"]
        pc = contexto["pc"]
        variaveis = contexto["variaveis"]

        if pc >= len(funcoes[funcao]):
            pilha_chamadas.pop()
            continue

        instrucao, args, linha, indice = funcoes[funcao][pc]
        contexto["pc"] += 1

        if instrucao == "set":
            escopo, variavel, valor = args
            encontrou = False

            for frame in reversed(pilha_chamadas):
                if frame["funcao"] == escopo:
                    frame["variaveis"][variavel] = valor
                    encontrou = True
                    break

            if not encontrou:
                raise Exception(f"error: scope {escopo} not found")
            
        elif instrucao == "sub":
            nova_funcao = args
            if nova_funcao not in funcoes:
                raise Exception(f"error: function {nova_funcao} not found")
            pilha_chamadas.append({
                "funcao": nova_funcao,
                "pc": 0,
                "variaveis": {}
            })
        elif instrucao == "out":
            escopo, variavel = args
            encontrou = False

            for frame in reversed(pilha_chamadas):
                if frame["funcao"] == escopo:
                    if variavel in frame["variaveis"]:
                        print(frame["variaveis"][variavel])
                        encontrou = True
                        break

            if not encontrou:
                raise Exception(f"error: cannot find value {variavel} in scope {escopo}")
        else:
            raise Exception(f"error: instrucao {instrucao} desconhecida")
            
def main():
    if len(sys.argv) < 2:
        print("usage: program.py inst_bytecode.txt")
        sys.exit()

    with open(sys.argv[1], 'r') as arq:
        texto = arq.read().splitlines()

    funcoes = ler_bytecode(texto)

    executar_bytecode(funcoes, ponto_entrada="global")


if __name__ == "__main__":
    main()