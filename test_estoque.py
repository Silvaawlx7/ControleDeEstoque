import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, Mock

import estoque_core as core
import desktop
from app import app


class TestEstoque(unittest.TestCase):
    def setUp(self):
        self.produtos = []
        self.produto = core.adicionar_produto(self.produtos, 'Caderno', 'Papelaria', 5, '12,50', 2)

    def test_cadastro_e_resumo(self):
        self.assertEqual(core.calcular_resumo(self.produtos),
                         {'produtos': 1, 'itens': 5, 'valor_total': 62.5, 'alertas': 0})

    def test_validacao(self):
        for qtd, preco in [('-1', '2'), ('1.5', '2'), ('2', 'nan'), ('2', 'inf'), ('2', '-1')]:
            with self.subTest(qtd=qtd, preco=preco), self.assertRaises(core.ErroValidacao):
                core.validar_campos('Lápis', '', qtd, preco, 0)
        with self.assertRaises(core.ErroValidacao):
            core.validar_campos('', '', 0, 0, 0)

    def test_duplicado(self):
        with self.assertRaises(core.ErroValidacao):
            core.adicionar_produto(self.produtos, 'caderno', '', 1, 2, 0)

    def test_movimentacao(self):
        core.movimentar_estoque(self.produtos, 1, 'saida', 3)
        self.assertEqual(core.situacao(self.produto), 'Baixo')
        with self.assertRaises(core.ErroValidacao):
            core.movimentar_estoque(self.produtos, 1, 'saida', 3)
        self.assertEqual(self.produto['quantidade'], 2)
        core.movimentar_estoque(self.produtos, 1, 'entrada', 1)
        self.assertEqual(self.produto['quantidade'], 3)

    def test_edicao_busca_exclusao(self):
        core.editar_produto(self.produtos, 1, 'Caneta', 'Papelaria', 0, 2, 1)
        self.assertEqual(core.buscar_produtos(self.produtos, 'papel', True), self.produtos)
        self.assertEqual(core.situacao(self.produto), 'Esgotado')
        core.remover_produto(self.produtos, 1)
        self.assertEqual(self.produtos, [])

    def test_arquivo(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta)/'estoque.json'
            self.assertEqual(core.carregar_dados(arquivo), [])
            core.salvar_dados(self.produtos, arquivo)
            self.assertEqual(core.carregar_dados(arquivo), self.produtos)
            for conteudo in ['{', '{}', '[{}]', json.dumps(self.produtos * 2)]:
                arquivo.write_text(conteudo)
                with self.assertRaises(core.ErroValidacao):
                    core.carregar_dados(arquivo)
                self.assertEqual(arquivo.read_text(), conteudo)

    def test_falha_salvamento_desktop(self):
        tela = SimpleNamespace(produtos=[{'id': 2}], produtos_salvos=[{'id': 1}], atualizar_tabela=Mock())
        with patch.object(core, 'salvar_dados', side_effect=OSError('Sem permissão')), patch.object(desktop.messagebox, 'showerror'):
            self.assertFalse(desktop.App._persistir(tela))
        self.assertEqual(tela.produtos, [{'id': 1}])

    def test_fluxo_web(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta)/'estoque.json'
            carregar, salvar = core.carregar_dados, core.salvar_dados
            with patch.object(core, 'carregar_dados', side_effect=lambda: carregar(arquivo)), patch.object(core, 'salvar_dados', side_effect=lambda dados: salvar(dados, arquivo)):
                cliente = app.test_client()
                self.assertEqual(cliente.get('/').status_code, 200)
                resposta = cliente.post('/salvar', data={'nome': "D'água <teste>", 'categoria': 'Geral', 'quantidade': 3, 'preco': '2,50', 'minimo': 1}, follow_redirects=True)
                self.assertEqual(resposta.status_code, 200)
                self.assertIn(b'&lt;teste&gt;', resposta.data)
                self.assertEqual(len(cliente.get('/api/produtos').json), 1)
                cliente.post('/movimentar/1', data={'tipo': 'saida', 'quantidade': 2})
                self.assertEqual(carregar(arquivo)[0]['quantidade'], 1)
                cliente.post('/salvar', data={'id': 1, 'nome': 'Caneta', 'categoria': 'Geral', 'quantidade': 4, 'preco': '3', 'minimo': 1})
                self.assertEqual(carregar(arquivo)[0]['nome'], 'Caneta')
                cliente.post('/remover/1')
                self.assertEqual(carregar(arquivo), [])
                arquivo.write_text('{')
                self.assertEqual(cliente.get('/').status_code, 500)
                self.assertEqual(arquivo.read_text(), '{')


if __name__ == '__main__':
    unittest.main()
