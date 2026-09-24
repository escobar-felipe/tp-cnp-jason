# Contract Net Protocol em Jason

Implementação do Contract Net Protocol (CNP) com agentes BDI em Jason 3.3 (AgentSpeak). Há dois papéis: *initiators*, que contratam um serviço, e *participants*, que fazem propostas. Cada initiator conduz várias negociações ao mesmo tempo.

## Requisitos

- Java 21
- Python 3 (apenas para os testes e a análise)

O Gradle não precisa estar instalado: o `gradlew` baixa a versão 8.10 na primeira execução, e o Gradle baixa o Jason.

## Como rodar

```sh
./gradlew run
```

Roda o cenário definido em `cnp.mas2j` e termina sozinho quando todas as negociações acabam. O log sai no terminal, e os resultados ficam em `results/eventos.csv` e `results/resumo.csv`.

Para mudar o cenário, altere os três números do `cnp.mas2j`, que precisam concordar entre si:

```
environment: cnp.CnpEnv(n, i, m)
initiator   [beliefs="tarefas(i)"] ... #n;
participant                        ... #m;
```

onde `n` é o número de initiators, `m` o de participants e `i` o de negociações simultâneas por initiator.

O `./run.sh` faz o mesmo que o `./gradlew run`, sem passar pelo Gradle, e é o que os scripts usam. Ele depende do cache criado por um `./gradlew classes` executado ao menos uma vez.

## Testes

```sh
python3 scripts/testes.py
```

Roda seis cenários e confere o resultado de cada um: escolha do menor preço, negociações em paralelo, recusa de todos, participant que não responde, vencedor que não entrega e um cenário com 150 negociações. Também confere se o número de mensagens bate com `n × i × (3m + 1)`.

## Experimentos

```sh
scripts/matriz.sh            # todos os cenários, 3 repetições
python3 scripts/analise.py   # métricas a partir de results/
```

`scripts/rodar.sh N M I REP` roda um único cenário e guarda o resultado em `results/nN_mM_iI_rREP/`. A matriz pula cenários que já foram rodados, então pode ser interrompida e retomada.

## Estrutura

```
cnp.mas2j                  configuração do sistema (agentes e ambiente)
src/agt/initiator.asl      agente que contrata
src/agt/participant.asl    agente que faz propostas
src/env/cnp/CnpEnv.java    ambiente: registra os eventos e encerra a execução
scripts/                   testes, experimentos e análise
relatorio/                 relatório do trabalho
```

