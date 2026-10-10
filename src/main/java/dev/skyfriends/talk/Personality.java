package dev.skyfriends.talk;

import java.util.Locale;
import net.minecraft.util.RandomSource;

/**
 * Who a Cirri is: the voice their lines are written in ({@code chat.<id>}, {@code baby.<id>}...) and the
 * {@link Manner} they keep while you talk. Grown-ups and children have their own sets; a child who grows up
 * becomes the grown-up their nature points to.
 */
public enum Personality {
    DREAMER("dreamer", "Dreamer", "Head in the clouds; drifts off mid-thought and wonders about everything.", Manner.STEADY, false, 3),
    MERRY("merry", "Merry", "Cheerful and teasing; darts off for a loop now and then and comes straight back.", Manner.FLIGHTY, false, 3),
    GENTLE("gentle", "Gentle", "Soft-spoken and kind; notices when you're hurt or tired.", Manner.STEADY, false, 3),
    SHY("shy", "Shy", "Quiet at first and keeps a little distance; warms slowly.", Manner.SHY, false, 2),
    PROUD("proud", "Proud", "Proud of the village and of Cirri ways, a little grand with walkers; softens as a friend.", Manner.STEADY, false, 2),
    RESTLESS("restless", "Restless", "Can't stay still and longs for distant skies; drifts round you as you talk.", Manner.RESTLESS, false, 2),
    BUSY("busy", "Busy", "Always in the middle of something; fond, but will excuse themselves after a while.", Manner.BUSY, false, 2),
    WISE("wise", "Wise", "An old soul, full of sayings and the old stories.", Manner.STEADY, false, 2),
    CURIOUS("curious", "Curious", "Fascinated by walkers and the ground; asks about everything.", Manner.STEADY, false, 3),

    PLAYFUL("playful", "Playful", "Bobs and drifts all round you, and turns everything into a game.", Manner.RESTLESS, true, 3),
    KID_SHY("shy", "Shy", "Peeks at you from a little way off.", Manner.SHY, true, 2),
    KID_CURIOUS("curious", "Curious", "Full of questions about walkers and the ground.", Manner.STEADY, true, 3),
    CHEEKY("cheeky", "Cheeky", "Darts off for a loop to show off, and comes straight back grinning.", Manner.FLIGHTY, true, 2),
    DREAMY("dreamy", "Dreamy", "Gazes at the clouds while you talk, and dreams of the Lengthening.", Manner.STEADY, true, 2),
    FIDGETY("fidgety", "Fidgety", "Can't hold still for long; runs off to play after a while.", Manner.BUSY, true, 2);

    public final String id, label, about;
    public final Manner manner;
    public final boolean child;
    public final int weight;

    Personality(String id, String label, String about, Manner manner, boolean child, int weight) {
        this.id = id;
        this.label = label;
        this.about = about;
        this.manner = manner;
        this.child = child;
        this.weight = weight;
    }

    /** A saved personality (by enum name), or a fresh pick if there is none or it no longer fits their age. */
    public static Personality of(String name, boolean child, RandomSource random) {
        try {
            Personality p = valueOf(name.toUpperCase(Locale.ROOT));
            if (p.child == child) return p;
            return child ? pick(true, random) : grownUp(p);
        } catch (IllegalArgumentException e) {
            return pick(child, random);
        }
    }

    public static Personality pick(boolean child, RandomSource random) {
        int total = 0;
        for (Personality p : values()) if (p.child == child) total += p.weight;
        int roll = random.nextInt(total);
        for (Personality p : values()) {
            if (p.child != child) continue;
            if ((roll -= p.weight) < 0) return p;
        }
        return child ? PLAYFUL : GENTLE;
    }

    /** The grown-up a child of this nature becomes. */
    public static Personality grownUp(Personality kid) {
        return switch (kid) {
            case PLAYFUL, CHEEKY -> MERRY;
            case KID_SHY -> SHY;
            case KID_CURIOUS -> CURIOUS;
            case DREAMY -> DREAMER;
            case FIDGETY -> RESTLESS;
            default -> kid;
        };
    }
}
