package dev.skyfriends.talk;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * What one Cirri and one player have been through together: how far into the Cirri's story the player
 * is, which of their requests are done and how it ended, how many different days they have talked, the
 * gifts the player has learned they love or don't, and the memories the Journal shows.
 */
public final class Tale {
    /** Chapters: 0 not yet told, 1 told and first request asked, 2 first request done, 3 confided, 4 ended. */
    public static final int UNTOLD = 0, ASKED = 1, HELPED = 2, CONFIDED = 3, ENDED = 4;
    public static final int MAX_MEMORIES = 40;

    public static final Codec<Tale> CODEC = RecordCodecBuilder.create(i -> i.group(
        Codec.INT.optionalFieldOf("chapter", 0).forGetter(t -> t.chapter),
        Codec.INT.optionalFieldOf("visits", 0).forGetter(t -> t.visits),
        Codec.LONG.optionalFieldOf("visit_day", -1L).forGetter(t -> t.visitDay),
        Codec.LONG.optionalFieldOf("first_day", -1L).forGetter(t -> t.firstDay),
        Codec.STRING.listOf().optionalFieldOf("done", List.of()).forGetter(t -> new ArrayList<>(t.done)),
        Codec.STRING.optionalFieldOf("ending", "").forGetter(t -> t.ending),
        Codec.STRING.listOf().optionalFieldOf("memories", List.of()).forGetter(t -> t.memories),
        Codec.unboundedMap(Codec.STRING, Codec.STRING).optionalFieldOf("tastes", Map.of()).forGetter(t -> t.tastes)
    ).apply(i, Tale::new));

    public int chapter;
    public int visits;
    public long visitDay;
    public long firstDay;
    /** Ids of the story's requests the player has brought. */
    public final Set<String> done;
    /** The ending the player chose, once there is one. */
    public String ending;
    public final List<String> memories;
    /** Item id to loved, liked or disliked, as found out by giving it. */
    public final Map<String, String> tastes;

    public Tale() {
        this(0, 0, -1L, -1L, List.of(), "", List.of(), Map.of());
    }

    private Tale(int chapter, int visits, long visitDay, long firstDay, List<String> done, String ending, List<String> memories,
                 Map<String, String> tastes) {
        this.chapter = chapter;
        this.visits = visits;
        this.visitDay = visitDay;
        this.firstDay = firstDay;
        this.done = new HashSet<>(done);
        this.ending = ending;
        this.memories = new ArrayList<>(memories);
        this.tastes = new HashMap<>(tastes);
    }

    /** Counts a day they talked (once a day). */
    public void visit(long day) {
        if (firstDay < 0) firstDay = day;
        if (visitDay == day) return;
        visitDay = day;
        visits++;
    }

    /** Writes a memory for the Journal, dated; the same thing twice on one day is kept once. */
    public void remember(long day, String what) {
        String line = "Day " + (day + 1) + ": " + what;
        if (memories.contains(line)) return;
        memories.add(line);
        while (memories.size() > MAX_MEMORIES) memories.removeFirst();
    }
}
