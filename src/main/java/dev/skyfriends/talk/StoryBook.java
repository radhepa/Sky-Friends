package dev.skyfriends.talk;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import dev.skyfriends.SkyFriends;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import org.jspecify.annotations.Nullable;

/**
 * The Cirri's personal stories: {@code data/skyfriends/stories/<bank>.json}, one book for grown-ups ({@code cirri})
 * and one for children ({@code cirri_child}). Checked by {@code tools/stories/check.py}, whose docstring is the schema.
 *
 * <p>A grown-up's story runs in chapters: they bring it up ({@code intro}), ask for a first thing
 * (requests[0]), take their time ({@code waiting}) until they are ready ({@code ready}) to tell you
 * the rest ({@code confide}), and after the other two requests let you answer it one of two ways
 * ({@code endings}); then they give you something. A child's story is one request and a gift.
 */
public final class StoryBook {
    public record Request(String id, String title, Item item, int count, String prompt, String thanks) {}

    public record Ending(String id, String label, String text, String memory) {}

    public record Story(String id, String title, List<String> jobs, String intro, List<Request> requests, String waiting,
                        String ready, String confide, List<Ending> endings, Item gift, int giftCount) {
        /** A child's story: one request and then the gift. */
        public boolean isShort() {
            return endings.isEmpty();
        }
    }

    private static final Map<String, StoryBook> BOOKS = new ConcurrentHashMap<>();

    private final List<String> locked;
    private final List<Story> stories = new ArrayList<>();

    private StoryBook(JsonObject json) {
        this.locked = strings(json.getAsJsonArray("locked"));
        JsonArray ss = json.getAsJsonArray("stories");
        if (ss != null) for (JsonElement el : ss) {
            JsonObject s = el.getAsJsonObject();
            List<Request> requests = new ArrayList<>();
            for (JsonElement r : s.getAsJsonArray("requests")) {
                JsonObject o = r.getAsJsonObject();
                requests.add(new Request(str(o, "id"), str(o, "title"), item(str(o, "item")), o.get("count").getAsInt(),
                        str(o, "prompt"), str(o, "thanks")));
            }
            List<Ending> endings = new ArrayList<>();
            JsonArray es = s.getAsJsonArray("endings");
            if (es != null) for (JsonElement e : es) {
                JsonObject o = e.getAsJsonObject();
                endings.add(new Ending(str(o, "id"), str(o, "label"), str(o, "text"), str(o, "memory")));
            }
            JsonObject gift = s.getAsJsonObject("gift");
            stories.add(new Story(str(s, "id"), str(s, "title"), strings(s.getAsJsonArray("jobs")), str(s, "intro"),
                    List.copyOf(requests), str(s, "waiting"), str(s, "ready"), str(s, "confide"), List.copyOf(endings),
                    item(str(gift, "item")), gift.get("count").getAsInt()));
        }
    }

    /** A book by bank name; a missing or broken book logs once and tells no stories. */
    public static StoryBook get(String bank) {
        return BOOKS.computeIfAbsent(bank, StoryBook::load);
    }

    private static StoryBook load(String bank) {
        String path = "/data/" + SkyFriends.MOD_ID + "/stories/" + bank + ".json";
        try (InputStream in = StoryBook.class.getResourceAsStream(path)) {
            if (in == null) {
                SkyFriends.LOG.error("Missing story book {}", path);
                return new StoryBook(new JsonObject());
            }
            return new StoryBook(JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject());
        } catch (Exception e) {
            SkyFriends.LOG.error("Can't read story book {}", path, e);
            return new StoryBook(new JsonObject());
        }
    }

    private static String str(JsonObject o, String key) {
        return o.has(key) ? o.get(key).getAsString() : "";
    }

    private static List<String> strings(@Nullable JsonArray array) {
        List<String> out = new ArrayList<>();
        if (array != null) for (JsonElement el : array) out.add(el.getAsString());
        return List.copyOf(out);
    }

    private static Item item(String id) {
        return id.isEmpty() ? Items.AIR : BuiltInRegistries.ITEM.getValue(Identifier.parse(id));
    }

    public List<Story> stories() {
        return stories;
    }

    /** What they say if you ask for their story before they know you. */
    public String locked(RandomSource random) {
        return locked.isEmpty() ? "Not yet." : locked.get(random.nextInt(locked.size()));
    }

    public @Nullable Story story(String id) {
        for (Story s : stories) if (s.id().equals(id)) return s;
        return null;
    }

    /** A story for someone with this job: one of their job's own, more often than not, if it has any. */
    public @Nullable Story pickStory(String job, RandomSource random) {
        List<Story> own = stories.stream().filter(s -> s.jobs().contains(job)).toList();
        List<Story> anyone = stories.stream().filter(s -> s.jobs().isEmpty()).toList();
        if (!own.isEmpty() && (anyone.isEmpty() || random.nextInt(3) != 0)) return own.get(random.nextInt(own.size()));
        if (!anyone.isEmpty()) return anyone.get(random.nextInt(anyone.size()));
        return stories.isEmpty() ? null : stories.get(random.nextInt(stories.size()));
    }

    /** Forget loaded books (tests and resource reloads). */
    public static void clear() {
        BOOKS.clear();
    }
}
