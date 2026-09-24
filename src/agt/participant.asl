// ========================= Crenças ==========================

servico(servico_a).

// ========================== Regras ==========================

num(N) :- .my_name(Me) & .term2string(Me, S) & .delete("participant", S, NS) & .term2string(N, NS).

estrategia(fixa)      :- num(N) & N mod 3 == 0.
estrategia(agressiva) :- num(N) & N mod 3 == 1.
estrategia(aleatoria) :- num(N) & N mod 3 == 2.

mudo      :- num(N) & silencioso(N).
caloteiro :- num(N) & nao_entrega(N).

// ========================== Planos ==========================

+!preco(fixa, P)      <- P = 1000.
+!preco(agressiva, P) <- .random(R); P = 900 + math.floor(R*151).
+!preco(aleatoria, P) <- .random(R); P = 800 + math.floor(R*401).

+cfp(Cid, S)[source(I)] : mudo.

+cfp(Cid, S)[source(I)] : servico(S) & estrategia(E)
   <- !preco(E, P);
      +proposta(Cid, I, P);
      .send(I, tell, propose(Cid, P)).

+cfp(Cid, S)[source(I)]
   <- .send(I, tell, refuse(Cid)).

+accept_proposal(Cid)[source(I)] : proposta(Cid, I, _) & not executando(Cid)
   <- +executando(Cid);
      .wait(100);
      !entregar(Cid, I).

+!entregar(Cid, I) : caloteiro.
+!entregar(Cid, I) <- .send(I, tell, inform_done(Cid)).

+reject_proposal(Cid)[source(I)]
   <- -proposta(Cid, I, _).
