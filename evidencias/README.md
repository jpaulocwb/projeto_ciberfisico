# Evidências

As figuras estão no apêndice do relatório. A tabela de testes contém links para cada figura e sua página.

## Prints originais do Terminal

| Figura | O que mostra | Arquivo |
|---|---|---|
| 2 | Rede, DNS e porta TCP | [Rede](prints/figura_02_rede.png) |
| 3 | Ping, usuário e permissões | [Linux](prints/figura_03_linux.png) |
| 4 | Treze testes automatizados aprovados | [Testes](prints/figura_04_testes.png) |
| 5 | Respostas 200, 403 e 401 | [HTTP](prints/figura_05_http.png) |
| 6 | Validação dos dados e rota | [Validação](prints/figura_06_validacao.png) |
| 7 | Atendimento dos dois leitores | [Leitores](prints/figura_07_leitores.png) |
| 8 | Timeout e recuperação | [Timeout](prints/figura_08_timeout.png) |
| 9 | Servidor parado e retomada | [Recuperação](prints/figura_09_recuperacao.png) |
| 10 | Logs preservados após recriar os contêineres | [Persistência](prints/figura_10_persistencia.png) |
| 11 | Captura do tráfego de rede | [Tráfego](prints/figura_11_trafego.png) |

## Registros complementares

- [Saída dos testes automatizados](logs/testes_automatizados.txt).
- [Histórico de acessos](logs/acessos.log).
- Arquivos [antes](logs/acessos_antes.log) e [depois](logs/acessos_depois.log) da recriação, para conferir a persistência.
- [Captura PCAP](trafego_http.pcap), que pode ser aberta no Wireshark.
- [Leitura textual da captura](logs/trafego_http.txt), de onde vieram as duas linhas transcritas abaixo da Figura 11.

As imagens e os registros são arquivos originais da execução local. Os logs da aplicação usam UTC, três horas à frente do horário local mostrado no Terminal nesta execução.
