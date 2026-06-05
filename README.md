# Analisador Simplificado de Rust

## Como executar

O analisador recebe como entrada um arquivo contendo o código Rust simplificado.

Exemplo de execução:

```bash
python analisador-V2.py testeX.txt
```

## Funcionalidades implementadas

O analisador possui suporte para:

* Declaração de funções
* Chamadas de funções
* Funções aninhadas
* Declaração de variáveis (`let`)
* Variáveis mutáveis (`let mut`)
* Declaração de constantes (`const`)
* Atribuições
* Impressão com `println`
* Closures sem parâmetros
* Escopos aninhados

## Verificações semânticas

O analisador detecta:

* Funções duplicadas
* Constantes duplicadas
* Uso de funções inexistentes
* Uso de variáveis inexistentes
* Tentativa de alterar variáveis imutáveis
* Shadowing de variáveis

## Implementação

A gramática foi desenvolvida utilizando a biblioteca Lark. O gerenciamento de escopos é realizado através da estrutura `ChainMap`, utilizada como tabela de símbolos.

O projeto é dividido em duas etapas principais:

* **Definer**: responsável por registrar funções e seus parâmetros.
* **Walker**: responsável pela execução das verificações semânticas e simulação da execução do programa.
