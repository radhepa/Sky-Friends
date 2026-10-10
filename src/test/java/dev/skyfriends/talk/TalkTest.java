package dev.skyfriends.talk;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import org.junit.jupiter.api.Test;

/** The line-picking engine, with no game running: pools by context, placeholders, questions, friendship levels. */
class TalkTest {
    private static Talk.Context context(String topic, boolean child, int level, String weather, Set<String> states, Set<String> extra,
                                        Map<String, String> fill) {
        return new Talk.Context(topic, child, child ? "playful" : "dreamer", child ? "" : "harpist", level, "evening", weather, "vell",
                "full", child ? "play" : "evensong", "", states, extra, fill);
    }

    @Test
    void poolsFollowTheMoment() {
        var greet = Talk.pools(context("greet", false, 0, "rain", Set.of("wet"), Set.of(), Map.of()));
        assertTrue(greet.containsKey("greet.evening"));
        assertTrue(greet.containsKey("greet.band.stranger"));
        assertTrue(greet.containsKey("greet.weather.rain"));
        assertTrue(greet.containsKey("player.wet"));
        assertTrue(greet.containsKey("greet.routine.evensong"));
        var chat = Talk.pools(context("chat", false, 7, "clear", Set.of(), Set.of("whale", "a:likes:aure"), Map.of()));
        assertTrue(chat.containsKey("chat.dreamer"));
        assertTrue(chat.containsKey("chat.close"));
        assertTrue(chat.containsKey("village.whale"));
        assertTrue(chat.containsKey("remember.likes_aure"));
        assertTrue(chat.containsKey("wind.vell"));
        var song = Talk.pools(context("song", false, 2, "clear", Set.of(), Set.of(), Map.of()));
        assertEquals(4, song.get("song.evensong"));
        assertTrue(song.containsKey("song.harpist"));
        var kid = Talk.pools(context("family", true, 1, "clear", Set.of(), Set.of(), Map.of()));
        assertTrue(kid.keySet().stream().allMatch(k -> k.startsWith("baby.family")));
    }

    @Test
    void placeholdersFillOrSkip() {
        Map<String, String> fill = new HashMap<>(Map.of("name", "Ilvara", "player", "Steve"));
        assertEquals("Fair wind, Steve!", Talk.fill("Fair wind, {player}!", fill));
        assertEquals("Ilvara here.", Talk.fill("{name} here.", fill));
        assertNull(Talk.fill("My {spouse}, {partner}.", fill));
        var bank = new Lines(1, Map.of("heart.partner", List.of("My {spouse}, {partner}, sings flat.", "No one yet.")), List.of());
        var line = Talk.from(bank, "heart.partner", fill, new Random(1), List.of());
        assertNotNull(line);
        assertEquals("No one yet.", line.text());
        assertNull(Talk.from(bank, "heart.partner", fill, new Random(1), List.of("heart.partner#1")));
    }

    @Test
    void questionsAskedWhenTheyFit() {
        var answers = List.of(new Lines.Answer("Yes", "Good.", "likes:rain", "", 1, "NOTE"), new Lines.Answer("No", "Oh.", "", "", 0, ""));
        var rainy = new Lines.Question("rain_q", false, List.of("rain", "!child"), List.of("Do you like rain?"), answers);
        var friends = new Lines.Question("deep_q", false, List.of("level:5"), List.of("Tell me a secret?"), answers);
        var heal = new Lines.Question("heal", true, List.of("hurt", "job:gardener|job:harpist"), List.of("You're hurt!"), answers);
        var bank = new Lines(1, Map.of(), List.of(rainy, friends, heal));
        var r = new Random(3);
        assertEquals("rain_q", Talk.question(bank, context("chat", false, 2, "rain", Set.of(), Set.of(), Map.of()), Set.of(), false, r).id());
        assertNull(Talk.question(bank, context("chat", false, 2, "clear", Set.of(), Set.of(), Map.of()), Set.of(), false, r));
        assertNull(Talk.question(bank, context("chat", true, 9, "rain", Set.of(), Set.of(), Map.of()), Set.of("deep_q"), false, r));
        assertEquals("heal", Talk.question(bank, context("chat", false, 0, "clear", Set.of("hurt"), Set.of(), Map.of()), Set.of(), true, r).id());
        assertNull(Talk.question(bank, context("chat", false, 0, "clear", Set.of(), Set.of(), Map.of()), Set.of(), true, r));
        assertEquals(1, Talk.answerIndex("answer:rain_q:1", "rain_q"));
        assertEquals(-1, Talk.answerIndex("answer:other:1", "rain_q"));
    }

    @Test
    void friendshipLevelsAndPeriods() {
        assertEquals(0, Friendship.level(0));
        assertEquals(1, Friendship.level(10));
        assertEquals(3, Friendship.level(45));
        assertEquals(10, Friendship.level(400));
        assertEquals("Walker", Friendship.name(0));
        assertEquals("One Sky", Friendship.name(10));
        assertEquals("best", Friendship.band(9));
        assertEquals("dawn", Talk.period(23500));
        assertEquals("morning", Talk.period(1000));
        assertEquals("evening", Talk.period(12000));
        assertEquals("night", Talk.period(15000));
        assertEquals(Personality.MERRY, Personality.grownUp(Personality.CHEEKY));
    }

    @Test
    void theShippedBankIsWhole() throws Exception {
        try (var in = TalkTest.class.getResourceAsStream("/data/skyfriends/dialogue/cirri.json")) {
            assertNotNull(in);
            Lines bank = Lines.parse(new String(in.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8));
            assertTrue(bank.size() > 5000, "size " + bank.size());
            for (Personality p : Personality.values()) assertTrue(bank.has(p.child ? "baby." + p.id : "chat." + p.id), p.id);
            for (String job : List.of("harpist", "weaver", "gardener", "bellkeeper", "lamplighter", "skymerchant", "windkeeper", "none")) {
                assertTrue(bank.has("work." + job), job);
            }
            // every flag an answer sets is called back to later
            for (var q : bank.questions()) {
                for (var a : q.answers()) {
                    if (a.flag() != null && !a.flag().isEmpty()) assertTrue(bank.has("remember." + a.flag().replace(':', '_')), a.flag());
                }
            }
            assertFalse(bank.pools().values().stream().flatMap(List::stream).anyMatch(l -> l.contains("--")));
        }
    }
}
