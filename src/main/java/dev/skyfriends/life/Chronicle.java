package dev.skyfriends.life;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import dev.skyfriends.SkyFriends;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.datafix.DataFixTypes;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;

/**
 * What has happened in each sky village lately, for the Cirri to talk about (docs/DIALOGUE.md, "news"): a baby
 * born, a child grown up, someone gone up past the blue, a whale passing, a storm, a walker's visit, a gift loved,
 * a blow struck, a story helped along. Names are kept as they were said. A village keeps its last 24 pieces of
 * news, none older than thirty days.
 */
public final class Chronicle extends SavedData {
    public record News(long day, String kind, String who, String other) {
        public static final Codec<News> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.LONG.fieldOf("day").forGetter(News::day),
            Codec.STRING.fieldOf("kind").forGetter(News::kind),
            Codec.STRING.optionalFieldOf("who", "").forGetter(News::who),
            Codec.STRING.optionalFieldOf("other", "").forGetter(News::other)
        ).apply(i, News::new));
    }

    private static final Codec<Map<String, List<News>>> MAPS = Codec.unboundedMap(Codec.STRING, News.CODEC.listOf());
    private static final Codec<Chronicle> CODEC = MAPS.xmap(Chronicle::new, c -> c.villages);
    private static final SavedDataType<Chronicle> TYPE =
            new SavedDataType<>(SkyFriends.id("chronicle"), Chronicle::new, CODEC, DataFixTypes.SAVED_DATA_COMMAND_STORAGE);
    private static final int KEEP = 24, DAYS = 30;

    private final Map<String, List<News>> villages = new HashMap<>();

    public Chronicle() {}

    private Chronicle(Map<String, List<News>> loaded) {
        loaded.forEach((k, v) -> villages.put(k, new ArrayList<>(v)));
    }

    public static Chronicle get(ServerLevel level) {
        return level.getServer().getDataStorage().computeIfAbsent(TYPE);
    }

    public static String key(BlockPos home) {
        return home.getX() + "," + home.getY() + "," + home.getZ();
    }

    /** Adds a piece of news to a village (the same news twice on one day is kept once). */
    public static void report(ServerLevel level, BlockPos home, long day, String kind, String who, String other) {
        Chronicle c = get(level);
        List<News> list = c.villages.computeIfAbsent(key(home), k -> new ArrayList<>());
        News news = new News(day, kind, who, other);
        if (list.contains(news)) return;
        list.add(news);
        list.removeIf(n -> day - n.day() > DAYS);
        while (list.size() > KEEP) list.removeFirst();
        c.setDirty();
    }

    /** Whether something of this kind is already news in the village today. */
    public static boolean reportedToday(ServerLevel level, BlockPos home, long day, String kind) {
        return get(level).villages.getOrDefault(key(home), List.of()).stream().anyMatch(n -> n.day() == day && n.kind().equals(kind));
    }

    /** The village's news from the last {@code days} days, newest first. */
    public static List<News> recent(ServerLevel level, BlockPos home, long today, int days) {
        var out = new ArrayList<News>();
        for (News n : get(level).villages.getOrDefault(key(home), List.of())) if (today - n.day() <= days) out.addFirst(n);
        return out;
    }
}
