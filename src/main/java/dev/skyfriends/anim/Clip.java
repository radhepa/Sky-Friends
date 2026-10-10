package dev.skyfriends.anim;

import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * One authored animation for a people. Tracks are keyed by model part name ({@code right_arm}, {@code tail},
 * {@code tentacle_3}...) plus two special bones: {@code waist} bends the upper body at the hips, {@code root} turns
 * or moves the whole body about the feet. Rotations are degrees added to the live pose; positions are model pixels.
 * {@link #require} entries are any-of groups ({@code "job:weaver|job:spinner"}) that must all match; {@link #avoid}
 * tags rule the clip out; {@link #boost} multiplies the weight for each matching tag.
 */
public record Clip(String id, String name, String trigger, float length, float weight,
                   List<Set<String>> require, Set<String> avoid, Map<String, Float> boost,
                   float blendIn, float blendOut, Mirror mirror,
                   String[] bones, String[] mirrored, Track[] rotations, Track[] positions) {

    public static final String WAIST = "waist", ROOT = "root";

    /** HAND mirrors for left-handed folk; FREE may also mirror at random for variety; NEVER keeps it as written. */
    public enum Mirror { HAND, FREE, NEVER }

    public boolean eligible(Set<String> tags) {
        for (Set<String> group : require) {
            boolean any = false;
            for (String tag : group) {
                if (tags.contains(tag)) {
                    any = true;
                    break;
                }
            }
            if (!any) return false;
        }
        for (String tag : avoid) {
            if (tags.contains(tag)) return false;
        }
        return true;
    }

    public float weightFor(Set<String> tags) {
        float w = weight;
        for (Map.Entry<String, Float> e : boost.entrySet()) {
            if (tags.contains(e.getKey())) w *= e.getValue();
        }
        return w;
    }

    /** Fades the clip in and out so interrupted or overlapping clips never pop. */
    public float envelope(float t) {
        if (t < 0 || t > length) return 0;
        float in = blendIn <= 0 ? 1 : smooth(t / blendIn), out = blendOut <= 0 ? 1 : smooth((length - t) / blendOut);
        return Math.min(in, out);
    }

    /** True if the clip only moves the legs, waist or whole body for part of it (so walking can't take over). */
    public boolean uses(String bone) {
        for (String b : bones) {
            if (b.equals(bone)) return true;
        }
        return false;
    }

    /** The other side's part: right_arm and left_arm, right_lower_forearm and left_lower_forearm. */
    public static String mirror(String bone) {
        if (bone.startsWith("right_")) return "left_" + bone.substring(6);
        if (bone.startsWith("left_")) return "right_" + bone.substring(5);
        return bone;
    }

    public static float smooth(float value) {
        float t = Math.max(0, Math.min(1, value));
        return t * t * (3 - 2 * t);
    }
}
