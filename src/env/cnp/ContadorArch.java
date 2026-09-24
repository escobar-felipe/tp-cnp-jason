package cnp;

import jason.architecture.AgArch;
import jason.asSemantics.Message;

import java.util.concurrent.atomic.AtomicLong;

public class ContadorArch extends AgArch {

    public static final AtomicLong MENSAGENS = new AtomicLong();

    @Override
    public void sendMsg(Message m) throws Exception {
        MENSAGENS.incrementAndGet();
        super.sendMsg(m);
    }
}
