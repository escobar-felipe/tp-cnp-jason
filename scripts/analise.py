#!/usr/bin/env python3
"""Calcula as metricas de todas as execucoes em results/.

Uso:  python3 scripts/analise.py

Le as pastas results/n{N}_m{M}_i{I}_r{REP}/ e gera:
  results/metricas_execucoes.csv  uma linha por execucao
  results/metricas_cenarios.csv   media e desvio das repeticoes de cada cenario
  results/vitorias_estrategia.csv contratos ganhos por estrategia de preco (criterio de comparacao)
  results/graficos/*.png          um grafico por bloco (so se o matplotlib estiver instalado)

So usa a biblioteca padrao para as metricas. Os graficos precisam de matplotlib:
  python3 -m venv .venv && .venv/bin/pip install matplotlib && .venv/bin/python scripts/analise.py
"""

import csv
import glob
import os
import re
import statistics
from collections import defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(RAIZ, "results")
FINAIS = {"concluida", "sem_proposta", "falha", "timeout_resultado"}
PASTA = re.compile(r"n(\d+)_m(\d+)_i(\d+)_r(\d+)$")
ESTRATEGIA = {
    0: "fixa",
    1: "agressiva",
    2: "aleatoria",
}  # num mod 3, como no participant.asl

# blocos do passo 8: (parametro que varia, valores fixos dos outros)
BLOCOS = {
    "n": {"m": 10, "i": 3},
    "m": {"n": 50, "i": 3},
    "i": {"n": 50, "m": 10},
}


def ler_kv(arq):
    with open(arq) as f:
        return dict(l.strip().split("=", 1) for l in f if "=" in l)


def analisar_execucao(pasta, n, m, i, rep):
    st = ler_kv(os.path.join(pasta, "status.txt"))
    eventos = []
    arq = os.path.join(pasta, "eventos.csv")
    if os.path.exists(arq):
        with open(arq) as f:
            eventos = list(csv.DictReader(f))

    abertura, fim, estado = {}, {}, {}
    vitorias = defaultdict(int)
    for e in eventos:
        t, cid = int(e["tempo_ms"]), e["cid"]
        if e["evento"] == "aberta":
            abertura[cid] = t
        elif e["evento"] in FINAIS:
            fim[cid], estado[cid] = t, e["evento"]
            if e["evento"] == "concluida" and e["participante"]:
                num = int(e["participante"].replace("participant", ""))
                vitorias[ESTRATEGIA[num % 3]] += 1

    esperadas = n * i
    concluidas = sum(1 for s in estado.values() if s == "concluida")
    lat = [fim[c] - abertura[c] for c in fim if c in abertura]
    tempo_total = (
        (max(fim.values()) - min(abertura.values())) if fim and abertura else None
    )

    msgs = ""
    arq = os.path.join(pasta, "resumo.csv")
    if os.path.exists(arq):
        with open(arq) as f:
            msgs = int(next(csv.DictReader(f))["mensagens"])

    return {
        "n": n,
        "m": m,
        "i": i,
        "rep": rep,
        "status": st.get("status", "?"),
        "negociacoes_esperadas": esperadas,
        "negociacoes_finalizadas": len(fim),
        "concluidas": concluidas,
        "sem_proposta": sum(1 for s in estado.values() if s == "sem_proposta"),
        "timeout_resultado": sum(
            1 for s in estado.values() if s == "timeout_resultado"
        ),
        "taxa_sucesso": round(
            concluidas / esperadas, 4
        ),  # faltantes contam como insucesso
        "tempo_total_ms": tempo_total if tempo_total is not None else "",
        "latencia_media_ms": round(statistics.mean(lat), 1) if lat else "",
        "latencia_max_ms": max(lat) if lat else "",
        "vazao_por_s": (
            round(concluidas / (tempo_total / 1000), 2) if tempo_total else ""
        ),
        "mensagens": msgs,
        "mensagens_formula": n * i * (3 * m + 1),
        "memoria_max_mb": (
            round(int(st["memoria_max_bytes"]) / 2**20, 1)
            if st.get("memoria_max_bytes")
            else ""
        ),
        "duracao_processo_s": st.get("duracao_s", ""),
    }, vitorias


def media_desvio(vals):
    vals = [v for v in vals if v != ""]
    if not vals:
        return "", ""
    return round(statistics.mean(vals), 2), (
        round(statistics.stdev(vals), 2) if len(vals) > 1 else 0
    )


def main():
    execucoes, vit_cenario = [], defaultdict(lambda: defaultdict(int))
    for pasta in sorted(glob.glob(os.path.join(RES, "n*_m*_i*_r*"))):
        m_ = PASTA.search(pasta)
        if not m_ or not os.path.exists(os.path.join(pasta, "status.txt")):
            continue
        n, m, i, rep = map(int, m_.groups())
        linha, vit = analisar_execucao(pasta, n, m, i, rep)
        execucoes.append(linha)
        for k, v in vit.items():
            vit_cenario[(n, m, i)][k] += v

    if not execucoes:
        print(
            "nenhuma execucao em results/n*_m*_i*_r*/ -- rode scripts/matriz.sh antes"
        )
        return

    with open(os.path.join(RES, "metricas_execucoes.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(execucoes[0]))
        w.writeheader()
        w.writerows(execucoes)

    grupos = defaultdict(list)
    for e in execucoes:
        grupos[(e["n"], e["m"], e["i"])].append(e)
    METRICAS = [
        "tempo_total_ms",
        "latencia_media_ms",
        "latencia_max_ms",
        "vazao_por_s",
        "taxa_sucesso",
        "mensagens",
        "memoria_max_mb",
    ]
    cenarios = []
    for (n, m, i), es in sorted(grupos.items()):
        c = {
            "n": n,
            "m": m,
            "i": i,
            "repeticoes": len(es),
            "execucoes_ok": sum(1 for e in es if e["status"] == "ok"),
            "mensagens_formula": es[0]["mensagens_formula"],
        }
        for met in METRICAS:
            c[met + "_media"], c[met + "_desvio"] = media_desvio([e[met] for e in es])
        cenarios.append(c)
    with open(os.path.join(RES, "metricas_cenarios.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cenarios[0]))
        w.writeheader()
        w.writerows(cenarios)

    with open(os.path.join(RES, "vitorias_estrategia.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["n", "m", "i", "fixa", "agressiva", "aleatoria"])
        for (n, m, i), v in sorted(vit_cenario.items()):
            w.writerow([n, m, i, v["fixa"], v["agressiva"], v["aleatoria"]])

    print(f"{len(execucoes)} execucoes, {len(cenarios)} cenarios")
    print(
        "gravado: results/metricas_execucoes.csv, metricas_cenarios.csv, vitorias_estrategia.csv"
    )
    graficos(cenarios)


def graficos(cenarios):
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print(
            "graficos: matplotlib nao instalado, pulei. Veja o topo deste arquivo para instalar."
        )
        return
    os.makedirs(os.path.join(RES, "graficos"), exist_ok=True)
    for par, fixos in BLOCOS.items():
        pts = sorted(
            (c for c in cenarios if all(c[k] == v for k, v in fixos.items())),
            key=lambda c: c[par],
        )
        if len(pts) < 2:
            continue
        xs = [c[par] for c in pts]
        fig, eixos = plt.subplots(1, 3, figsize=(15, 4))
        for ax, (met, rot) in zip(
            eixos,
            [
                ("tempo_total_ms", "tempo total (ms)"),
                ("latencia_media_ms", "latencia media (ms)"),
                ("vazao_por_s", "vazao (concluidas/s)"),
            ],
        ):
            ys = [c[met + "_media"] for c in pts]
            es = [c[met + "_desvio"] or 0 for c in pts]
            ax.errorbar(xs, ys, yerr=es, marker="o", capsize=4)
            ax.set_xlabel(par)
            ax.set_ylabel(rot)
            ax.grid(alpha=0.3)
        fixo_txt = ", ".join(f"{k}={v}" for k, v in fixos.items())
        fig.suptitle(f"Variando {par} ({fixo_txt})")
        fig.tight_layout()
        arq = os.path.join(RES, "graficos", f"variando_{par}.png")
        fig.savefig(arq, dpi=120)
        plt.close(fig)
        print("grafico:", os.path.relpath(arq, RAIZ))


if __name__ == "__main__":
    main()
