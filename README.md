# Controle de acesso físico simulado

Projeto didático de conectividade para o primeiro ano de Ciência da Computação, inspirado no tema 10 da disciplina PSI129A. Dois leitores simulados consultam um servidor para saber se uma matrícula está autorizada. O servidor registra a tentativa e sua decisão em um arquivo de log.

O projeto usa apenas a biblioteca padrão do Python. Não é necessário instalar pacotes com `pip`, banco de dados ou leitor RFID físico. Não há painel web: a demonstração acontece pelo terminal e por requisições HTTP.

## Integrantes

- Nicolas Rodrigo Zinc Gonçalves dos Santos
- João Paulo Gonçalves Barbosa

## Documentação e evidências

O código Python e os arquivos do Docker ficam na raiz. Execute os comandos deste README nesta pasta, onde está `compose.yaml`.

## 1. Arquivos e funcionamento

| Arquivo | Função |
|---|---|
| `servidor.py` | Recebe requisições, valida token e dados, consulta as matrículas e grava logs. |
| `cliente.py` | Simula um leitor, sorteando uma matrícula e consultando o servidor a cada ciclo. |
| `compose.yaml` | Define os três contêineres, a rede e o volume dos logs. |
| `Dockerfile` | Prepara Linux, Python, ferramentas de diagnóstico e o usuário `appuser`. |
| `testes.py` | Executa testes automatizados com `unittest`, sem dependências externas. |

```text
leitor-01 (172.30.0.21) ---- HTTP/TCP ---->
                                           servidor-acesso (172.30.0.10:8080)
leitor-02 (172.30.0.22) ---- HTTP/TCP ---->             |
                                                      +--> logs/acessos.log
```

| Elemento | Configuração |
|---|---|
| Rede Docker | Bridge, `172.30.0.0/24` |
| Máscara | `255.255.255.0` |
| Gateway | `172.30.0.1` |
| Servidor | `servidor-acesso`, IP `172.30.0.10`, porta TCP `8080` |
| Leitores | `leitor-01`: `172.30.0.21`; `leitor-02`: `172.30.0.22` |
| DNS | O Docker resolve o nome `servidor-acesso` dentro da rede. |
| Acesso pelo computador | `http://127.0.0.1:8080/validar` |
| Logs persistentes | Volume Docker `logs_acesso`, montado em `/app/logs` no servidor |

Os leitores usam `http://servidor-acesso:8080/validar`. A publicação `127.0.0.1:8080:8080` permite testes no próprio computador e não publica o serviço em todas as interfaces do hospedeiro. Os IPs `172.30.0.x` são da rede dos contêineres; use `127.0.0.1` nos testes feitos pelo computador.

## 2. Instalação

1. **Windows ou macOS:** instale e abra o [Docker Desktop](https://docs.docker.com/get-docker/). No Windows, siga a [instalação com WSL 2](https://docs.docker.com/desktop/setup/install/windows-install/) e use contêineres Linux.
2. **Linux:** siga a instalação do [Docker Engine](https://docs.docker.com/engine/install/) para sua distribuição e do [plugin Docker Compose](https://docs.docker.com/compose/install/linux/).
3. Extraia o ZIP e abra um terminal dentro da pasta `controle_acesso`, onde está `compose.yaml`.
4. Verifique a instalação:

```sh
docker version
docker compose version
```

O primeiro comando deve mostrar informações do cliente e do servidor Docker. O Docker precisa estar em execução. A primeira construção precisa de internet para baixar a imagem e as ferramentas Linux. Usando Docker, não é necessário instalar Python no computador.

## 3. Executar e acompanhar

Na pasta do projeto:

```sh
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs -f
```

Os três serviços devem aparecer em execução. Os leitores enviam matrículas e mostram `LIBERADO` ou a resposta de acesso negado. `Ctrl+C` encerra apenas o acompanhamento dos logs; os serviços continuam em execução.

Para ver somente o servidor ou um leitor:

```sh
docker compose logs -f servidor-acesso
docker compose logs -f leitor-01
```

Para parar e remover os contêineres, preservando o histórico:

```sh
docker compose down
```

Para iniciar novamente:

```sh
docker compose up -d
```

Se modificar o código, use novamente `docker compose up --build -d`, pois os arquivos são copiados para a imagem durante a construção.

## 4. Mensagens e respostas

A única operação da aplicação é `POST /validar`, com JSON e o cabeçalho `Authorization: Bearer pucpr-2026`.

```json
{"leitor": "leitor-01", "matricula": "2026001"}
```

Regras de entrada:

- O corpo deve ser um objeto JSON.
- `matricula` deve ser texto com exatamente sete dígitos de `0` a `9`, após remover espaços das extremidades.
- `leitor` deve ser texto não vazio, com até 50 caracteres após remover espaços das extremidades.
- O token deve corresponder ao valor configurado no código.

| Matrícula | Pessoa / resultado |
|---|---|
| `2026001` | Nicolas: autorizado |
| `2026002` | Ana: autorizada |
| `2026003` | Carlos: autorizado |
| `9999999` | Não cadastrada: acesso negado |

| Código HTTP | Significado |
|---|---|
| `200` | Matrícula autorizada; resposta com `status` e `usuario`. |
| `403` | Matrícula válida no formato, mas não cadastrada; resposta com `status` e `motivo`. |
| `401` | Token ausente ou incorreto. |
| `400` | JSON ou campos inválidos. |
| `404` | `POST` enviado para uma rota diferente de `/validar`. |

Abrir o endereço no navegador envia `GET`, que não está implementado e recebe HTTP `501`. Isso não indica que o servidor deixou de funcionar.

## 5. Testes automatizados

Com os serviços em execução, execute os testes dentro do servidor:

```sh
docker compose exec servidor-acesso python testes.py
```

Também é possível rodar os testes diretamente na pasta do projeto com Python 3.11 ou mais recente:

```sh
python3 testes.py
```

No Windows, se o comando instalado for `py`, use `py testes.py`.

Os testes isolados verificam o comportamento do código e devem terminar com `OK`. Eles não substituem a demonstração dos contêineres, do DNS, da rede e do volume. Para essas partes, execute os testes manuais a seguir e registre os resultados realmente obtidos.

## 6. Testes manuais de HTTP

Com os serviços em execução, crie na pasta do projeto um arquivo temporário chamado `requisicao.json` com este conteúdo:

```json
{"leitor": "leitor-01", "matricula": "2026001"}
```

Execute no computador, na mesma pasta:

```sh
curl -i -X POST http://127.0.0.1:8080/validar -H "Content-Type: application/json" -H "Authorization: Bearer pucpr-2026" --data-binary @requisicao.json
```

No PowerShell, use `curl.exe` no lugar de `curl` e escreva `--data-binary "@requisicao.json"`. O arquivo evita diferenças de escape de aspas entre terminais.

O resultado esperado é HTTP `200` e um JSON semelhante a:

```json
{"status": "LIBERADO", "usuario": "Nicolas"}
```

Repita o comando com as alterações abaixo, restaurando o arquivo e o comando entre os casos:

| Teste | Alteração | Resultado esperado |
|---|---|---|
| T01: autorização | Use o JSON apresentado acima. | `200`, `LIBERADO`, Nicolas. |
| T02: matrícula desconhecida | Troque a matrícula por `9999999`. | `403`, `NEGADO`. |
| T03: autenticação | Troque o token no comando por `Bearer errado`. | `401`. |
| T04: JSON inválido | Deixe somente `{` no arquivo. | `400`. |
| T05: campo obrigatório | Use `{"matricula":"2026001"}`, sem `leitor`. | `400`. |
| T06: formato da matrícula | Use `{"leitor":"leitor-01","matricula":"abc"}`. | `400`. |
| T07: rota | Restaure o JSON válido e troque `/validar` por `/outra` na URL. | `404`. |

Para conferir o registro das decisões:

```sh
docker compose exec servidor-acesso tail -n 20 /app/logs/acessos.log
```

## 7. Falhas, concorrência e persistência

### Servidor fora do ar e recuperação

Em um terminal, acompanhe `docker compose logs -f leitor-01`. Em outro, execute:

```sh
docker compose stop servidor-acesso
```

Aguarde alguns ciclos. O leitor deve registrar falhas de comunicação e continuar em execução. Depois:

```sh
docker compose start servidor-acesso
```

As consultas devem voltar a funcionar nos ciclos seguintes. O leitor espera quatro segundos entre ciclos; uma operação que aguarde o timeout acrescenta aproximadamente dois segundos de espera.

### Timeout sem encerrar o leitor

Com os serviços funcionando, pause temporariamente o servidor:

```sh
docker compose pause servidor-acesso
```

Aguarde pelo menos dez segundos e observe os logs do leitor. O timeout deve ser registrado sem causar `AttributeError` nem encerrar o processo. Ao terminar o teste, retome o servidor:

```sh
docker compose unpause servidor-acesso
```

Confira a recuperação nos logs. Não deixe o servidor pausado ao seguir para os demais testes.

### Dois leitores

Mantenha os dois leitores ligados e acompanhe:

```sh
docker compose logs -f servidor-acesso leitor-01 leitor-02
```

Verifique registros dos dois leitores e os nomes das threads no servidor. O servidor usa `ThreadingHTTPServer`, que permite atendimento concorrente. Duas linhas próximas no log, por si só, não medem sobreposição nem desempenho; não declare uma latência ou quantidade de requisições simultâneas sem realizar essa medição.

Opcionalmente, envie seis consultas por threads do mesmo leitor:

```sh
docker compose exec leitor-01 python -c "import cliente, logging; from concurrent.futures import ThreadPoolExecutor; logging.basicConfig(level=logging.INFO); executor = ThreadPoolExecutor(max_workers=6); list(executor.map(cliente.enviar_leitura, ['2026001'] * 6)); executor.shutdown()"
```

Observe as seis respostas e os registros do servidor. Esse comando gera seis tarefas concorrentes no `leitor-01`; não representa seis equipamentos distintos nem garante que todas permaneçam em execução ao mesmo tempo.

### Logs após recriar os contêineres

Observe uma linha antiga do arquivo, execute os comandos abaixo e confira se ela continua presente:

```sh
docker compose exec servidor-acesso head -n 5 /app/logs/acessos.log
docker compose down
docker compose up -d
docker compose exec servidor-acesso head -n 5 /app/logs/acessos.log
```

Use a mesma pasta e o mesmo nome de projeto Compose para reutilizar o volume. `docker compose down -v` remove também o volume e apaga o histórico; use essa opção somente se quiser zerar os dados.

## 8. Configuração e monitoramento do Linux

Execute os comandos abaixo com os serviços em funcionamento e explique o resultado durante a apresentação:

| O que verificar | Comando |
|---|---|
| Interface e IP do servidor | `docker compose exec servidor-acesso ip addr` |
| Rede e gateway | `docker compose exec servidor-acesso ip route` |
| Porta TCP em escuta | `docker compose exec servidor-acesso ss -lnt` |
| Resolução do nome do servidor | `docker compose exec leitor-01 getent hosts servidor-acesso` |
| Conectividade do leitor ao servidor | `docker compose exec leitor-01 ping -c 3 servidor-acesso` |
| Usuário sem root | `docker compose exec servidor-acesso id` |
| Permissões dos logs | `docker compose exec servidor-acesso ls -ld /app/logs /app/logs/acessos.log` |
| Uso de recursos dos contêineres | `docker compose stats --no-stream` |

Os nomes podem receber um prefixo do projeto nas listagens do Docker. Salve as saídas ou capturas de tela para o relatório. O comando `ping` testa conectividade IP; as requisições HTTP verificam também o serviço da aplicação.

## 9. Decisões e limitações

- **HTTP sobre TCP:** oferece mensagens simples de requisição e resposta. TCP entrega um fluxo ordenado e retransmite dados perdidos, mas a comunicação ainda pode falhar; por isso o cliente trata exceções.
- **Threads:** o servidor pode atender vários clientes de forma concorrente. Não é necessário implementar processos ou comunicação entre threads neste projeto.
- **Token:** demonstra autenticação básica. É um valor didático compartilhado e está no código; quem conhece esse valor pode enviar requisições. HTTP não criptografa a matrícula nem o token.
- **Permissões:** a aplicação executa como `appuser`, sem privilégios de root. Isso reduz seus privilégios dentro do contêiner.
- **Falhas:** o timeout é de dois segundos. O cliente espera quatro segundos antes do próximo ciclo, que sorteia uma nova matrícula. Não há fila nem garantia de reenvio da leitura anterior.
- **Histórico:** o volume preserva o arquivo ao recriar os contêineres. O log registra tentativas e decisões de autorização, sem confirmar passagem física, entrada ou saída de pessoas.
- **Cadastro:** as três matrículas estão no dicionário `AUTORIZADOS`. Para alterá-las, edite o servidor e reconstrua a imagem.
- **Escopo:** trata-se de uma simulação acadêmica. Não há hardware, painel, criptografia TLS nem regras específicas de autorização por porta.

## 10. Problemas comuns

| Sintoma | O que conferir |
|---|---|
| Docker não responde | Abra o Docker Desktop ou verifique se o serviço Docker está iniciado. |
| Compose não encontra configuração | Execute os comandos na pasta que contém `compose.yaml`. |
| Porta `8080` ocupada | Pare o serviço que a utiliza ou troque apenas a porta do hospedeiro, por exemplo para `127.0.0.1:8081:8080`; nesse caso use `8081` nos testes pelo computador. |
| Sub-rede em conflito | Verifique `docker network ls` e as redes já existentes. Se precisar alterar a rede do projeto, ajuste conjuntamente sub-rede, gateway e os três IPs no Compose. |
| Código alterado sem efeito | Execute `docker compose up --build -d`. |
| Erro na primeira consulta | O servidor pode ainda estar iniciando; o cliente tenta novamente no ciclo seguinte. |
| Navegador mostra `501` | A aplicação recebe `POST /validar`; não implementa `GET` ou painel. |


Referências técnicas para estudo: [servidor HTTP do Python](https://docs.python.org/3.11/library/http.server.html), [urllib.request](https://docs.python.org/3.11/library/urllib.request.html), [logging](https://docs.python.org/3.11/library/logging.html), [redes do Docker](https://docs.docker.com/engine/network/) e [volumes](https://docs.docker.com/engine/storage/volumes/).
