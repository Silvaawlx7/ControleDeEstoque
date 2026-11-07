"""Gestão de Estoque - versão desktop (Tkinter)."""

from copy import deepcopy

import tkinter as tk
from tkinter import messagebox, ttk

import estoque_core as core

LARGURA_LIMITE = 900  # abaixo disso o layout empilha

COR_FUNDO = "#f4f6f8"
COR_CARTAO = "#ffffff"
COR_DESTAQUE = "#2563eb"
COR_ALERTA = "#fef3c7"
COR_ESGOTADO = "#fee2e2"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestão de Estoque")
        self.geometry("1100x680")
        self.minsize(900, 600)
        self.configure(bg=COR_FUNDO)

        try:
            self.produtos = core.carregar_dados()
        except (core.ErroValidacao, OSError) as erro:
            self.withdraw()
            messagebox.showerror("Erro ao abrir estoque", str(erro), parent=self)
            self.destroy()
            raise SystemExit(1)
        self.produtos_salvos = deepcopy(self.produtos)
        self.id_selecionado = None
        self.modo_layout = None

        self.var_nome = tk.StringVar()
        self.var_categoria = tk.StringVar()
        self.var_quantidade = tk.StringVar(value="0")
        self.var_preco = tk.StringVar(value="0,00")
        self.var_minimo = tk.StringVar(value="0")
        self.var_mov = tk.StringVar(value="1")
        self.var_busca = tk.StringVar()
        self.var_alertas = tk.BooleanVar(value=False)
        self.var_status = tk.StringVar(value="Pronto.")

        self._configurar_estilo()
        self._criar_resumo()
        self._criar_area_principal()
        self._criar_barra_status()

        self.var_busca.trace_add("write", lambda *_: self.atualizar_tabela())
        self.bind("<Configure>", self._ao_redimensionar)
        self.protocol("WM_DELETE_WINDOW", self._fechar)
        self.atualizar_tabela()
        self._aplicar_layout(1100)

    # Montagem da janela
    def _configurar_estilo(self):
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure("TFrame", background=COR_FUNDO)
        estilo.configure("Cartao.TFrame", background=COR_CARTAO)
        estilo.configure("TLabel", background=COR_CARTAO, font=("Segoe UI", 10))
        estilo.configure("Fundo.TLabel", background=COR_FUNDO)
        estilo.configure("Titulo.TLabel", background=COR_CARTAO, font=("Segoe UI", 12, "bold"))
        estilo.configure("Valor.TLabel", background=COR_CARTAO, font=("Segoe UI", 18, "bold"),
                         foreground=COR_DESTAQUE)
        estilo.configure("Rotulo.TLabel", background=COR_CARTAO, foreground="#6b7280",
                         font=("Segoe UI", 9))
        estilo.configure("TCheckbutton", background=COR_FUNDO)
        estilo.configure("TButton", font=("Segoe UI", 10), padding=6)
        estilo.configure("Destaque.TButton", background=COR_DESTAQUE, foreground="white")
        estilo.map("Destaque.TButton", background=[("active", "#1d4ed8")])
        estilo.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        estilo.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _criar_resumo(self):
        self.frame_resumo = ttk.Frame(self, padding=(12, 12, 12, 0))
        self.frame_resumo.grid(row=0, column=0, sticky="ew")
        self.rotulos_resumo = {}
        itens = [("produtos", "Produtos"), ("itens", "Itens em estoque"),
                 ("valor_total", "Valor em estoque"), ("alertas", "Em alerta")]
        for coluna, (chave, titulo) in enumerate(itens):
            self.frame_resumo.columnconfigure(coluna, weight=1, uniform="resumo")
            cartao = ttk.Frame(self.frame_resumo, style="Cartao.TFrame", padding=10)
            cartao.grid(row=0, column=coluna, sticky="nsew", padx=4)
            ttk.Label(cartao, text=titulo, style="Rotulo.TLabel").pack(anchor="w")
            rotulo = ttk.Label(cartao, text="0", style="Valor.TLabel")
            rotulo.pack(anchor="w")
            self.rotulos_resumo[chave] = rotulo
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

    def _criar_area_principal(self):
        self.principal = ttk.Frame(self, padding=12)
        self.principal.grid(row=1, column=0, sticky="nsew")

        self.painel_form = ttk.Frame(self.principal, style="Cartao.TFrame", padding=12)
        self._criar_formulario(self.painel_form)

        self.painel_tabela = ttk.Frame(self.principal, style="Cartao.TFrame", padding=12)
        self._criar_tabela(self.painel_tabela)

    def _criar_formulario(self, pai):
        pai.columnconfigure(0, weight=1)
        self.rotulo_form = ttk.Label(pai, text="Novo produto", style="Titulo.TLabel")
        self.rotulo_form.grid(row=0, column=0, sticky="w", pady=(0, 8))

        campos = [("Nome", self.var_nome), ("Categoria", self.var_categoria),
                  ("Quantidade", self.var_quantidade), ("Preço (R$)", self.var_preco),
                  ("Estoque mínimo", self.var_minimo)]
        linha = 1
        self.entradas = {}
        for texto, variavel in campos:
            ttk.Label(pai, text=texto).grid(row=linha, column=0, sticky="w")
            if texto == "Categoria":
                entrada = ttk.Combobox(pai, textvariable=variavel, values=self._categorias())
            else:
                entrada = ttk.Entry(pai, textvariable=variavel)
            entrada.grid(row=linha + 1, column=0, sticky="ew", pady=(0, 6))
            self.entradas[texto] = entrada
            linha += 2

        botoes = ttk.Frame(pai, style="Cartao.TFrame")
        botoes.grid(row=linha, column=0, sticky="ew", pady=(6, 0))
        for c in range(3):
            botoes.columnconfigure(c, weight=1)
        self.botao_salvar = ttk.Button(botoes, text="Adicionar", style="Destaque.TButton",
                                       command=self.salvar)
        self.botao_salvar.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(botoes, text="Limpar", command=self.limpar_formulario).grid(
            row=0, column=1, sticky="ew", padx=4)
        ttk.Button(botoes, text="Excluir", command=self.excluir).grid(
            row=0, column=2, sticky="ew", padx=(4, 0))

        ttk.Separator(pai).grid(row=linha + 1, column=0, sticky="ew", pady=12)
        ttk.Label(pai, text="Movimentar estoque", style="Titulo.TLabel").grid(
            row=linha + 2, column=0, sticky="w")
        mov = ttk.Frame(pai, style="Cartao.TFrame")
        mov.grid(row=linha + 3, column=0, sticky="ew", pady=(6, 0))
        mov.columnconfigure(0, weight=1)
        mov.columnconfigure(1, weight=1)
        mov.columnconfigure(2, weight=1)
        ttk.Entry(mov, textvariable=self.var_mov, width=6).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(mov, text="+ Entrada", command=lambda: self.movimentar("entrada")).grid(
            row=0, column=1, sticky="ew", padx=4)
        ttk.Button(mov, text="− Saída", command=lambda: self.movimentar("saida")).grid(
            row=0, column=2, sticky="ew", padx=(4, 0))

    def _criar_tabela(self, pai):
        pai.columnconfigure(0, weight=1)
        pai.rowconfigure(1, weight=1)

        barra = ttk.Frame(pai, style="Cartao.TFrame")
        barra.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        barra.columnconfigure(1, weight=1)
        ttk.Label(barra, text="Buscar:").grid(row=0, column=0, padx=(0, 6))
        ttk.Entry(barra, textvariable=self.var_busca).grid(row=0, column=1, sticky="ew")
        ttk.Checkbutton(barra, text="Só alertas", variable=self.var_alertas,
                        command=self.atualizar_tabela, style="TCheckbutton").grid(
            row=0, column=2, padx=(8, 0))

        colunas = ("id", "nome", "categoria", "quantidade", "preco", "minimo", "situacao")
        titulos = {"id": "ID", "nome": "Produto", "categoria": "Categoria",
                   "quantidade": "Qtd", "preco": "Preço", "minimo": "Mín.",
                   "situacao": "Situação"}
        larguras = {"id": 40, "nome": 200, "categoria": 110, "quantidade": 60,
                    "preco": 90, "minimo": 55, "situacao": 85}
        self.tabela = ttk.Treeview(pai, columns=colunas, show="headings", selectmode="browse")
        for coluna in colunas:
            self.tabela.heading(coluna, text=titulos[coluna])
            ancora = "w" if coluna in ("nome", "categoria") else "center"
            self.tabela.column(coluna, width=larguras[coluna], anchor=ancora,
                               stretch=(coluna == "nome"), minwidth=40)
        self.tabela.tag_configure("baixo", background=COR_ALERTA)
        self.tabela.tag_configure("esgotado", background=COR_ESGOTADO)
        self.tabela.grid(row=1, column=0, sticky="nsew")

        barra_v = ttk.Scrollbar(pai, orient="vertical", command=self.tabela.yview)
        barra_v.grid(row=1, column=1, sticky="ns")
        barra_h = ttk.Scrollbar(pai, orient="horizontal", command=self.tabela.xview)
        barra_h.grid(row=2, column=0, sticky="ew")
        self.tabela.configure(yscrollcommand=barra_v.set, xscrollcommand=barra_h.set)
        self.tabela.bind("<<TreeviewSelect>>", self._ao_selecionar)

    def _criar_barra_status(self):
        ttk.Label(self, textvariable=self.var_status, style="Fundo.TLabel",
                  anchor="w", padding=(14, 0, 14, 8)).grid(row=2, column=0, sticky="ew")

    # Posição dos painéis
    def _ao_redimensionar(self, evento):
        if evento.widget is self:
            self._aplicar_layout(evento.width)

    def _aplicar_layout(self, largura):
        modo = "largo" if largura >= LARGURA_LIMITE else "estreito"
        if modo == self.modo_layout:
            return
        self.modo_layout = modo
        for c in range(2):
            self.principal.columnconfigure(c, weight=0)
        for r in range(2):
            self.principal.rowconfigure(r, weight=0)
        self.painel_form.grid_forget()
        self.painel_tabela.grid_forget()
        if modo == "largo":
            self.painel_form.grid(row=0, column=0, sticky="ns", padx=(0, 8))
            self.painel_tabela.grid(row=0, column=1, sticky="nsew")
            self.principal.columnconfigure(1, weight=1)
            self.principal.rowconfigure(0, weight=1)
        else:
            self.painel_form.grid(row=0, column=0, sticky="ew", pady=(0, 8))
            self.painel_tabela.grid(row=1, column=0, sticky="nsew")
            self.principal.columnconfigure(0, weight=1)
            self.principal.rowconfigure(1, weight=1)

    # Produtos e tabela
    def _categorias(self):
        return sorted({p["categoria"] for p in self.produtos})

    def atualizar_tabela(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)
        filtrados = core.buscar_produtos(self.produtos, self.var_busca.get(),
                                         self.var_alertas.get())
        for p in filtrados:
            estado = core.situacao(p)
            tag = {"Baixo": "baixo", "Esgotado": "esgotado"}.get(estado, "")
            self.tabela.insert("", "end", iid=str(p["id"]), tags=(tag,), values=(
                p["id"], p["nome"], p["categoria"], p["quantidade"],
                core.formatar_moeda(p["preco"]), p["minimo"], estado))
        resumo = core.calcular_resumo(self.produtos)
        self.rotulos_resumo["produtos"].config(text=str(resumo["produtos"]))
        self.rotulos_resumo["itens"].config(text=str(resumo["itens"]))
        self.rotulos_resumo["valor_total"].config(text=core.formatar_moeda(resumo["valor_total"]))
        self.rotulos_resumo["alertas"].config(text=str(resumo["alertas"]))
        self.entradas["Categoria"].configure(values=self._categorias())
        if self.id_selecionado is not None and self.tabela.exists(str(self.id_selecionado)):
            self.tabela.selection_set(str(self.id_selecionado))

    def _persistir(self):
        try:
            core.salvar_dados(self.produtos)
        except OSError as erro:
            self.produtos = deepcopy(self.produtos_salvos)
            self.atualizar_tabela()
            messagebox.showerror("Erro ao salvar", f"Não foi possível gravar o arquivo:\n{erro}")
            return False
        self.produtos_salvos = deepcopy(self.produtos)
        return True

    # Cadastro, exclusão e movimentação
    def _ao_selecionar(self, _evento):
        selecao = self.tabela.selection()
        if not selecao:
            return
        try:
            p = core.encontrar_produto(self.produtos, selecao[0])
        except core.ErroValidacao:
            return
        self.id_selecionado = p["id"]
        self.var_nome.set(p["nome"])
        self.var_categoria.set(p["categoria"])
        self.var_quantidade.set(str(p["quantidade"]))
        self.var_preco.set(f"{p['preco']:.2f}".replace(".", ","))
        self.var_minimo.set(str(p["minimo"]))
        self.rotulo_form.config(text=f"Editando #{p['id']}")
        self.botao_salvar.config(text="Salvar alterações")

    def limpar_formulario(self):
        self.id_selecionado = None
        self.var_nome.set("")
        self.var_categoria.set("")
        self.var_quantidade.set("0")
        self.var_preco.set("0,00")
        self.var_minimo.set("0")
        self.rotulo_form.config(text="Novo produto")
        self.botao_salvar.config(text="Adicionar")
        self.tabela.selection_remove(self.tabela.selection())

    def salvar(self):
        dados = (self.var_nome.get(), self.var_categoria.get(), self.var_quantidade.get(),
                 self.var_preco.get(), self.var_minimo.get())
        try:
            if self.id_selecionado is None:
                produto = core.adicionar_produto(self.produtos, *dados)
                mensagem = f"Produto '{produto['nome']}' adicionado."
            else:
                produto = core.editar_produto(self.produtos, self.id_selecionado, *dados)
                mensagem = f"Produto '{produto['nome']}' atualizado."
        except core.ErroValidacao as erro:
            messagebox.showwarning("Dados inválidos", str(erro))
            return
        if self._persistir():
            self.var_status.set(mensagem)
            self.limpar_formulario()
            self.atualizar_tabela()

    def excluir(self):
        if self.id_selecionado is None:
            messagebox.showinfo("Excluir", "Selecione um produto na tabela.")
            return
        try:
            produto = core.encontrar_produto(self.produtos, self.id_selecionado)
        except core.ErroValidacao as erro:
            messagebox.showwarning("Excluir", str(erro))
            return
        if not messagebox.askyesno("Confirmar", f"Excluir '{produto['nome']}'?"):
            return
        core.remover_produto(self.produtos, produto["id"])
        if self._persistir():
            self.var_status.set(f"Produto '{produto['nome']}' removido.")
            self.limpar_formulario()
            self.atualizar_tabela()

    def movimentar(self, tipo):
        if self.id_selecionado is None:
            messagebox.showinfo("Movimentar", "Selecione um produto na tabela.")
            return
        try:
            produto = core.movimentar_estoque(self.produtos, self.id_selecionado,
                                              tipo, self.var_mov.get())
        except core.ErroValidacao as erro:
            messagebox.showwarning("Movimentação inválida", str(erro))
            return
        if self._persistir():
            rotulo = "Entrada" if tipo == "entrada" else "Saída"
            self.var_status.set(f"{rotulo} registrada: '{produto['nome']}' agora tem "
                                f"{produto['quantidade']} un.")
            self.var_quantidade.set(str(produto["quantidade"]))
            self.atualizar_tabela()

    def _fechar(self):
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
