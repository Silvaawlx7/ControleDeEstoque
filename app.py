"""Gestão de Estoque - versão web (Flask), responsiva."""

import os

from flask import Flask, flash, jsonify, redirect, render_template_string, request, url_for

import estoque_core as core

app = Flask(__name__)
app.secret_key = os.environ.get("ESTOQUE_SECRET", os.urandom(32))
app.jinja_env.filters["moeda"] = core.formatar_moeda

PAGINA = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gestão de Estoque</title>
<style>
  :root { --fundo:#f4f6f8; --cartao:#fff; --texto:#111827; --suave:#6b7280; --borda:#e5e7eb;
          --azul:#2563eb; --azul-esc:#1d4ed8; --vermelho:#dc2626; --verde:#16a34a;
          --alerta-bg:#fef3c7; --esgotado-bg:#fee2e2; }
  @media (prefers-color-scheme: dark) {
    :root { --fundo:#0f172a; --cartao:#1e293b; --texto:#f1f5f9; --suave:#94a3b8; --borda:#334155;
            --alerta-bg:#422006; --esgotado-bg:#450a0a; }
  }
  * { box-sizing: border-box; }
  body { margin:0; font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
         background:var(--fundo); color:var(--texto); line-height:1.4; }
  header { padding:16px; }
  h1 { margin:0; font-size:1.4rem; }
  main { max-width:1200px; margin:0 auto; padding:0 16px 32px; }
  .resumo { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin-bottom:16px; }
  .cartao { background:var(--cartao); border:1px solid var(--borda); border-radius:12px; padding:14px; }
  .cartao small { color:var(--suave); display:block; }
  .cartao strong { font-size:1.5rem; color:var(--azul); }
  .layout { display:grid; grid-template-columns:320px 1fr; gap:16px; align-items:start; }
  @media (max-width: 860px) { .layout { grid-template-columns:1fr; } }
  h2 { margin:0 0 10px; font-size:1.05rem; }
  label { display:block; font-size:.85rem; color:var(--suave); margin-top:8px; }
  input, select { width:100%; padding:10px; border:1px solid var(--borda); border-radius:8px;
                  background:var(--fundo); color:var(--texto); font-size:1rem; }
  .linha { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
  button, .botao { display:inline-block; padding:10px 14px; border:0; border-radius:8px; cursor:pointer;
                   background:var(--azul); color:#fff; font-size:.95rem; text-decoration:none; }
  button:hover, .botao:hover { background:var(--azul-esc); }
  .sec { background:transparent; color:var(--texto); border:1px solid var(--borda); }
  .sec:hover { background:var(--borda); }
  .perigo { background:var(--vermelho); } .perigo:hover { background:#b91c1c; }
  .acoes { display:flex; gap:8px; margin-top:12px; flex-wrap:wrap; }
  .busca { display:flex; gap:8px; margin-bottom:12px; flex-wrap:wrap; align-items:center; }
  .busca input[type=search] { flex:1 1 180px; width:auto; }
  .busca label { display:flex; gap:6px; align-items:center; margin:0; }
  .busca input[type=checkbox] { width:auto; }
  .aviso { padding:10px 14px; border-radius:8px; margin-bottom:12px; background:#dbeafe; color:#1e3a8a; }
  .aviso.erro { background:#fee2e2; color:#7f1d1d; }
  table { width:100%; border-collapse:collapse; }
  th, td { padding:10px 8px; text-align:left; border-bottom:1px solid var(--borda); vertical-align:middle; }
  th { font-size:.8rem; color:var(--suave); text-transform:uppercase; }
  tr.Baixo { background:var(--alerta-bg); } tr.Esgotado { background:var(--esgotado-bg); }
  .selo { font-size:.75rem; padding:2px 8px; border-radius:999px; border:1px solid var(--borda); }
  .mov { display:flex; gap:4px; } .mov input { width:64px; padding:6px; }
  .mov button { padding:6px 10px; }
  .vazio { text-align:center; color:var(--suave); padding:24px; }
  /* Celular: a tabela vira uma lista de cartões */
  @media (max-width: 700px) {
    table, thead, tbody, tr, td { display:block; }
    thead { display:none; }
    tr { background:var(--cartao); border:1px solid var(--borda); border-radius:12px;
         margin-bottom:10px; padding:8px; }
    tr.Baixo { background:var(--alerta-bg); } tr.Esgotado { background:var(--esgotado-bg); }
    td { border:0; display:flex; justify-content:space-between; gap:12px; padding:5px 4px; }
    td::before { content:attr(data-label); color:var(--suave); font-size:.8rem; }
  }
</style>
</head>
<body>
<header><h1>Gestão de Estoque</h1></header>
<main>
  {% for categoria, mensagem in get_flashed_messages(with_categories=true) %}
    <div class="aviso {{ 'erro' if categoria == 'erro' else '' }}">{{ mensagem }}</div>
  {% endfor %}

  <section class="resumo">
    <div class="cartao"><small>Produtos</small><strong>{{ resumo.produtos }}</strong></div>
    <div class="cartao"><small>Itens em estoque</small><strong>{{ resumo.itens }}</strong></div>
    <div class="cartao"><small>Valor em estoque</small><strong>{{ resumo.valor_total|moeda }}</strong></div>
    <div class="cartao"><small>Em alerta</small><strong>{{ resumo.alertas }}</strong></div>
  </section>

  <div class="layout">
    <section class="cartao">
      <h2>{{ 'Editando #%d'|format(edicao.id) if edicao else 'Novo produto' }}</h2>
      <form method="post" action="{{ url_for('salvar') }}">
        {% if edicao %}<input type="hidden" name="id" value="{{ edicao.id }}">{% endif %}
        <label for="nome">Nome</label>
        <input id="nome" name="nome" maxlength="60" required value="{{ form.nome }}">
        <label for="categoria">Categoria</label>
        <input id="categoria" name="categoria" maxlength="30" list="categorias" value="{{ form.categoria }}">
        <datalist id="categorias">{% for c in categorias %}<option value="{{ c }}">{% endfor %}</datalist>
        <div class="linha">
          <div><label for="quantidade">Quantidade</label>
            <input id="quantidade" name="quantidade" type="number" min="0" step="1" value="{{ form.quantidade }}"></div>
          <div><label for="minimo">Mínimo</label>
            <input id="minimo" name="minimo" type="number" min="0" step="1" value="{{ form.minimo }}"></div>
        </div>
        <label for="preco">Preço (R$)</label>
        <input id="preco" name="preco" inputmode="decimal" value="{{ form.preco }}">
        <div class="acoes">
          <button type="submit">{{ 'Salvar alterações' if edicao else 'Adicionar' }}</button>
          {% if edicao %}<a class="botao sec" href="{{ url_for('index') }}">Cancelar</a>{% endif %}
        </div>
      </form>
    </section>

    <section class="cartao">
      <h2>Produtos</h2>
      <form class="busca" method="get" action="{{ url_for('index') }}">
        <input type="search" name="q" placeholder="Buscar por nome ou categoria" value="{{ q }}">
        <label><input type="checkbox" name="alertas" value="1" {{ 'checked' if so_alertas }}> Só alertas</label>
        <button type="submit">Filtrar</button>
      </form>
      <table>
        <thead><tr><th>ID</th><th>Produto</th><th>Categoria</th><th>Qtd</th><th>Preço</th>
          <th>Situação</th><th>Movimentar</th><th></th></tr></thead>
        <tbody>
        {% for p in produtos %}
          <tr class="{{ p.situacao }}">
            <td data-label="ID">{{ p.id }}</td>
            <td data-label="Produto"><strong>{{ p.nome }}</strong></td>
            <td data-label="Categoria">{{ p.categoria }}</td>
            <td data-label="Qtd">{{ p.quantidade }} <small>(mín. {{ p.minimo }})</small></td>
            <td data-label="Preço">{{ p.preco|moeda }}</td>
            <td data-label="Situação"><span class="selo">{{ p.situacao }}</span></td>
            <td data-label="Movimentar">
              <form class="mov" method="post" action="{{ url_for('movimentar', produto_id=p.id) }}">
                <input type="number" name="quantidade" min="1" value="1" aria-label="Quantidade">
                <button name="tipo" value="entrada" title="Entrada">+</button>
                <button name="tipo" value="saida" class="sec" title="Saída">−</button>
              </form>
            </td>
            <td data-label="Ações">
              <div class="acoes" style="margin:0">
                <a class="botao sec" href="{{ url_for('index', editar=p.id) }}">Editar</a>
                <form method="post" action="{{ url_for('remover', produto_id=p.id) }}"
                      onsubmit="return confirm('Excluir este produto?')">
                  <button class="perigo">Excluir</button>
                </form>
              </div>
            </td>
          </tr>
        {% else %}
          <tr><td class="vazio" colspan="8">Nenhum produto encontrado.</td></tr>
        {% endfor %}
        </tbody>
      </table>
    </section>
  </div>
</main>
</body>
</html>
"""


def _produto_para_tela(produto):
    return {**produto, "situacao": core.situacao(produto)}


def _executar(acao, mensagem_sucesso):
    try:
        produtos = core.carregar_dados()
        acao(produtos)
        core.salvar_dados(produtos)
        flash(mensagem_sucesso, "ok")
        return True
    except core.ErroValidacao as erro:
        flash(str(erro), "erro")
    except OSError:
        flash("Não foi possível gravar o arquivo de estoque.", "erro")
    return False


@app.errorhandler(core.ErroValidacao)
def erro_dados(erro):
    return render_template_string("<h1>Erro no estoque</h1><p>{{ mensagem }}</p>",
                                  mensagem=str(erro)), 500


@app.errorhandler(OSError)
def erro_arquivo(erro):
    return "Não foi possível acessar o arquivo de estoque. Confira as permissões da pasta.", 500


@app.route("/")
def index():
    produtos = core.carregar_dados()
    q = request.args.get("q", "")
    so_alertas = request.args.get("alertas") == "1"
    filtrados = core.buscar_produtos(produtos, q, so_alertas)

    edicao = None
    form = {"nome": "", "categoria": "", "quantidade": "0", "minimo": "0", "preco": "0,00"}
    try:
        if request.args.get("editar"):
            edicao = core.encontrar_produto(produtos, request.args["editar"])
            form = {"nome": edicao["nome"], "categoria": edicao["categoria"],
                    "quantidade": edicao["quantidade"], "minimo": edicao["minimo"],
                    "preco": f"{edicao['preco']:.2f}".replace(".", ",")}
    except core.ErroValidacao as erro:
        flash(str(erro), "erro")

    return render_template_string(
        PAGINA, produtos=[_produto_para_tela(p) for p in filtrados],
        resumo=core.calcular_resumo(produtos), q=q, so_alertas=so_alertas,
        edicao=edicao, form=form,
        categorias=sorted({p["categoria"] for p in produtos}))


@app.post("/salvar")
def salvar():
    campos = [request.form.get(c, "") for c in ("nome", "categoria", "quantidade", "preco", "minimo")]
    produto_id = request.form.get("id")
    if produto_id:
        ok = _executar(lambda lista: core.editar_produto(lista, produto_id, *campos),
                       "Produto atualizado.")
        if not ok:
            return redirect(url_for("index", editar=produto_id))
    else:
        _executar(lambda lista: core.adicionar_produto(lista, *campos), "Produto adicionado.")
    return redirect(url_for("index"))


@app.post("/remover/<int:produto_id>")
def remover(produto_id):
    _executar(lambda lista: core.remover_produto(lista, produto_id), "Produto removido.")
    return redirect(url_for("index"))


@app.post("/movimentar/<int:produto_id>")
def movimentar(produto_id):
    tipo = request.form.get("tipo", "")
    quantidade = request.form.get("quantidade", "")
    _executar(lambda lista: core.movimentar_estoque(lista, produto_id, tipo, quantidade),
              "Movimentação registrada.")
    return redirect(url_for("index"))


@app.get("/api/produtos")
def api_produtos():
    return jsonify([_produto_para_tela(p) for p in core.carregar_dados()])


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
