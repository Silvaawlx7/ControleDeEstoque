"""Núcleo do sistema de estoque."""

import json
import math
import os
import tempfile
from datetime import datetime

ARQUIVO_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "estoque.json")


class ErroValidacao(ValueError):
    pass


def carregar_dados(caminho=ARQUIVO_JSON):
    """Lê os produtos sem apagar um arquivo que esteja com problemas."""
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, UnicodeError) as erro:
        raise ErroValidacao("O estoque.json está inválido. Confira o arquivo antes de continuar.") from erro

    if not isinstance(dados, list):
        raise ErroValidacao("O estoque.json deve conter uma lista de produtos.")
    ids = set()
    produtos = []
    for item in dados:
        try:
            if not isinstance(item, dict):
                raise ValueError()
            produto_id = item["id"]
            if type(produto_id) is not int or produto_id < 1 or produto_id in ids:
                raise ValueError()
            if not isinstance(item["nome"], str) or not isinstance(item["categoria"], str):
                raise ValueError()
            campos = validar_campos(item["nome"], item["categoria"], item["quantidade"],
                                    item["preco"], item["minimo"])
        except (KeyError, TypeError, ValueError) as erro:
            raise ErroValidacao("Há um produto inválido ou um ID repetido no estoque.json.") from erro
        ids.add(produto_id)
        produtos.append({**item, **campos})
    return produtos


def salvar_dados(produtos, caminho=ARQUIVO_JSON):
    pasta = os.path.dirname(caminho) or "."
    descritor, temporario = tempfile.mkstemp(dir=pasta, suffix=".tmp")
    try:
        with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
            json.dump(produtos, arquivo, ensure_ascii=False, indent=2)
        os.replace(temporario, caminho)
    except OSError:
        if os.path.exists(temporario):
            os.remove(temporario)
        raise

def _inteiro_nao_negativo(valor, rotulo):
    try:
        numero = int(str(valor).strip())
    except (ValueError, TypeError):
        raise ErroValidacao(f"{rotulo} deve ser um número inteiro.")
    if numero < 0:
        raise ErroValidacao(f"{rotulo} não pode ser negativo.")
    return numero


def validar_campos(nome, categoria, quantidade, preco, minimo):
    nome = str(nome).strip()
    if not nome:
        raise ErroValidacao("O nome do produto é obrigatório.")
    if len(nome) > 60:
        raise ErroValidacao("O nome deve ter no máximo 60 caracteres.")

    categoria = str(categoria).strip() or "Geral"
    if len(categoria) > 30:
        raise ErroValidacao("A categoria deve ter no máximo 30 caracteres.")

    quantidade = _inteiro_nao_negativo(quantidade, "Quantidade")

    try:
        preco = float(str(preco).strip().replace(",", "."))
    except (ValueError, TypeError):
        raise ErroValidacao("Preço deve ser um número (ex.: 19,90).")
    if not math.isfinite(preco) or preco < 0:
        raise ErroValidacao("Preço deve ser um valor válido e não negativo.")

    texto_minimo = str(minimo).strip()
    minimo = _inteiro_nao_negativo(texto_minimo or 0, "Estoque mínimo")

    return {
        "nome": nome,
        "categoria": categoria,
        "quantidade": quantidade,
        "preco": round(preco, 2),
        "minimo": minimo,
    }

def agora():
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def gerar_id(produtos):
    return max((p.get("id", 0) for p in produtos), default=0) + 1


def encontrar_produto(produtos, produto_id):
    try:
        produto_id = int(produto_id)
    except (ValueError, TypeError):
        raise ErroValidacao("Identificador de produto inválido.")
    for produto in produtos:
        if produto.get("id") == produto_id:
            return produto
    raise ErroValidacao("Produto não encontrado.")


def _checar_nome_duplicado(produtos, nome, ignorar_id=None):
    for produto in produtos:
        if produto["id"] != ignorar_id and produto["nome"].lower() == nome.lower():
            raise ErroValidacao(f"Já existe um produto chamado '{nome}'.")


def adicionar_produto(produtos, nome, categoria, quantidade, preco, minimo):
    campos = validar_campos(nome, categoria, quantidade, preco, minimo)
    _checar_nome_duplicado(produtos, campos["nome"])
    produto = {"id": gerar_id(produtos), **campos, "atualizado_em": agora()}
    produtos.append(produto)
    return produto


def editar_produto(produtos, produto_id, nome, categoria, quantidade, preco, minimo):
    produto = encontrar_produto(produtos, produto_id)
    campos = validar_campos(nome, categoria, quantidade, preco, minimo)
    _checar_nome_duplicado(produtos, campos["nome"], ignorar_id=produto["id"])
    produto.update(campos)
    produto["atualizado_em"] = agora()
    return produto


def remover_produto(produtos, produto_id):
    produto = encontrar_produto(produtos, produto_id)
    produtos.remove(produto)
    return produto


def movimentar_estoque(produtos, produto_id, tipo, quantidade):
    produto = encontrar_produto(produtos, produto_id)
    quantidade = _inteiro_nao_negativo(quantidade, "Quantidade da movimentação")
    if quantidade == 0:
        raise ErroValidacao("A movimentação deve ser maior que zero.")
    if tipo == "entrada":
        produto["quantidade"] += quantidade
    elif tipo == "saida":
        if quantidade > produto["quantidade"]:
            raise ErroValidacao(
                f"Saída maior que o estoque disponível ({produto['quantidade']})."
            )
        produto["quantidade"] -= quantidade
    else:
        raise ErroValidacao("Tipo de movimentação inválido.")
    produto["atualizado_em"] = agora()
    return produto


def situacao(produto):
    if produto["quantidade"] == 0:
        return "Esgotado"
    if produto["quantidade"] <= produto["minimo"]:
        return "Baixo"
    return "OK"


def buscar_produtos(produtos, termo="", apenas_alertas=False):
    termo = termo.strip().lower()
    resultado = []
    for produto in produtos:
        if termo and termo not in produto["nome"].lower() and termo not in produto["categoria"].lower():
            continue
        if apenas_alertas and situacao(produto) == "OK":
            continue
        resultado.append(produto)
    return sorted(resultado, key=lambda p: p["nome"].lower())


def calcular_resumo(produtos):
    return {
        "produtos": len(produtos),
        "itens": sum(p["quantidade"] for p in produtos),
        "valor_total": round(sum(p["quantidade"] * p["preco"] for p in produtos), 2),
        "alertas": sum(1 for p in produtos if situacao(p) != "OK"),
    }


def formatar_moeda(valor):
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"
