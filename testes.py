"""Testes isolados da aplicação, usando apenas a biblioteca padrão.

Execute: python3 testes.py
As chamadas de rede são simuladas. Os testes de rede real estão no README.
"""

import io
import json
import unittest
from http.client import HTTPException
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError, URLError

import cliente
import servidor


class TestesServidor(unittest.TestCase):
    def setUp(self):
        # O unittest chama setUp antes de cada teste.
        # patch troca o logging por uma simulação para não gravar acessos de teste.
        self.logs = patch.object(servidor, "logging")
        self.logs.start()
        # Restaura o logging mesmo se algum teste falhar.
        self.addCleanup(self.logs.stop)

    def requisicao(self, dados=None, corpo=None, caminho="/validar",
                   token="Bearer pucpr-2026", tamanho=None):
        """Monta uma requisição em memória, sem abrir uma porta de rede."""
        if corpo is None:
            corpo = json.dumps(dados).encode("utf-8")
        # __new__ cria o objeto sem executar a inicialização que espera uma conexão.
        # Os campos usados por do_POST são preenchidos aqui para testar as regras.
        handler = servidor.HandlerAcesso.__new__(servidor.HandlerAcesso)
        handler.path = caminho
        handler.headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "Content-Length": str(len(corpo)) if tamanho is None else tamanho,
        }
        # BytesIO permite ler os bytes como se viessem do arquivo da conexão.
        handler.rfile = io.BytesIO(corpo)
        handler.client_address = ("127.0.0.1", 12345)
        # Mock guarda a chamada a responder, sem enviar dados pela rede.
        handler.responder = Mock()
        handler.do_POST()
        handler.responder.assert_called_once()
        # Devolve o código HTTP e o conteúdo para conferir no teste.
        return handler.responder.call_args.args

    def test_matriculas_autorizadas(self):
        # Confere as três pessoas do cadastro, incluindo o nome devolvido.
        for matricula, nome in [("2026001", "Nicolas"), ("2026002", "Ana"),
                                ("2026003", "Carlos")]:
            # subTest identifica qual matrícula falhou e permite testar as demais.
            with self.subTest(matricula=matricula):
                codigo, resposta = self.requisicao(
                    {"matricula": matricula, "leitor": "leitor-01"})
                # assertEqual compara o resultado recebido com o esperado.
                self.assertEqual(codigo, 200)
                self.assertEqual(resposta, {"status": "LIBERADO", "usuario": nome})

    def test_matricula_desconhecida(self):
        # O formato está correto, mas essa matrícula não está no cadastro.
        codigo, resposta = self.requisicao(
            {"matricula": "9999999", "leitor": "leitor-02"})
        self.assertEqual(codigo, 403)
        self.assertEqual(resposta["status"], "NEGADO")

    def test_token_incorreto(self):
        # Uma matrícula cadastrada não deve ser aceita com token errado.
        codigo, _ = self.requisicao(
            {"matricula": "2026001", "leitor": "leitor-01"}, token="incorreto")
        self.assertEqual(codigo, 401)

    def test_rota_inexistente(self):
        # Só /validar pode consultar a autorização de acesso.
        codigo, _ = self.requisicao(
            {"matricula": "2026001", "leitor": "leitor-01"}, caminho="/outra")
        self.assertEqual(codigo, 404)

    def test_json_invalido(self):
        # Testa JSON incompleto e bytes que não podem ser lidos como UTF-8.
        for corpo in [b'{"matricula":', b"\xff"]:
            with self.subTest(corpo=corpo):
                codigo, _ = self.requisicao(corpo=corpo)
                self.assertEqual(codigo, 400)

    def test_campos_invalidos(self):
        # Reúne dados ausentes, tipos errados e valores fora dos limites aceitos.
        entradas = [
            [], None, {},
            {"matricula": "2026001"},
            {"leitor": "leitor-01"},
            {"matricula": 2026001, "leitor": "leitor-01"},
            {"matricula": "2026ABC", "leitor": "leitor-01"},
            {"matricula": "123", "leitor": "leitor-01"},
            {"matricula": "２０２６００１", "leitor": "leitor-01"},
            {"matricula": "2026001", "leitor": "   "},
            {"matricula": "2026001", "leitor": 1},
            {"matricula": "2026001", "leitor": "a" * 51},
        ]
        for dados in entradas:
            with self.subTest(dados=dados):
                codigo, _ = self.requisicao(dados)
                self.assertEqual(codigo, 400)

    def test_tamanho_invalido(self):
        # O tamanho deve ser um número entre 1 e 4096 bytes.
        for tamanho in ["abc", "0", "-1", "4097"]:
            with self.subTest(tamanho=tamanho):
                codigo, _ = self.requisicao(corpo=b"{}", tamanho=tamanho)
                self.assertEqual(codigo, 400)

    def test_cliente_desconectado_gera_aviso_sem_excecao(self):
        # O leitor pode atingir seu timeout antes de o servidor responder.
        for erro in [BrokenPipeError("conexão fechada"),
                     ConnectionResetError("conexão interrompida")]:
            with self.subTest(erro=erro):
                handler = servidor.HandlerAcesso.__new__(servidor.HandlerAcesso)
                handler.send_response = Mock()
                handler.send_header = Mock()
                handler.end_headers = Mock()
                handler.wfile = Mock()
                # side_effect provoca a falha quando o servidor tenta escrever.
                handler.wfile.write.side_effect = erro
                # Zera as chamadas anteriores para conferir somente este caso.
                servidor.logging.warning.reset_mock()
                handler.responder(200, {"status": "LIBERADO", "usuario": "Nicolas"})
                handler.wfile.write.assert_called_once()
                servidor.logging.warning.assert_called_once()


class TestesCliente(unittest.TestCase):
    def setUp(self):
        # Evita misturar as mensagens esperadas de erro com a saída dos testes.
        self.logs = patch.object(cliente, "logging")
        self.logs.start()
        self.addCleanup(self.logs.stop)

    def resposta(self, corpo):
        # MagicMock simula a resposta usada pelo cliente no bloco with.
        # __enter__ define o objeto recebido ao entrar nesse bloco.
        resposta = MagicMock()
        resposta.__enter__.return_value = resposta
        # read() entrega os bytes escolhidos para cada caso de teste.
        resposta.read.return_value = corpo
        return resposta

    def test_envia_json_token_e_timeout(self):
        resposta = self.resposta(b'{"status": "LIBERADO", "usuario": "Nicolas"}')
        # Substitui urlopen apenas dentro do with, sem fazer uma consulta real.
        with patch.object(cliente.urllib.request, "urlopen", return_value=resposta) as abrir:
            cliente.enviar_leitura("2026001")
        # call_args guarda os argumentos enviados pelo cliente ao abrir a conexão.
        pedido = abrir.call_args.args[0]
        self.assertEqual(pedido.full_url, cliente.URL_SERVIDOR)
        self.assertEqual(pedido.get_method(), "POST")
        self.assertEqual(json.loads(pedido.data),
                         {"matricula": "2026001", "leitor": cliente.LEITOR_ID})
        # Nomes de cabeçalhos HTTP podem variar entre maiúsculas e minúsculas.
        cabecalhos = {nome.lower(): valor for nome, valor in pedido.header_items()}
        self.assertEqual(cabecalhos["authorization"], "Bearer pucpr-2026")
        self.assertEqual(cabecalhos["content-type"], "application/json")
        self.assertEqual(abrir.call_args.kwargs["timeout"], 2.0)

    def test_falhas_de_conexao_nao_encerram_cliente(self):
        # Cada erro deve ser tratado dentro de enviar_leitura, sem sair da função
        # com uma exceção. Se isso acontecer, o unittest marca o caso como erro.
        erros = [TimeoutError("tempo esgotado"), URLError("conexão recusada"),
                 ConnectionResetError("conexão encerrada"), HTTPException("falha HTTP")]
        for erro in erros:
            with self.subTest(erro=erro):
                with patch.object(cliente.urllib.request, "urlopen", side_effect=erro):
                    cliente.enviar_leitura("2026001")

    def test_timeout_durante_leitura_nao_encerra_cliente(self):
        # A conexão pode abrir e o tempo se esgotar durante read().
        # Este teste evita repetir a falha de acessar .reason em TimeoutError.
        resposta = self.resposta(b"")
        resposta.read.side_effect = TimeoutError("tempo esgotado na leitura")
        with patch.object(cliente.urllib.request, "urlopen", return_value=resposta):
            cliente.enviar_leitura("2026001")

    def test_erro_http_com_json_ou_html_nao_encerra_cliente(self):
        # O cliente deve tratar o código HTTP mesmo se a resposta não for JSON.
        for corpo in [b'{"status": "NEGADO"}', b"<html>Erro HTTP</html>"]:
            with self.subTest(corpo=corpo):
                erro = HTTPError(cliente.URL_SERVIDOR, 403, "Forbidden", {}, io.BytesIO(corpo))
                with patch.object(cliente.urllib.request, "urlopen", side_effect=erro):
                    cliente.enviar_leitura("9999999")

    def test_resposta_invalida_nao_encerra_cliente(self):
        # Uma resposta que não pode ser lida como JSON também deve gerar só um log.
        resposta = self.resposta(b"isto nao e JSON")
        with patch.object(cliente.urllib.request, "urlopen", return_value=resposta):
            cliente.enviar_leitura("2026001")


if __name__ == "__main__":
    # Mostra o nome e o resultado de cada teste ao executar este arquivo.
    unittest.main(verbosity=2)
