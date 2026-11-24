# A imagem já traz Linux e Python 3.11; não é preciso instalar Python no computador.
FROM python:3.11-slim

# iproute2 fornece ip e ss; os outros pacotes fornecem ping e tcpdump.
# A lista do apt é apagada depois da instalação para ocupar menos espaço na imagem.
RUN apt-get update && apt-get install -y --no-install-recommends \
    iproute2 iputils-ping tcpdump \
    && rm -rf /var/lib/apt/lists/*

# Cria um usuário comum para executar o programa.
RUN useradd -m -u 1000 appuser
# Os comandos dos serviços serão executados dentro de /app.
WORKDIR /app
COPY servidor.py cliente.py testes.py ./
# A pasta dos logs precisa pertencer ao appuser para ele conseguir gravar nela.
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# A partir daqui, o programa roda como appuser, sem privilégios de root.
USER appuser
