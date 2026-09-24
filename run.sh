#!/bin/sh
# Compila o ambiente Java e roda o MAS, sem passar pelo Gradle.
#
# Faz o mesmo que "./gradlew run", porem mais rapido, e aceita outro arquivo
# de projeto (MAS=...), por isso e o que os scripts de experimento usam.
#
# Uso:  ./run.sh              -> log no terminal
#       ./run.sh --debug      -> abre tambem o Mind Inspector de cada agente
#       MAS=outro.mas2j ./run.sh   -> roda outro arquivo de projeto (usado pelos scripts)

cd "$(dirname "$0")" || exit 1

CACHE="$HOME/.gradle/caches/modules-2/files-2.1"

jar() {
    find "$CACHE" -name "$1" 2>/dev/null | head -1
}

CP="build/classes/java/main:build/resources/main"
for NAME in jason-interpreter-3.3.0.jar jade-4.3.jar javax.json-api-1.1.4.jar javax.json-1.1.4.jar; do
    FOUND=$(jar "$NAME")
    [ -n "$FOUND" ] && CP="$CP:$FOUND"
done

# compila o ambiente (src/env) antes de subir o MAS
mkdir -p build/classes/java/main
if ! javac -cp "$CP" -d build/classes/java/main src/env/cnp/*.java; then
    echo "ERRO de compilacao no ambiente Java. MAS nao foi iniciado."
    exit 1
fi

exec java -cp "$CP" jason.infra.local.RunLocalMAS "${MAS:-cnp.mas2j}" "$@"
