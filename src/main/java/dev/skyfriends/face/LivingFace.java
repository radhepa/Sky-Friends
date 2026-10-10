package dev.skyfriends.face;

import java.util.UUID;

/**
 * Living eyes, the same as Village Friends residents': two pixel-art eye styles, fine brows, a small
 * mouth and, for feminine faces, a lash wing, rosy lips and a blush. Every feature is a plane in front
 * of a clean face that samples one pixel of the face swatch strip baked into the texture
 * (tools/people/living_eyes.py). Face coordinates are model pixels: x runs from -4 (the viewer's left
 * edge of the face) to 4, y from -8 (top of the head) to 0 (chin).
 *
 * <p>The numbers and timing match Village Friends' FaceDetails and ResidentMotion exactly, so a Cirri
 * blinks, glances and keeps eye contact the way a villager does. Nothing here depends on Village
 * Friends being installed.
 */
public final class LivingFace {
    /** Each person keeps one eye style for life, chosen from their seed. */
    public enum EyeStyle {
        /** Lash line, a tinted-white over dark-pupil row, then a glint over the iris: three rows tall. */
        STARLIT,
        /** Lash line over a glint and the iris: two rows tall, lower and softer. */
        SOFT_GLINT
    }

    /** The face swatch strip, in the order tools/people/living_eyes.py bakes it. */
    public enum Swatch { WHITE, IRIS, LID, BROW, LASH, SHADOW, TINT, PUPIL, LIP, ROSE_LIP, BLUSH }

    /** The open eye always ends on the bottom of face row 5. */
    public static final float EYE_BOTTOM = -2F;

    /** A stable per-person number from their UUID (Village Friends' ResidentMotion.seed). */
    public static int seed(UUID id) {
        return mix(Long.hashCode(id.getMostSignificantBits() ^ Long.rotateLeft(id.getLeastSignificantBits(), 23)));
    }

    public static EyeStyle eyeStyle(int seed) {
        return (mix(seed ^ 0x51A7E5) & 1) == 0 ? EyeStyle.STARLIT : EyeStyle.SOFT_GLINT;
    }

    /** The feminine details (lash wing, arched brows, rosy lips, blush), from the seed: about half of all Cirri. */
    public static boolean feminine(int seed) {
        return (mix(seed ^ 0x7E11A5) & 1) == 0;
    }

    /** Top of the open eye, below its lash line. */
    public static float eyeTop(EyeStyle style) { return style == EyeStyle.STARLIT ? -4F : -3F; }
    /** Top of the brows: higher over the taller Starlit eye, always a clear gap above the lashes. */
    public static float browTop(EyeStyle style) { return style == EyeStyle.STARLIT ? -6F : -5.6F; }
    /** The lash line rests on the eye and thins a little as it sweeps down to close it. */
    public static float lashHeight(float blink) { return 1 - .4F * blink; }
    public static float lashBottom(EyeStyle style, float blink) { float top = eyeTop(style); return top + (EYE_BOTTOM - top) * blink; }
    /** The feminine wing: below the Starlit lash, above the Soft Glint lash; it joins the closed lash line. */
    public static float wingTop(EyeStyle style, float blink) { float rest = style == EyeStyle.STARLIT ? -4F : -5F; return rest + (-2.8F - rest) * blink; }
    public static float wingHeight(float blink) { return 1 - .5F * blink; }

    // -- blinking and glances (Village Friends' ResidentMotion) -------------------------------------

    public static float phase(int seed) { return Math.floorMod(seed >>> 12, 6283) * .001F; }
    public static int blinkPeriod(int seed) { return 97 + Math.floorMod(seed >>> 3, 67); }

    /** How closed the eyes are (0 open .. 1 shut) at this age in ticks: about 0.2 s per blink, every five to eight seconds, sometimes twice. */
    public static float blink(float age, int seed) {
        int period = blinkPeriod(seed);
        float time = age + Math.floorMod(seed, period);
        int cycle = (int) Math.floor(time / period);
        float local = time - cycle * period;
        float start = 12 + Math.floorMod(mix(seed ^ cycle), period - 28);
        float first = blinkPulse(local - start);
        return Math.floorMod(mix(seed + cycle), 7) == 0 ? Math.max(first, blinkPulse(local - start - 7)) : first;
    }

    private static float blinkPulse(float time) {
        if (time < 0 || time > 3.9F) return 0;
        if (time < 1.2F) return smooth(time / 1.2F);
        if (time < 1.5F) return 1;
        return 1 - smooth((time - 1.5F) / 2.4F);
    }

    /** An idle sideways glance, -0.18..0.18 px. */
    public static float glance(float age, int seed) {
        float phase = phase(seed);
        return (float) (Math.sin(age * .031F + phase) * Math.sin(age * .013F + phase) * .18F);
    }

    public static float smooth(float value) {
        float t = Math.max(0, Math.min(1, value));
        return t * t * (3 - 2 * t);
    }

    static int mix(int value) {
        value ^= value >>> 16;
        value *= 0x7feb352d;
        value ^= value >>> 15;
        value *= 0x846ca68b;
        return value ^ (value >>> 16);
    }

    private LivingFace() {}
}
