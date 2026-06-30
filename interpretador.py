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
                raise f"Função {nome} já definida"
            corpo_funcao = []
        elif operacao == "ret":
            if nome_funcao is None:
                continue # n sei oq tem q acontecer nesse caso
            funcoes[nome_funcao] = corpo_funcao # atribui todo o corpo da funcao no nome da funcao 
            nome_funcao = None # reseta o nome
            corpo_funcao = [] # reseta o corpo
        else:
            if nome_funcao is None:
                continue 
            corpo_funcao.append(ler_instrucoes(operacao, partes, linha, i))
            #print(corpo_funcao)

    if nome_funcao is not None:
        raise f"funcao {nome_funcao} nao foi fechada com ret"
    return funcoes

def ler_instrucoes(operacao, partes, linha, indice):
    if operacao == "set":
        escopo, variavel = partes[1].split(":", 1)

        valor = partes[2]
        return(operacao, (escopo, variavel, valor), linha, indice)
    elif operacao == "sub":
        funcao = partes[1].strip("()")
        return(operacao, funcao, linha, indice)
    elif operacao == "out":
        escopo, variavel = partes[1].split(":", 1)
        return (operacao, (escopo, variavel), linha, indice)
    else:
        raise f"erro: {operacao} desconhecida"


def main():
    if len(sys.argv) < 2:
        print("usage: program.py inst_bytecode.txt")
        sys.exit()

    with open(sys.argv[1], 'r') as arq:
        texto = arq.read().splitlines()
    
    funcoes = {}
    print(texto)
    funcoes = ler_bytecode(texto)
    print(funcoes)
    


if __name__ == "__main__":
    main()