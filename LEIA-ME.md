# Controle de estoque

O programa cadastra produtos, registra entradas e saídas e mostra os itens com estoque baixo.

## Abrir no Windows

Extraia o ZIP inteiro. Abra o terminal na pasta dos arquivos e execute:

```powershell
py desktop.py
```

Os arquivos desktop.py e estoque_core.py precisam estar na mesma pasta. O desktop usa Tkinter, normalmente incluído na instalação do Python para Windows. Se aparecer erro de módulo tkinter ausente, modifique a instalação do Python para incluir Tcl/Tk. Não é necessário instalar Flask para usar o desktop.

Para usar a versão web:

```powershell
py -m pip install -r requirements.txt
py app.py
```

Depois, abra http://127.0.0.1:5000 no navegador. Para encerrar o servidor, pressione Ctrl+C no terminal.

## Arquivos

- estoque_core.py: cadastro, validação, busca, movimentação e leitura/gravação dos produtos.
- desktop.py: janela feita com Tkinter.
- app.py: página e rotas da versão Flask.
- requirements.txt: dependência da versão web.
- test_estoque.py: testes das funções e rotas.
- ANALISE.md: problemas encontrados, correções e limitações.

O estoque.json é criado na primeira gravação, na mesma pasta do código. Se você já tem esse arquivo, faça uma cópia de segurança e mantenha-o junto dos arquivos corrigidos. Nenhum estoque de exemplo está incluído para evitar substituir seus produtos.

Use uma versão de cada vez. Desktop e web usam o mesmo arquivo e não sincronizam alterações simultâneas. A pasta precisa permitir gravação.

## Uso

Preencha nome, categoria, quantidade, preço e estoque mínimo e clique em Adicionar. A categoria vazia vira Geral. Para editar ou excluir no desktop, selecione a linha na tabela. Entrada aumenta a quantidade; saída diminui. O programa impede saída maior que o saldo disponível. Quantidade zero fica Esgotado; quantidade até o mínimo fica Baixo.

Digite preços como 19,90 ou 19.90, sem símbolo de moeda ou separador de milhar.

## Conferir os testes

Com Flask instalado:

```powershell
py -m unittest -v
```
