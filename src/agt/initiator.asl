// ========================== Regras ==========================

servico_alvo(S)         :- pedir(S).
servico_alvo(servico_a) :- not pedir(_).

todos_responderam(Cid) :-
    cfps(Cid, NP) &
    .count(propose(Cid, _)[source(_)], NA) &
    .count(refuse(Cid)[source(_)], NR) &
    NA + NR >= NP.

// ===================== Objetivo inicial =====================

!start.

// ========================== Planos ==========================

+!start : tarefas(I)
   <- .wait(1000);
      for (.range(K, 1, I)) {
         !!cnp(K)
      }.

+!cnp(K)
   <- .my_name(Me);
      Cid = c(Me, K);
      ?servico_alvo(S);
      .all_names(Todos);
      .findall(A, .member(A, Todos) & .substring("participant", A), Ps);
      .length(Ps, NP);
      +cfps(Cid, NP);
      +estado(Cid, coletando);
      registrar(aberta, Cid);
      .send(Ps, tell, cfp(Cid, S));
      .wait(2000);
      !decidir(Cid).

+propose(Cid, _) : estado(Cid, coletando) & todos_responderam(Cid)
   <- !decidir(Cid).

+refuse(Cid) : estado(Cid, coletando) & todos_responderam(Cid)
   <- !decidir(Cid).

@decidir[atomic]
+!decidir(Cid) : estado(Cid, coletando)
   <- .findall(of(P, A), propose(Cid, P)[source(A)], L);
      .count(refuse(Cid)[source(_)], NR);
      .length(L, NL);
      ?cfps(Cid, NP);
      T = NP + NL + NR;
      +msgs(Cid, T);
      !escolher(Cid, L).
+!decidir(_).

+!escolher(Cid, [])
   <- !mudar_estado(Cid, sem_proposta);
      ?msgs(Cid, T);
      registrar(sem_proposta, Cid, T).

+!escolher(Cid, L)
   <- .min(L, of(Preco, W));
      .print(Cid, " propostas ", L, " -> vencedor ", W, " por ", Preco);
      +vencedor(Cid, W, Preco);
      !mudar_estado(Cid, esperando);
      .send(W, tell, accept_proposal(Cid));
      for (.member(of(_, A), L) & A \== W) {
         .send(A, tell, reject_proposal(Cid))
      };
      .length(L, NL);
      ?msgs(Cid, T0);
      T = T0 + NL;
      -msgs(Cid, _);
      +msgs(Cid, T);
      !!esperar_resultado(Cid).

+!esperar_resultado(Cid)
   <- .wait(5000);
      !expirar(Cid).

@expirar[atomic]
+!expirar(Cid) : estado(Cid, esperando)
   <- !mudar_estado(Cid, timeout_resultado);
      ?msgs(Cid, T);
      registrar(timeout_resultado, Cid, T).
+!expirar(_).

@done[atomic]
+inform_done(Cid)[source(W)] : vencedor(Cid, W, Preco) & estado(Cid, esperando)
   <- !mudar_estado(Cid, concluida);
      ?msgs(Cid, T0);
      T = T0 + 1;
      registrar(concluida, Cid, W, Preco, T).

+!mudar_estado(Cid, Novo)
   <- -estado(Cid, _);
      +estado(Cid, Novo).
