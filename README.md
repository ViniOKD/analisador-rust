# Analisador Simplificado de Rust

## Descrição

Este projeto consiste na implementação de um analisador sintático e semântico simplificado para a linguagem Rust utilizando Python e a biblioteca Lark. O analisador é capaz de reconhecer construções básicas da linguagem, gerar uma árvore sintática (AST), manter uma tabela de símbolos e realizar algumas verificações semânticas durante a execução.

## Tecnologias Utilizadas

* Python 3
* Lark
* Rich
* Collections (ChainMap)

## Funcionalidades Implementadas

### Funções

O analisador reconhece declarações e chamadas de funções.

Exemplo:

```rust
fn foo() {
}

fn main() {
    foo();
}
```

Também há suporte para funções declaradas dentro de outras funções.

### Variáveis

Suporte a:

```rust
let x = 10;
let mut y = 20;
```

Além da declaração com tipo explícito:

```rust
let x: i32 = 10;
```

### Constantes

Suporte a declarações constantes:

```rust
const A: i32 = 10;
```

O analisador detecta redefinições de constantes no mesmo escopo.

### Atribuições

Apenas variáveis declaradas com `mut` podem receber novos valores.

Exemplo:

```rust
let mut x = 10;
x = 20;
```

### Closures

Foi implementado suporte simplificado para closures sem parâmetros.

Exemplo:

```rust
let inner = || {
    println("{}", x);
};

inner();
```

As closures conseguem acessar variáveis do escopo onde foram definidas.

### Impressão

Suporte ao comando:

```rust
println("{}", x);
```

## Tabela de Símbolos

A tabela de símbolos foi implementada utilizando `ChainMap`, permitindo representar escopos aninhados de maneira simples.

Nela são armazenadas:

* Variáveis
* Constantes
* Funções
* Closures

## Verificações Semânticas

O analisador realiza algumas verificações básicas:

* Funções duplicadas
* Constantes duplicadas
* Uso de funções inexistentes
* Uso de variáveis inexistentes
* Atribuição em variáveis imutáveis
* Shadowing de variáveis

## Considerações Finais

O desenvolvimento deste projeto permitiu aplicar conceitos de análise sintática, análise semântica, gerenciamento de escopos e construção de interpretadores, utilizando uma versão simplificada da linguagem Rust como estudo de caso.
