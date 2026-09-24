// ========================== Regras ==========================

servico_alvo(S)         :- pedir(S).
servico_alvo(servico_a) :- not pedir(_).

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
      +estado(Cid, coletando);
      registrar(aberta, Cid);
      .send(Ps, tell, cfp(Cid, S));
      .wait(2000);
      !decidir(Cid).

@decidir[atomic]
+!decidir(Cid) : estado(Cid, coletando)
   <- .findall(of(P, A), propose(Cid, P)[source(A)], L);
      !escolher(Cid, L).
+!decidir(_).

+!escolher(Cid, [])
   <- !mudar_estado(Cid, sem_proposta);
      registrar(sem_proposta, Cid).

+!escolher(Cid, L)
   <- .min(L, of(Preco, W));
      .print(Cid, " propostas ", L, " -> vencedor ", W, " por ", Preco);
      +vencedor(Cid, W, Preco);
      !mudar_estado(Cid, esperando);
      .send(W, tell, accept_proposal(Cid));
      for (.member(of(_, A), L) & A \== W) {
         .send(A, tell, reject_proposal(Cid))
      };
      !!esperar_resultado(Cid).

+!esperar_resultado(Cid)
   <- .wait(5000);
      !expirar(Cid).

@expirar[atomic]
+!expirar(Cid) : estado(Cid, esperando)
   <- !mudar_estado(Cid, timeout_resultado);
      registrar(timeout_resultado, Cid).
+!expirar(_).

@done[atomic]
+inform_done(Cid)[source(W)] : vencedor(Cid, W, Preco) & estado(Cid, esperando)
   <- !mudar_estado(Cid, concluida);
      registrar(concluida, Cid, W, Preco).

+!mudar_estado(Cid, Novo)
   <- -estado(Cid, _);
      +estado(Cid, Novo).
