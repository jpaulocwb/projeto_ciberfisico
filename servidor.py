# Servidor da simulação: recebe a matrícula, consulta o cadastro e registra a decisão.
# A comunicação com os leitores usa HTTP na porta 8080.
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import logging
import threading


# Token demonstrativo compartilhado pelos leitores. HTTP não criptografa os dados.
TOKEN_SECRETO = "Bearer pucpr-2026"
# O cadastro fica neste dicionário para manter o projeto simples, sem banco de dados.
AUTORIZADOS = {
    "2026001": "Nicolas",
    "2026002": "Ana",
    "2026003": "Carlos",
}


# Esta classe define como o servidor trata e responde às requisições dos leitores.
class HandlerAcesso(BaseHTTPRequestHandler):
    def responder(self, codigo, dados):
        # O código informa o resultado HTTP; os dados são enviados como JSON em UTF-8.
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        try:
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            # Content-Length informa a quantidade de bytes, incluindo os acentos.
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
        except ConnectionError:
            # O leitor pode desistir por timeout antes de receber a resposta.
            logging.warning("Cliente desconectou antes de receber a resposta")

    def do_POST(self):
        # O servidor HTTP chama este método quando recebe uma requisição POST.
        # Somente esta rota realiza a consulta de autorização.
        if self.path != "/validar":
            return self.responder(404, {"erro": "Rota não encontrada"})

        # Confere o token antes de consultar a matrícula enviada pelo dispositivo.
        if self.headers.get("Authorization") != TOKEN_SECRETO:
            logging.warning("Token inválido recebido de %s", self.client_address[0])
            return self.responder(401, {"erro": "Token inválido"})

        # O JSON esperado é pequeno. O limite de 4096 bytes evita ler corpos muito grandes.
        try:
            tamanho = int(self.headers.get("Content-Length", 0))
            if tamanho <= 0 or tamanho > 4096:
                return self.responder(400, {"erro": "Tamanho da mensagem inválido"})
            corpo = json.loads(self.rfile.read(tamanho).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return self.responder(400, {"erro": "JSON ou tamanho inválido"})

        # Uma lista ou um número também pode ser JSON, mas aqui precisamos de campos.
        if not isinstance(corpo, dict):
            return self.responder(400, {"erro": "O JSON deve ser um objeto"})

        # O formato de matrícula adotado neste projeto tem sete dígitos.
        matricula = corpo.get("matricula")
        leitor = corpo.get("leitor")
        if not isinstance(matricula, str) or not isinstance(leitor, str):
            return self.responder(400, {"erro": "Matrícula e leitor devem ser textos"})

        # Retira espaços das pontas e aceita apenas os dígitos de 0 a 9 na matrícula.
        matricula = matricula.strip()
        leitor = leitor.strip()
        if len(matricula) != 7 or not matricula.isascii() or not matricula.isdigit():
            return self.responder(400, {"erro": "Matrícula deve conter sete dígitos"})
        if not leitor or len(leitor) > 50:
            return self.responder(400, {"erro": "Leitor deve conter de 1 a 50 caracteres"})

        # O nome da thread ajuda a identificar os atendimentos no log do servidor.
        thread_atual = threading.current_thread().name
        # Registra a decisão; não confirma uma passagem física pela porta.
        if matricula in AUTORIZADOS:
            nome = AUTORIZADOS[matricula]
            logging.info(
                "[%s] LIBERADO | Leitor=%s | Aluno=%s (%s)",
                thread_atual, leitor, nome, matricula,
            )
            self.responder(200, {"status": "LIBERADO", "usuario": nome})
        else:
            logging.warning(
                "[%s] NEGADO | Leitor=%s | Matrícula=%s",
                thread_atual, leitor, matricula,
            )
            self.responder(403, {"status": "NEGADO", "motivo": "Matrícula não cadastrada"})

    def log_message(self, format, *args):
        # Desativa o log automático de HTTP; os registros usados no projeto estão acima.
        pass


def main():
    # No Docker, esta pasta é /app/logs e fica em um volume persistente.
    pasta_logs = Path(__file__).resolve().parent / "logs"
    pasta_logs.mkdir(exist_ok=True)
    # Mostra os registros no terminal e também salva uma cópia no arquivo de histórico.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(pasta_logs / "acessos.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    # 0.0.0.0 aceita conexões pelas interfaces do contêiner.
    # Cada conexão é atendida em uma thread, permitindo atender mais de um leitor.
    with ThreadingHTTPServer(("0.0.0.0", 8080), HandlerAcesso) as servidor:
        logging.info("Servidor de Controle de Acesso na porta 8080 (HTTP/TCP)")
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            logging.info("Servidor encerrado")


# Importar este arquivo nos testes não inicia o servidor.
if __name__ == "__main__":
    main()
