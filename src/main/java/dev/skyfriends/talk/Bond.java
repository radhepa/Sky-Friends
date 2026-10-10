package dev.skyfriends.talk;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

/**
 * What one Cirri knows of one player: friendship points, whether they have met, what was talked about and given
 * today, when the player last hurt them and how much of a grudge they still hold (it fades a step each day, or
 * with an apology or a gift they love), and what they remember: flags ({@code a:likes:aure} an answer you gave,
 * {@code q:<id>} a question answered, {@code asking:<id>} the one on the table, {@code offer:<id>:<day>} an offer
 * made today) and the lines they said to you lately, so they don't repeat themselves.
 */
public final class Bond {
    public static final int MAX_GRUDGE = 5, RECENT = 40;

    public static final Codec<Bond> CODEC = RecordCodecBuilder.create(i -> i.group(
        Codec.INT.optionalFieldOf("points", 0).forGetter(b -> b.points),
        Codec.BOOL.optionalFieldOf("met", false).forGetter(b -> b.met),
        Codec.LONG.optionalFieldOf("day", -1L).forGetter(b -> b.day),
        Codec.STRING.listOf().optionalFieldOf("topics", List.of()).forGetter(b -> new ArrayList<>(b.topics)),
        Codec.INT.optionalFieldOf("gifts", 0).forGetter(b -> b.gifts),
        Codec.BOOL.optionalFieldOf("greeted", false).forGetter(b -> b.greeted),
        Codec.LONG.optionalFieldOf("hurt_until", 0L).forGetter(b -> b.hurtUntil),
        Codec.INT.optionalFieldOf("grudge", 0).forGetter(b -> b.grudge),
        Codec.BOOL.optionalFieldOf("apologized", false).forGetter(b -> b.apologized),
        Codec.STRING.listOf().optionalFieldOf("flags", List.of()).forGetter(b -> new ArrayList<>(b.flags)),
        Codec.STRING.listOf().optionalFieldOf("recent", List.of()).forGetter(b -> new ArrayList<>(b.recent)),
        Codec.LONG.optionalFieldOf("brought", -1L).forGetter(b -> b.brought),
        Codec.LONG.optionalFieldOf("waved", -1L).forGetter(b -> b.waved)
    ).apply(i, Bond::new));

    public int points;
    public boolean met;
    /** The day (overworld days since the world began) the daily counts below belong to. */
    public long day;
    public final Set<String> topics;
    public int gifts;
    public boolean greeted;
    public long hurtUntil;
    /** Blows not yet made up for; while there is one they won't stay to talk. */
    public int grudge;
    /** Said sorry today. */
    public boolean apologized;
    public final Set<String> flags;
    public final LinkedHashSet<String> recent;
    /** The last day they brought you a present, and the last day they waved you over. */
    public long brought, waved;

    public Bond() {
        this(0, false, -1L, List.of(), 0, false, 0L, 0, false, List.of(), List.of(), -1L, -1L);
    }

    private Bond(int points, boolean met, long day, List<String> topics, int gifts, boolean greeted, long hurtUntil, int grudge,
                 boolean apologized, List<String> flags, List<String> recent, long brought, long waved) {
        this.points = points;
        this.met = met;
        this.day = day;
        this.topics = new HashSet<>(topics);
        this.gifts = gifts;
        this.greeted = greeted;
        this.hurtUntil = hurtUntil;
        this.grudge = grudge;
        this.apologized = apologized;
        this.flags = new LinkedHashSet<>(flags);
        this.recent = new LinkedHashSet<>(recent);
        this.brought = brought;
        this.waved = waved;
    }

    /** Starts a new day's counts when the day has turned. Offers made on earlier days are forgotten. */
    public void today(long today) {
        if (day == today) return;
        if (day >= 0 && today > day) grudge = (int) Math.max(0, grudge - Math.min(MAX_GRUDGE, today - day));
        day = today;
        topics.clear();
        gifts = 0;
        greeted = false;
        apologized = false;
        flags.removeIf(f -> f.startsWith("offer:") && !f.endsWith(":" + today));
    }

    public int level() {
        return Friendship.level(points);
    }

    public boolean has(String flag) {
        return flags.contains(flag);
    }

    public void flag(String flag) {
        flags.add(flag);
    }

    public void unflag(String flag) {
        flags.remove(flag);
    }

    /** Remembers a line they said, so it isn't said again soon. */
    public void said(String id) {
        recent.remove(id);
        recent.add(id);
        while (recent.size() > RECENT) recent.remove(recent.iterator().next());
    }

    /** The question on the table, if any. */
    public String asking() {
        for (String f : flags) if (f.startsWith("asking:")) return f.substring(7);
        return "";
    }

    public void stopAsking() {
        flags.removeIf(f -> f.startsWith("asking:"));
    }
}
