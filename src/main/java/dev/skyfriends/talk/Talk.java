package dev.skyfriends.talk;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Chooses what a Cirri says from what is actually happening: the hour, the weather and today's wind, the moon,
 * what they were doing, their personality and job, how well they know you, what you hold and how you look, what
 * is near (a Cloud Whale, koi, children, a wind harp, the Evensong) and what you told them before. Pure: the
 * world is read into a {@link Context} by {@link TalkWorld}. docs/DIALOGUE.md lists every pool.
 */
public final class Talk {
    /**
     * The moment a line is chosen for. {@code states} describe the player ("hurt", "wet", "elytra"...), {@code
     * extra} the surroundings ("whale", "koi", "evensong") and remembered answers ("a:likes:aure").
     */
    public record Context(String topic, boolean child, String personality, String job, int level, String period, String weather,
                          String wind, String moon, String routine, String held, Set<String> states, Set<String> extra,
                          Map<String, String> fill) {
        public boolean night() {
            return period.equals("night") || period.equals("late");
        }

        /** Every tag a question's "when:" can test. */
        public Set<String> tags() {
            var tags = new HashSet<String>();
            tags.add(topic);
            tags.add(child ? "child" : "adult");
            tags.add("personality:" + personality);
            tags.add("job:" + job);
            tags.add(period);
            tags.add(night() ? "night" : "day");
            tags.add(weather);
            tags.add("wind:" + wind);
            tags.add("moon:" + moon);
            tags.add("routine:" + routine);
            if (!held.isEmpty()) tags.add("held:" + held);
            tags.add(level >= 3 ? "friends" : "newcomers");
            tags.addAll(states);
            tags.addAll(extra);
            return tags;
        }
    }

    /** A chosen line, its pool and position (for not repeating it soon). */
    public record Line(String key, int index, String text) {
        public String id() {
            return key + "#" + index;
        }
    }

    public static final String[] MOONS = {"full", "waning_gibbous", "last_quarter", "waning_crescent", "new", "waxing_crescent",
            "first_quarter", "waxing_gibbous"};
    public static final List<String> THINGS = List.of("whale", "koi", "children", "harp", "evensong");

    private Talk() {}

    public static String moonName(String moon) {
        return moon.replace('_', ' ') + " moon";
    }

    /** The hour, from the clock (ticks; 0 is six in the morning). */
    public static String period(long time) {
        int hour = (int) (Math.floorMod(time, 24000L) / 1000 + 6) % 24;
        if (hour >= 5 && hour < 7) return "dawn";
        if (hour < 5) return "late";
        if (hour < 11) return "morning";
        if (hour < 13) return "noon";
        if (hour < 17) return "afternoon";
        if (hour < 20) return "evening";
        return "night";
    }

    /** Which pools a topic draws from now, and how likely each is. */
    public static Map<String, Integer> pools(Context c) {
        var w = new LinkedHashMap<String, Integer>();
        boolean weather = !c.weather.equals("clear");
        if (c.child) {
            child(w, c, weather);
            return w;
        }
        switch (c.topic) {
            case "greet" -> {
                w.put("greet." + c.period, 3);
                w.put("greet.band." + Friendship.band(c.level), 3);
                w.put("greet.personality." + c.personality, 2);
                w.put("greet.routine." + c.routine, 3);
                if (weather) w.put("greet.weather." + c.weather, 5);
                w.put("greet.wind." + c.wind, 1);
                held(w, c, 2);
                states(w, c, 4);
            }
            case "chat" -> {
                w.put("chat." + c.personality, 6);
                w.put("chat.general", 3);
                w.put("routine." + c.routine, 3);
                w.put("time." + c.period, 2);
                w.put(c.level >= 6 ? "chat.close" : c.level <= 1 ? "chat.new" : "chat.friendly", 2);
                w.put("weather." + c.weather, weather ? 4 : 1);
                if (c.night()) w.put("moon." + c.moon, 2);
                w.put("wind." + c.wind, 2);
                for (String thing : THINGS) if (c.extra.contains(thing)) w.put("village." + thing, 2);
                held(w, c, 2);
                states(w, c, 3);
                remembered(w, c, 3);
            }
            case "work" -> {
                w.put("work." + (c.job.isEmpty() ? "none" : c.job), 7);
                w.put(c.routine.equals("work") ? "work.on" : "work.off", 2);
                if (weather) w.put("work.weather." + c.weather, 1);
            }
            case "sky" -> {
                w.put("sky.general", 3);
                w.put("sky.winds", 2);
                w.put("sky.clouds", 2);
                w.put("sky.whales", c.extra.contains("whale") ? 6 : 2);
                w.put("sky.koi", c.extra.contains("koi") ? 4 : 1);
                w.put("sky.stars", c.night() ? 4 : 1);
                w.put("sky.storms", c.weather.equals("rain") || c.weather.equals("thunder") ? 4 : 1);
                w.put("sky.veils", 2);
                w.put("sky.history", c.level >= 3 ? 3 : 2);
            }
            case "ground" -> {
                w.put("ground.general", 4);
                w.put("ground." + c.personality, 3);
                w.put("ground.villages", 1);
                w.put("ground.wonders", 2);
                w.put("ground.fears", 2);
            }
            case "song" -> {
                w.put("song.general", 4);
                w.put("song." + c.personality, 2);
                w.put("song.evensong", c.period.equals("evening") || c.extra.contains("evensong") ? 4 : 1);
                if (c.night()) w.put("song.night", 4);
                if (weather) w.put("song.weather." + c.weather, 2);
                if (c.job.equals("harpist")) w.put("song.harpist", 4);
            }
            default -> w.put("chat.general", 1);
        }
        return w;
    }

    private static void child(Map<String, Integer> w, Context c, boolean weather) {
        switch (c.topic) {
            case "greet" -> {
                w.put("baby.greet", 6);
                if (weather) w.put("baby.weather." + c.weather, 4);
                w.put("baby.routine." + c.routine, 2);
                w.put("baby.time." + c.period, 1);
                if (!c.held.isEmpty()) w.put("baby.held", 1);
                for (String s : c.states) w.put("baby.player." + s, 3);
            }
            case "chat" -> {
                w.put("baby.chat", 6);
                w.put("baby." + c.personality, 3);
                w.put("baby.weather." + c.weather, weather ? 3 : 1);
                w.put("baby.routine." + c.routine, 2);
                w.put("baby.time." + c.period, 1);
                for (String thing : THINGS) if (c.extra.contains(thing)) w.put("baby.village." + thing, 2);
                if (!c.held.isEmpty()) w.put("baby.held", 1);
                for (String s : c.states) w.put("baby.player." + s, 2);
                remembered(w, c, 2);
            }
            case "play" -> {
                w.put("baby.play", 6);
                w.put("baby." + c.personality, 1);
            }
            case "sky" -> {
                w.put("baby.sky", 6);
                if (c.extra.contains("whale")) w.put("baby.village.whale", 2);
                if (c.extra.contains("koi")) w.put("baby.village.koi", 2);
            }
            case "ground" -> w.put("baby.ground", 6);
            case "song" -> {
                w.put("baby.song", 6);
                if (c.night()) w.put("baby.song.night", 6);
            }
            case "secret" -> w.put("baby.secret", 6);
            case "family" -> {
                w.put("baby.family", 3);
                w.put("baby.family.mum", 3);
                w.put("baby.family.dad", 3);
            }
            default -> w.put("baby.chat", 1);
        }
    }

    private static void held(Map<String, Integer> w, Context c, int weight) {
        if (!c.held.isEmpty()) w.put("held." + c.held, weight);
    }

    private static void states(Map<String, Integer> w, Context c, int weight) {
        for (String s : c.states) w.put("player." + s, weight);
    }

    private static void remembered(Map<String, Integer> w, Context c, int weight) {
        for (String tag : c.extra) if (tag.startsWith("a:")) w.put("remember." + tag.substring(2).replace(':', '_'), weight);
    }

    /** A line for this moment that hasn't been said lately, placeholders filled; null if nothing fits. */
    public static Line pick(Lines bank, Context c, Random random, Collection<String> recent) {
        var weights = new LinkedHashMap<String, Integer>();
        for (var e : pools(c).entrySet()) if (bank.has(e.getKey())) weights.put(e.getKey(), e.getValue());
        for (int attempt = 0; attempt < 12 && !weights.isEmpty(); attempt++) {
            String key = weighted(weights, random);
            Line line = from(bank, key, c.fill(), random, recent);
            if (line != null) return line;
            weights.remove(key);    // everything here was said lately or can't be filled
        }
        return null;
    }

    /** A line from one pool that hasn't been said lately and whose placeholders can be filled; null if none. */
    public static Line from(Lines bank, String key, Map<String, String> fill, Random random, Collection<String> recent) {
        List<String> lines = bank.pool(key);
        if (lines.isEmpty()) return null;
        int start = random.nextInt(lines.size());
        for (int n = 0; n < lines.size(); n++) {
            int index = (start + n) % lines.size();
            if (recent.contains(key + "#" + index)) continue;
            String text = fill(lines.get(index), fill);
            if (text != null) return new Line(key, index, text);
        }
        return null;
    }

    private static String weighted(Map<String, Integer> weights, Random random) {
        int total = 0;
        for (int v : weights.values()) total += v;
        int roll = random.nextInt(total);
        for (var e : weights.entrySet()) {
            roll -= e.getValue();
            if (roll < 0) return e.getKey();
        }
        return weights.keySet().iterator().next();
    }

    private static final Pattern SLOT = Pattern.compile("\\{([a-z_]+)}");

    /** Fills {placeholders}; null when one of them has no value here. */
    public static String fill(String line, Map<String, String> values) {
        Matcher m = SLOT.matcher(line);
        var out = new StringBuilder();
        while (m.find()) {
            String value = values.get(m.group(1));
            if (value == null || value.isBlank()) return null;
            m.appendReplacement(out, Matcher.quoteReplacement(value));
        }
        m.appendTail(out);
        String text = out.toString();
        return text.isEmpty() ? text : Character.toUpperCase(text.charAt(0)) + text.substring(1);
    }

    /** Whether a question's conditions hold: tags must all be present, "!tag" absent, "level:N" reached, "a|b" either. */
    public static boolean eligible(Lines.Question q, Set<String> tags, int level) {
        if (q.when() == null) return true;
        for (String cond : q.when()) {
            if (cond.startsWith("level:")) {
                if (level < Integer.parseInt(cond.substring(6))) return false;
            } else if (cond.startsWith("!")) {
                for (String option : cond.substring(1).split("\\|")) if (tags.contains(option)) return false;
            } else if (cond.contains("|")) {
                boolean any = false;
                for (String option : cond.split("\\|")) any |= tags.contains(option);
                if (!any) return false;
            } else if (!tags.contains(cond)) {
                return false;
            }
        }
        return true;
    }

    /** A question to ask (or an offer to make) now, avoiding ones already done; null if none fit. */
    public static Lines.Question question(Lines bank, Context c, Set<String> done, boolean offers, Random random) {
        var tags = c.tags();
        var fit = new ArrayList<Lines.Question>();
        for (var q : bank.questions()) {
            if (q.offer() != offers || done.contains(q.id()) || !eligible(q, tags, c.level())) continue;
            boolean fillable = true;
            for (String ask : q.ask()) if (fill(ask, c.fill()) == null) fillable = false;
            if (fillable) fit.add(q);
        }
        return fit.isEmpty() ? null : fit.get(random.nextInt(fit.size()));
    }

    /** The 0-based answer from an action like "answer:favourite_wind:2", or -1. */
    public static int answerIndex(String action, String questionId) {
        String prefix = "answer:" + questionId + ":";
        if (!action.startsWith(prefix)) return -1;
        try {
            return Integer.parseInt(action.substring(prefix.length()));
        } catch (NumberFormatException e) {
            return -1;
        }
    }
}
