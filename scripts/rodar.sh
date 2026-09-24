#!/bin/sh
# Roda UM cenario do CNP e guarda o resultado em results/n{N}_m{M}_i{I}_r{REP}/
#
# Uso:  scripts/rodar.sh N M I REP
#
# Variaveis opcionais:
#   LIMITE=600                      segundos ate matar uma execucao que nao termina
#   LOG=logging.properties          log com os .print (padrao: so avisos e erros)
#   EXTRA_INI="pedir(servico_b)"    crencas extras dos initiators  (testes)
#   EXTRA_PART="silencioso(1)"      crencas extras dos participants (testes)
#   SAIDA=results/outra_pasta       pasta de destino
#
# Na pasta de destino ficam: eventos.csv, resumo.csv (se terminou),
# saida.log (log + memoria medida pelo /usr/bin/time) e status.txt.

set -u
cd "$(dirname "$0")/.." || exit 1

if [ $# -ne 4 ]; then
    echo "uso: $0 N M I REP" >&2
    exit 2
fi
N=$1; M=$2; I=$3; REP=$4
LIMITE=${LIMITE:-600}
if [ -z "${LOG:-}" ]; then
    LOG=build/logging-silencioso.properties
    mkdir -p build
    sed 's/^\.level = INFO$/.level = WARNING/' logging.properties > "$LOG"
fi
SAIDA=${SAIDA:-results/n${N}_m${M}_i${I}_r${REP}}

# --- gera o experimento.mas2j a partir do modelo ---
INI_CRENCAS="tarefas($I)"
[ -n "${EXTRA_INI:-}" ] && INI_CRENCAS="$INI_CRENCAS, $EXTRA_INI"
PART_OPC=""
[ -n "${EXTRA_PART:-}" ] && PART_OPC="[beliefs=\"$EXTRA_PART\"]"

sed -e "s|@N@|$N|g" -e "s|@M@|$M|g" -e "s|@I@|$I|g" \
    -e "s|@INI_CRENCAS@|$INI_CRENCAS|g" -e "s|@PART_OPC@|$PART_OPC|g" \
    scripts/modelo.mas2j > experimento.mas2j

# --- roda, com um vigia que mata a execucao se passar do LIMITE ---
mkdir -p "$SAIDA"
rm -f results/eventos.csv results/resumo.csv
INICIO=$(date +%s)

MAS=experimento.mas2j /usr/bin/time -l ./run.sh --log-conf "$LOG" > "$SAIDA/saida.log" 2>&1 &
PID=$!
( sleep "$LIMITE"; echo "LIMITE de ${LIMITE}s atingido, matando" >> "$SAIDA/saida.log";
  pkill -f "RunLocalMAS experimento.mas2j" ) 2>/dev/null &
VIGIA=$!
wait "$PID"
CODIGO=$?
pkill -P "$VIGIA" 2>/dev/null   # mata o sleep do vigia
kill "$VIGIA" 2>/dev/null
wait "$VIGIA" 2>/dev/null
DURACAO=$(( $(date +%s) - INICIO ))

# --- guarda os resultados ---
[ -f results/eventos.csv ] && mv results/eventos.csv "$SAIDA/"
if [ -f results/resumo.csv ]; then
    mv results/resumo.csv "$SAIDA/"
    STATUS=ok
else
    STATUS=incompleto
fi
MEMORIA=$(grep "maximum resident set size" "$SAIDA/saida.log" | awk '{print $1}')

cat > "$SAIDA/status.txt" <<FIM
status=$STATUS
codigo_saida=$CODIGO
duracao_s=$DURACAO
memoria_max_bytes=${MEMORIA:-}
FIM

echo "n=$N m=$M i=$I rep=$REP -> $STATUS em ${DURACAO}s ($SAIDA)"
[ "$STATUS" = ok ]
