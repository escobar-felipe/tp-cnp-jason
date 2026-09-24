#!/usr/bin/env python3
"""Passo 6 do PLANO.md: roda os cenarios de teste e confere o esperado.

Uso:  python3 scripts/testes.py            (todos)
      python3 scripts/testes.py 1 3        (so os testes 1 e 3)

Cada teste roda via scripts/rodar.sh e guarda a saida em results/testes/<nome>/.
O resultado geral vai para results/testes/resultado.txt.
"""
import csv
import os
import re
import subprocess
import sys
from collections import defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "results", "testes")


def rodar(nome, n, m, i, extra_ini="", extra_part=""):
    saida = os.path.join("results", "testes", nome)
    env = dict(os.environ, SAIDA=saida, LOG="logging.properties",
               EXTRA_INI=extra_ini, EXTRA_PART=extra_part, LIMITE="120")
    subprocess.run(["scripts/rodar.sh", str(n), str(m), str(i), "1"],
                   cwd=RAIZ, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return os.path.join(RAIZ, saida)


def ler(pasta):
    """Devolve (resumo, eventos, linhas do log)."""
    resumo = {}
    arq = os.path.join(pasta, "resumo.csv")
    if os.path.exists(arq):
        with open(arq) as f:
            resumo = {k: int(v) if v.isdigit() else v for k, v in next(csv.DictReader(f)).items()}
    eventos = []
    arq = os.path.join(pasta, "eventos.csv")
    if os.path.exists(arq):
        with open(arq) as f:
            eventos = list(csv.DictReader(f))
    with open(os.path.join(pasta, "saida.log")) as f:
        log = f.read().splitlines()
    return resumo, eventos, log


DECISAO = re.compile(r"propostas \[(.*)\] -> vencedor (\w+) por (\d+)")
OFERTA = re.compile(r"of\((\d+),(\w+)\)")


def decisoes(log):
    """Para cada linha de decisao do initiator: (ofertas, vencedor, preco)."""
    out = []
    for linha in log:
        d = DECISAO.search(linha)
        if d:
            ofertas = [(int(p), a) for p, a in OFERTA.findall(d.group(1))]
            out.append((ofertas, d.group(2), int(d.group(3))))
    return out


def checar(cond, msg, falhas):
    if not cond:
        falhas.append(msg)


def vencedor_e_o_menor(log, falhas):
    ds = decisoes(log)
    checar(ds, "nenhuma decisao encontrada no log", falhas)
    for ofertas, venc, preco in ds:
        checar(min(ofertas) == (preco, venc),
               f"vencedor errado: {venc} por {preco}, mas o menor era {min(ofertas)}", falhas)


def cada_cid_uma_vez(eventos, esperado, falhas):
    FINAIS = {"concluida", "sem_proposta", "falha", "timeout_resultado"}
    abertas, finais = defaultdict(int), defaultdict(int)
    for e in eventos:
        if e["evento"] == "aberta":
            abertas[e["cid"]] += 1
        elif e["evento"] in FINAIS:
            finais[e["cid"]] += 1
    checar(len(abertas) == esperado, f"{len(abertas)} negociacoes abertas, esperado {esperado}", falhas)
    checar(set(abertas) == set(finais), "ha negociacao aberta sem estado final (ou o contrario)", falhas)
    duplas = [c for c, k in list(abertas.items()) + list(finais.items()) if k != 1]
    checar(not duplas, f"eventos duplicados em {sorted(set(duplas))[:5]}", falhas)


def msgs_formula(resumo, n, m, i, falhas):
    esperado = n * i * (3 * m + 1)
    checar(resumo.get("mensagens") == esperado,
           f"{resumo.get('mensagens')} mensagens, formula n*i*(3m+1) = {esperado}", falhas)


# ---------------------------------------------------------------- testes

def t1():
    """Normal (2,2,1): 2 concluidas, vencedor = menor preco."""
    r, e, log = ler(rodar("1_normal", 2, 2, 1))
    f = []
    checar(r.get("concluida") == 2, f"concluida={r.get('concluida')}, esperado 2", f)
    vencedor_e_o_menor(log, f)
    msgs_formula(r, 2, 2, 1, f)
    return f


def t2():
    """Paralelo (2,2,3): 6 negociacoes, as 3 de cada initiator abertas antes da 1a terminar."""
    r, e, log = ler(rodar("2_paralelo", 2, 2, 3))
    f = []
    checar(r.get("concluida") == 6, f"concluida={r.get('concluida')}, esperado 6", f)
    cada_cid_uma_vez(e, 6, f)
    for ini in ("initiator1", "initiator2"):
        evs = [x for x in e if x["agente"] == ini]
        primeiro_final = next((k for k, x in enumerate(evs) if x["evento"] != "aberta"), len(evs))
        abertas_antes = sum(1 for x in evs[:primeiro_final] if x["evento"] == "aberta")
        checar(abertas_antes == 3, f"{ini}: {abertas_antes} abertas antes do 1o final, esperado 3", f)
    vencedor_e_o_menor(log, f)
    msgs_formula(r, 2, 2, 3, f)
    return f


def t3():
    """Todos recusam (initiator pede servico_b): sem_proposta."""
    r, e, log = ler(rodar("3_todos_recusam", 2, 2, 1, extra_ini="pedir(servico_b)"))
    f = []
    checar(r.get("sem_proposta") == 2, f"sem_proposta={r.get('sem_proposta')}, esperado 2", f)
    checar(r.get("concluida") == 0, f"concluida={r.get('concluida')}, esperado 0", f)
    # cfp para m + refuse de m = 2m por negociacao
    checar(r.get("mensagens") == 2 * 1 * 2 * 2, f"{r.get('mensagens')} mensagens, esperado 8", f)
    return f


def t4():
    """Um participant nao responde (participant1 mudo): contrata o outro apos o prazo."""
    r, e, log = ler(rodar("4_um_nao_responde", 2, 2, 1, extra_part="silencioso(1)"))
    f = []
    checar(r.get("concluida") == 2, f"concluida={r.get('concluida')}, esperado 2", f)
    venc = {x["participante"] for x in e if x["evento"] == "concluida"}
    checar(venc == {"participant2"}, f"vencedores {venc}, esperado so participant2", f)
    return f


def t5():
    """Vencedor nao entrega (nenhum participant entrega): timeout_resultado."""
    r, e, log = ler(rodar("5_vencedor_nao_entrega", 2, 2, 1, extra_part="nao_entrega(1), nao_entrega(2)"))
    f = []
    checar(r.get("timeout_resultado") == 2,
           f"timeout_resultado={r.get('timeout_resultado')}, esperado 2", f)
    checar(r.get("concluida") == 0, f"concluida={r.get('concluida')}, esperado 0", f)
    return f


def t6():
    """Grande (50,10,3): 150 estados finais, nenhum faltando nem duplicado."""
    r, e, log = ler(rodar("6_grande", 50, 10, 3))
    f = []
    checar(r.get("negociacoes") == 150, f"negociacoes={r.get('negociacoes')}, esperado 150", f)
    checar(r.get("concluida") == 150, f"concluida={r.get('concluida')}, esperado 150", f)
    cada_cid_uma_vez(e, 150, f)
    vencedor_e_o_menor(log, f)
    msgs_formula(r, 50, 10, 3, f)
    return f


TESTES = [t1, t2, t3, t4, t5, t6]

if __name__ == "__main__":
    escolhidos = [int(a) for a in sys.argv[1:]] or range(1, len(TESTES) + 1)
    os.makedirs(PASTA, exist_ok=True)
    linhas, total_falhas = [], 0
    for k in escolhidos:
        t = TESTES[k - 1]
        print(f"teste {k}: {t.__doc__.splitlines()[0]} ...", flush=True)
        falhas = t()
        total_falhas += len(falhas)
        status = "PASSOU" if not falhas else "FALHOU"
        linhas.append(f"[{status}] teste {k}: {t.__doc__.splitlines()[0]}")
        linhas += [f"         - {x}" for x in falhas]
        print("   " + status + "".join(f"\n   - {x}" for x in falhas), flush=True)
    with open(os.path.join(PASTA, "resultado.txt"), "w") as arq:
        arq.write("\n".join(linhas) + "\n")
    sys.exit(1 if total_falhas else 0)
