# Simula um leitor de crachá que consulta o servidor e mostra a resposta no terminal.
# As matrículas são sorteadas porque o projeto não usa um leitor RFID físico.
import http.client
import json
import logging
import random
import socket
import time
import urllib.error
import urllib.request


# O DNS da rede Docker traduz o nome servidor-acesso para o IP do servidor.
URL_SERVIDOR = "http://servidor-acesso:8080/validar"
TOKEN_SECRETO = "Bearer pucpr-2026"
# O hostname configurado no Compose diferencia leitor-01 de leitor-02 nos registros.
LEITOR_ID = socket.gethostname()
# A última matrícula não está cadastrada e permite observar uma recusa de acesso.
MATRICULAS_TESTE = ["2026001", "2026002", "2026003", "9999999"]


def enviar_leitura(matricula):
    # Envia a matrícula junto com a identificação da porta que fez a consulta.
    # O JSON é convertido em bytes para ser enviado no corpo da requisição HTTP.
    dados = json.dumps({"leitor": LEITOR_ID, "matricula": matricula}).encode("utf-8")
    req = urllib.request.Request(
        URL_SERVIDOR,
        data=dados,
        headers={"Content-Type": "application/json", "Authorization": TOKEN_SECRETO},
        method="POST",
    )
    try:
        # O timeout limita a espera nas operações de rede. O with fecha a resposta ao sair.
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            resposta = json.loads(resp.read().decode("utf-8"))
            logging.info(
                "Matrícula %s -> %s (%s)",
                matricula, resposta["status"], resposta["usuario"],
            )
    except urllib.error.HTTPError as e:
        # HTTPError também é URLError: este except deve vir primeiro.
        # Um 403, por exemplo, é uma recusa do servidor e não uma falha de conexão.
        logging.warning("Matrícula %s -> HTTP %s: %s", matricula, e.code, e.reason)
        e.close()
    except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as e:
        # A falha é registrada sem encerrar o leitor. TimeoutError não possui .reason.
        logging.error("Servidor inacessível (%s). Nova tentativa no próximo ciclo.", e)
    except (ValueError, KeyError, TypeError) as e:
        # Uma resposta sem JSON válido ou sem os campos esperados também precisa ser tratada.
        logging.error("Resposta inválida do servidor (%s). Nova tentativa no próximo ciclo.", e)


def main():
    # Inclui o horário e o tipo da mensagem para facilitar a leitura dos testes.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    try:
        while True:
            # Cada ciclo simula uma nova leitura; não há fila de leituras antigas.
            enviar_leitura(random.choice(MATRICULAS_TESTE))
            # Aguarda quatro segundos depois de cada tentativa, inclusive quando há erro.
            time.sleep(4)
    except KeyboardInterrupt:
        # Permite encerrar a simulação com Ctrl+C sem mostrar uma mensagem de exceção.
        logging.info("Leitor encerrado")


# O ciclo só começa ao executar o arquivo, não quando ele é importado nos testes.
if __name__ == "__main__":
    main()
