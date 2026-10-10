package dev.skyfriends.life;

import dev.skyfriends.entity.Cirri;
import dev.skyfriends.talk.TalkWorld;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Random;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import org.jspecify.annotations.Nullable;

/**
 * What the Cirri say about their village and each other: the news (from the {@link Chronicle}, with real
 * names), the one they love (from {@link Kin}), and a word about a neighbour now and then. The lines are in the
 * dialogue bank ({@code news.*}, {@code heart.*}, {@code mention.*}).
 */
public final class Gossip {
    private static final Random RANDOM = new Random();
    /** How far back news still counts. */
    private static final int DAYS = 7;

    private Gossip() {}

    /** "Any news?": something that has happened lately (not the player's own doings), or that all is quiet. */
    public static String news(Cirri c, ServerPlayer p) {
        if (!(c.level() instanceof ServerLevel level) || !c.settled() && !c.isBaby()) return orQuiet(c, p, null);
        String me = p.getName().getString();
        var news = new ArrayList<Chronicle.News>();
        for (var n : Chronicle.recent(level, c.home(), c.dayNumber(), DAYS)) {
            // what you did yourself isn't news to you, and nobody brings up their own sorrow as gossip
            if (n.other().equals(me) || n.kind().equals("visitor") && n.who().equals(me) || n.who().equals(c.firstName())) continue;
            news.add(n);
        }
        // the newest first, mostly; now and then something from a few days ago
        Chronicle.News pick = news.isEmpty() ? null : news.get(RANDOM.nextInt(4) == 0 ? RANDOM.nextInt(news.size()) : 0);
        return orQuiet(c, p, pick);
    }

    private static String orQuiet(Cirri c, ServerPlayer p, Chronicle.@Nullable News n) {
        if (n != null) {
            String said = TalkWorld.say(c, p, "news." + n.kind(), Map.of("who", n.who(), "other", n.other()));
            if (said != null) return said;
        }
        String quiet = TalkWorld.say(c, p, "news.none");
        return quiet != null ? quiet : "A quiet sky lately. The best kind.";
    }

    /** "Anyone special?": the one they share their nest with, someone they're sweet on, their children, or no one yet. */
    public static String heart(Cirri c, ServerPlayer p) {
        var village = Kin.village(c);
        List<String> pools = new ArrayList<>();
        if (Kin.partner(c) != null) pools.add("heart.partner");
        else if (Kin.crush(c, village) != null) pools.add("heart.crush");
        else pools.add("heart.single");
        if (!Kin.children(c, village).isEmpty() && RANDOM.nextBoolean()) pools.addFirst("heart.parent");
        for (String pool : pools) {
            String said = TalkWorld.say(c, p, pool);
            if (said != null) return said;
        }
        return "The sky is wide. My heart's still deciding where to drift.";
    }

    /** A sentence about someone in the village to add after a chat or work line, or "" if nothing fits. */
    public static String mention(Cirri c, ServerPlayer p, String topic) {
        List<String> pools = new ArrayList<>(topic.equals("work") ? List.of("mention.coworker", "mention.friend")
                : List.of("mention.partner", "mention.child", "mention.friend", "mention.neighbour", "mention.coworker"));
        java.util.Collections.shuffle(pools, RANDOM);
        for (String pool : pools) {
            String said = TalkWorld.say(c, p, pool);
            if (said != null) return said;
        }
        return "";
    }
}
