package dev.skyfriends.talk;

import com.google.gson.Gson;
import dev.skyfriends.SkyFriends;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.Map;

/**
 * Everything the Cirri can say: pools of handwritten lines keyed by situation ("work.weaver", "weather.rain",
 * "baby.play"...) and questions they ask you, with your possible answers. Compiled from {@code tools/dialogue}
 * by {@code dialogue.py} into {@code data/skyfriends/dialogue/cirri.json}; docs/DIALOGUE.md is the canon.
 */
public record Lines(int format, Map<String, List<String>> pools, List<Question> questions) {
    /** One answer: its label, their reply, a flag they remember, an effect, friendship points and their mood. */
    public record Answer(String label, String reply, String flag, String effect, int points, String mood) {}

    /** {@code offer}s are situational and can come up once a day; ordinary questions are asked once. */
    public record Question(String id, boolean offer, List<String> when, List<String> ask, List<Answer> answers) {}

    private static final Gson GSON = new Gson();
    private static final String PATH = "/data/skyfriends/dialogue/cirri.json";
    private static volatile Lines current;

    public static Lines current() {
        Lines lines = current;
        if (lines == null) current = lines = load();
        return lines;
    }

    public List<String> pool(String key) {
        return pools.getOrDefault(key, List.of());
    }

    public boolean has(String key) {
        return !pool(key).isEmpty();
    }

    public Question question(String id) {
        for (Question q : questions) if (q.id().equals(id)) return q;
        return null;
    }

    /** Lines, questions and answers (label and reply each). */
    public int size() {
        int n = 0;
        for (List<String> lines : pools.values()) n += lines.size();
        for (Question q : questions) n += q.ask().size() + q.answers().size() * 2;
        return n;
    }

    private static Lines load() {
        try (var stream = Lines.class.getResourceAsStream(PATH)) {
            if (stream == null) throw new IllegalStateException("missing " + PATH);
            return validate(GSON.fromJson(new InputStreamReader(stream, StandardCharsets.UTF_8), Lines.class));
        } catch (Exception e) {
            SkyFriends.LOG.error("Can't read the Cirri's dialogue {}", PATH, e);
            return new Lines(1, Map.of(), List.of());
        }
    }

    public static Lines parse(String json) {
        return validate(GSON.fromJson(json, Lines.class));
    }

    static Lines validate(Lines lines) {
        if (lines == null || lines.format != 1 || lines.pools == null || lines.questions == null)
            throw new IllegalArgumentException("Dialogue needs format 1, pools and questions");
        for (var e : lines.pools.entrySet()) {
            if (!e.getKey().matches("[a-z0-9_.]+")) throw new IllegalArgumentException("Bad pool key " + e.getKey());
            for (String line : e.getValue()) {
                if (line == null || line.isBlank() || line.length() > 300) throw new IllegalArgumentException("Bad line in " + e.getKey());
            }
        }
        var ids = new HashSet<String>();
        for (Question q : lines.questions) {
            if (q.id() == null || !q.id().matches("[a-z0-9_]{2,40}") || !ids.add(q.id())) throw new IllegalArgumentException("Bad question id " + q.id());
            if (q.ask() == null || q.ask().isEmpty() || q.answers() == null || q.answers().size() < 2 || q.answers().size() > 4)
                throw new IllegalArgumentException("Question " + q.id() + " needs a question and 2-4 answers");
        }
        return lines;
    }

    /** Forget the loaded bank (tests). */
    public static void clear() {
        current = null;
    }
}
