package cnp;

import jason.asSyntax.*;
import jason.environment.*;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.logging.*;

public class CnpEnv extends Environment {

    private static final Set<String> FINAIS =
            Set.of("concluida", "sem_proposta", "falha", "timeout_resultado");

    private Logger logger = Logger.getLogger("cnp." + CnpEnv.class.getName());

    private int n, i, m, esperadas;
    private int finais = 0;
    private long primeiraAberta = -1, ultimoFinal = -1;
    private final Map<String, Integer> contagem = new TreeMap<>();
    private PrintWriter eventos;

    @Override
    public void init(String[] args) {
        super.init(args);
        n = Integer.parseInt(args[0].trim());
        i = Integer.parseInt(args[1].trim());
        m = args.length > 2 ? Integer.parseInt(args[2].trim()) : -1;
        esperadas = n * i;
        for (String f : FINAIS) contagem.put(f, 0);
        try {
            Files.createDirectories(Paths.get("results"));
            eventos = new PrintWriter(new FileWriter("results/eventos.csv"));
            eventos.println("tempo_ms,agente,evento,cid,participante,preco");
        } catch (IOException e) {
            throw new RuntimeException("nao consegui criar results/eventos.csv", e);
        }
        logger.info("n=" + n + " i=" + i + " -> esperando " + esperadas + " negociacoes");
    }

    @Override
    public boolean executeAction(String ag, Structure action) {
        if (!action.getFunctor().equals("registrar") || action.getArity() < 2) {
            logger.warning("acao desconhecida: " + action);
            return false;
        }
        String evento = action.getTerm(0).toString();
        String cid    = action.getTerm(1).toString();
        String part   = action.getArity() > 2 ? action.getTerm(2).toString() : "";
        String preco  = action.getArity() > 3 ? action.getTerm(3).toString() : "";
        registrar(ag, evento, cid, part, preco);
        return true;
    }

    private synchronized void registrar(String ag, String evento,
                                       String cid, String part, String preco) {
        long t = System.currentTimeMillis();
        eventos.printf("%d,%s,%s,\"%s\",%s,%s%n", t, ag, evento, cid, part, preco);

        if (evento.equals("aberta") && primeiraAberta < 0) primeiraAberta = t;

        if (FINAIS.contains(evento)) {
            contagem.merge(evento, 1, Integer::sum);
            finais++;
            ultimoFinal = t;
            if (finais == esperadas) encerrar();
        }
    }

    private void encerrar() {
        eventos.close();
        long msgs = ContadorArch.MENSAGENS.get();
        try (PrintWriter r = new PrintWriter(new FileWriter("results/resumo.csv"))) {
            r.println("n,m,i,negociacoes,concluida,sem_proposta,falha,timeout_resultado,mensagens,tempo_total_ms");
            r.printf("%d,%s,%d,%d,%d,%d,%d,%d,%d,%d%n",
                    n, m < 0 ? "" : String.valueOf(m), i, finais,
                    contagem.get("concluida"), contagem.get("sem_proposta"),
                    contagem.get("falha"), contagem.get("timeout_resultado"),
                    msgs, ultimoFinal - primeiraAberta);
        } catch (IOException e) {
            logger.severe("nao consegui gravar results/resumo.csv: " + e);
        }
        logger.info("FIM: " + finais + " negociacoes " + contagem + ", " + msgs
                + " mensagens, " + (ultimoFinal - primeiraAberta) + " ms");
        System.exit(0);
    }
}
