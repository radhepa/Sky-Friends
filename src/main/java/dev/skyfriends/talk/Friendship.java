package dev.skyfriends.talk;

/**
 * How close a Cirri and a player are: eleven levels, 0 to 10, shown as ten little clouds that fill with gold.
 * Each level has a name in the Cirri's own manner and opens something new.
 */
public final class Friendship {
    public static final int MAX = 10;
    private static final int[] THRESHOLDS = {0, 10, 25, 45, 70, 100, 135, 175, 220, 270, 330};
    private static final String[] NAMES = {"Walker", "Passing Cloud", "Light Breeze", "Fair Wind", "Kind Air", "Open Sky", "Updraft",
            "High Wind", "Windsong", "Veil-Kin", "One Sky"};
    private static final String[] PERKS = {"", "They'll tell you what's on their mind (Story).", "They'll remember what you tell them.",
            "They tell you the village news.", "They ask after you when you've been away.", "Heart-to-heart talks about the ones they love.",
            "They share the old stories.", "They wave you over with a heart, and save you little presents.", "They sing for you.",
            "Kin of the veil.", "One sky: as close as friends can be."};
    /** Levels at which things open. */
    public static final int STORY = 1, NEWS = 3, HEART = 5, PRESENTS = 7;

    private Friendship() {}

    public static int level(int points) {
        int level = 0;
        while (level < MAX && points >= THRESHOLDS[level + 1]) level++;
        return level;
    }

    /** Points at which a level begins. */
    public static int floor(int level) {
        return THRESHOLDS[Math.clamp(level, 0, MAX)];
    }

    /** Points at which the next level begins (the top level's own floor at 10). */
    public static int next(int level) {
        return THRESHOLDS[Math.clamp(level + 1, 0, MAX)];
    }

    /** The most points worth keeping: a little past the top level. */
    public static int cap() {
        return THRESHOLDS[MAX] + 50;
    }

    public static String name(int level) {
        return NAMES[Math.clamp(level, 0, MAX)];
    }

    public static String perk(int level) {
        return PERKS[Math.clamp(level, 0, MAX)];
    }

    /** How well they know you, in five bands, for greetings ({@code greet.band.<band>}). */
    public static String band(int level) {
        return level <= 0 ? "stranger" : level <= 2 ? "acquaintance" : level <= 4 ? "friend" : level <= 7 ? "close" : "best";
    }
}
