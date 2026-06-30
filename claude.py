"""
interpretador.py
----------------
Interpretador (máquina virtual de pilha de ativação) para o bytecode gerado
pelo analisador-V2.py, conforme a especificação do 2º trabalho de
Linguagens de Programação (UEM).

Instruções de bytecode suportadas:

    fun <nome>              abre o corpo da função <nome>
    ret                     fecha o corpo de função / retorna ao chamador
    set <escopo>:<var> <v>  atribui a constante inteira <v> (ou o valor já
                             resolvido de outra variável <v> do mesmo
                             <escopo>) à variável <var> do frame de <escopo>
    sub <nome>()            chama a função <nome>: empilha um novo frame de
                             ativação, executa o corpo de <nome> por
                             completo e desempilha o frame ao final
    out <escopo>:<var>      imprime na saída padrão o valor atual de <var>
                             no frame de <escopo>

Uso:
    python3 interpretador.py bytecode.txt
    python3 analisador-V2.py programa.txt | python3 interpretador.py

Quando nenhum arquivo é passado por argumento, o bytecode é lido da entrada
padrão (stdin) — o que permite encadear diretamente a saída do analisador
(linhas de depuração fora de blocos "fun ... ret" são simplesmente
ignoradas; veja `ler_bytecode`).
"""

import collections
import re
import sys


class ErroBytecode(Exception):
    """Erro estático: o texto do bytecode está malformado."""


class ErroExecucao(Exception):
    """Erro em tempo de execução: função ou variável não encontrada, etc."""


Instrucao = collections.namedtuple("Instrucao", "op args linha numero")


# ---------------------------------------------------------------------------
# 1) Leitura do bytecode para uma estrutura de dados auxiliar
# ---------------------------------------------------------------------------

_RE_NOME = r"\w+"


def _remove_parenteses(nome):
    nome = nome.strip()
    if nome.endswith("()"):
        nome = nome[:-2]
    return nome.strip("()")


def ler_bytecode(texto):
    """
    Lê o texto do bytecode e devolve um dict {nome_da_funcao: [Instrucao, ...]}

    Cada função é delimitada por uma linha 'fun <nome>' e uma linha 'ret'.
    Linhas fora de um bloco 'fun ... ret' são ignoradas (permite ler
    diretamente a saída "bruta" do analisador, que mistura mensagens de
    depuração com o bytecode).
    """
    funcoes = {}
    nome_atual = None
    corpo_atual = []

    for numero, linha_bruta in enumerate(texto.splitlines(), start=1):
        linha = linha_bruta.strip()
        if not linha:
            continue

        partes = linha.split()
        op = partes[0]

        if op == "fun":
            if len(partes) < 2:
                raise ErroBytecode(f"linha {numero}: 'fun' sem nome de função: {linha!r}")
            nome = _remove_parenteses(partes[1])
            if not re.fullmatch(_RE_NOME, nome):
                raise ErroBytecode(f"linha {numero}: nome de função inválido: {nome!r}")
            if nome_atual is not None:
                raise ErroBytecode(
                    f"linha {numero}: 'fun {nome}' aberta dentro do corpo de "
                    f"'{nome_atual}' (falta 'ret' antes)"
                )
            if nome in funcoes:
                raise ErroBytecode(f"linha {numero}: função '{nome}' já foi definida")
            nome_atual = nome
            corpo_atual = []

        elif op == "ret":
            if nome_atual is None:
                # 'ret' fora de qualquer bloco: ignora como ruído de depuração
                continue
            funcoes[nome_atual] = corpo_atual
            nome_atual = None
            corpo_atual = []

        else:
            if nome_atual is None:
                # instrução fora de qualquer bloco 'fun ... ret': ignora
                continue
            corpo_atual.append(_parse_instrucao(op, partes, linha, numero))

    if nome_atual is not None:
        raise ErroBytecode(f"função '{nome_atual}' não foi fechada com 'ret'")

    return funcoes


def _parse_instrucao(op, partes, linha, numero):
    if op == "set":
        # set <escopo>:<var> <valor>
        if len(partes) != 3 or ":" not in partes[1]:
            raise ErroBytecode(f"linha {numero}: instrução 'set' malformada: {linha!r}")
        escopo, var = partes[1].split(":", 1)
        valor = partes[2]
        return Instrucao("set", (_remove_parenteses(escopo), var, valor), linha, numero)

    if op == "sub":
        # sub <nome>()
        if len(partes) != 2:
            raise ErroBytecode(f"linha {numero}: instrução 'sub' malformada: {linha!r}")
        destino = _remove_parenteses(partes[1])
        return Instrucao("sub", (destino,), linha, numero)

    if op == "out":
        # out <escopo>:<var>
        if len(partes) != 2 or ":" not in partes[1]:
            raise ErroBytecode(f"linha {numero}: instrução 'out' malformada: {linha!r}")
        escopo, var = partes[1].split(":", 1)
        return Instrucao("out", (_remove_parenteses(escopo), var), linha, numero)

    raise ErroBytecode(f"linha {numero}: instrução desconhecida: {linha!r}")


# ---------------------------------------------------------------------------
# 2) Frame de ativação e 3) Máquina de execução
# ---------------------------------------------------------------------------

class Frame:
    """Frame de ativação: variáveis locais de uma chamada de função em curso."""

    __slots__ = ("escopo", "variaveis")

    def __init__(self, escopo):
        self.escopo = escopo
        self.variaveis = {}


class ContextoDeExecucao:
    """Um quadro na pilha de chamadas EXPLÍCITA do interpretador: aponta
    para a lista de instruções da função em curso, a posição atual nela
    (o 'contador de programa') e o frame de ativação correspondente."""

    __slots__ = ("nome", "instrucoes", "pc", "frame")

    def __init__(self, nome, instrucoes, frame):
        self.nome = nome
        self.instrucoes = instrucoes
        self.pc = 0
        self.frame = frame


class Interpretador:

    PROFUNDIDADE_MAXIMA = 10_000

    def __init__(self, funcoes):
        self.funcoes = funcoes
        # frames ativos por nome de escopo (pilha por nome, suporta
        # chamadas recursivas: cada chamada empilha seu próprio frame)
        self._frames_por_escopo = collections.defaultdict(list)

    # -- mapeamento dos pontos de entrada já é o próprio dict self.funcoes --

    def executar(self, ponto_de_entrada="global"):
        if ponto_de_entrada not in self.funcoes:
            raise ErroExecucao(
                f"bytecode não contém a função de entrada '{ponto_de_entrada}'"
            )

        pilha = []  # pilha de chamadas explícita (não usa recursão do Python)
        self._empilhar(pilha, ponto_de_entrada)

        while pilha:
            contexto = pilha[-1]

            if contexto.pc >= len(contexto.instrucoes):
                # fim do corpo da função ('ret' implícito ao acabar a lista)
                self._frames_por_escopo[contexto.nome].pop()
                pilha.pop()
                continue

            instr = contexto.instrucoes[contexto.pc]
            contexto.pc += 1

            if instr.op == "sub":
                (destino,) = instr.args
                self._empilhar(pilha, destino)
            else:
                self._executar_instrucao(instr)

    def _empilhar(self, pilha, nome):
        if nome not in self.funcoes:
            chamadores = " -> ".join(c.nome for c in pilha) or "<vazia>"
            raise ErroExecucao(
                f"chamada para função desconhecida '{nome}()' "
                f"(pilha de chamadas: {chamadores})"
            )
        if len(pilha) >= self.PROFUNDIDADE_MAXIMA:
            raise ErroExecucao(
                "profundidade máxima de chamadas excedida "
                "(possível recursão infinita)"
            )
        frame = Frame(nome)
        self._frames_por_escopo[nome].append(frame)
        pilha.append(ContextoDeExecucao(nome, self.funcoes[nome], frame))

    def _frame_ativo(self, escopo, instr):
        pilha = self._frames_por_escopo.get(escopo)
        if not pilha:
            raise ErroExecucao(
                f"linha {instr.numero}: escopo '{escopo}' não está ativo em "
                f"tempo de execução ({instr.linha!r})"
            )
        return pilha[-1]

    def _resolver(self, token, escopo, instr):
        if re.fullmatch(r"-?\d+", token):
            return int(token)
        frame = self._frame_ativo(escopo, instr)
        if token in frame.variaveis:
            return frame.variaveis[token]
        raise ErroExecucao(
            f"linha {instr.numero}: variável '{token}' não encontrada em "
            f"tempo de execução no escopo '{escopo}' ({instr.linha!r})"
        )

    def _executar_instrucao(self, instr):
        if instr.op == "set":
            escopo, var, token_valor = instr.args
            valor = self._resolver(token_valor, escopo, instr)
            frame = self._frame_ativo(escopo, instr)
            frame.variaveis[var] = valor

        elif instr.op == "out":
            escopo, var = instr.args
            frame = self._frame_ativo(escopo, instr)
            if var not in frame.variaveis:
                raise ErroExecucao(
                    f"linha {instr.numero}: variável '{var}' não encontrada "
                    f"em tempo de execução no escopo '{escopo}' ({instr.linha!r})"
                )
            print(frame.variaveis[var])

        else:  # pragma: no cover - 'sub' é tratado no laço principal; outros já são filtrados em _parse_instrucao
            raise ErroExecucao(f"instrução desconhecida em tempo de execução: {instr}")


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as f:
            texto = f.read()
    else:
        texto = sys.stdin.read()

    try:
        funcoes = ler_bytecode(texto)
    except ErroBytecode as e:
        print(f"erro de bytecode: {e}", file=sys.stderr)
        sys.exit(1)

    interpretador = Interpretador(funcoes)
    try:
        interpretador.executar("global")
    except ErroExecucao as e:
        print(f"erro em tempo de execução: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()