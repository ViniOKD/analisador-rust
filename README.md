# analisador-rust

# Objetivos 
O projeto implementa um analisador léxico, sintático e semântico para um subconjunto da sintaxe na linguagem Rust, utilizando Python e a biblioteca Lark

O analisador suporta:
- 

# Estrutura do analisador
Código fonte
   ↓
Lexer/Parser (Lark)
   ↓
AST
   ↓
Walker
   ↓
Análise semântica

# Funcionalidades implementadas
- análise léxica
- análise sintática
- geração de AST
- definição de funções
- chamadas de funções
- variáveis mutáveis e imutáveis
- constantes
- verificação semântica de escopo
- verificação de variáveis desconhecidas
- verificação de mutabilidade

# Execução
Para executar: 
```bash
python analisador-v1.py testeX.txt
```

