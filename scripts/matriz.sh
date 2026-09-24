#!/bin/sh
# Roda todos os cenarios do passo 8 do PLANO.md, REPS vezes cada.
# Varia um parametro de cada vez; 50/10/3 aparece em tres blocos e roda uma vez so.
#
# Uso:  scripts/matriz.sh            (3 repeticoes)
#       REPS=1 scripts/matriz.sh     (rodada rapida)
#
# Cenarios que ja tem status=ok sao pulados, entao da para interromper e retomar.

cd "$(dirname "$0")/.." || exit 1
REPS=${REPS:-3}

CENARIOS="
2 10 3
10 10 3
50 10 3
100 10 3
199 10 3
50 2 3
50 5 3
50 25 3
50 49 3
50 10 1
50 10 5
50 10 9
199 49 9
"

echo "$CENARIOS" | while read -r N M I; do
    [ -z "$N" ] && continue
    REP=1
    while [ "$REP" -le "$REPS" ]; do
        DIR="results/n${N}_m${M}_i${I}_r${REP}"
        if grep -q "status=ok" "$DIR/status.txt" 2>/dev/null; then
            echo "n=$N m=$M i=$I rep=$REP -> ja feito, pulando"
        else
            scripts/rodar.sh "$N" "$M" "$I" "$REP"
        fi
        REP=$((REP + 1))
    done
done

echo
echo "=== resumo da matriz ==="
for S in results/n*_m*_i*_r*/status.txt; do
    printf "%-28s %s\n" "$(basename "$(dirname "$S")")" "$(grep status= "$S")"
done
