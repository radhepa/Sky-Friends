package dev.skyfriends.client.anim;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.WeakHashMap;

import dev.skyfriends.anim.Clip;
import dev.skyfriends.anim.Library;
import dev.skyfriends.anim.Pack;
import dev.skyfriends.anim.Track;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;
import org.joml.Matrix3f;
import org.joml.Vector3f;

/**
 * Adds the clips in a {@link Pose} on top of a model's live pose (look direction, gait, breathing). Parts are found
 * by name, so one pack serves every look of a people: a part a look doesn't have is skipped. The waist bends the
 * pack's upper parts at the hips and the root turns the whole body about the feet, so bows and leans keep the feet
 * planted. Rendering is single threaded; scratch buffers are reused so posing allocates nothing once warm.
 */
public final class Poser {
    private static final float[] SAMPLE = new float[3], WAIST = new float[3], ROOT = new float[3], ROOT_POS = new float[3];
    private static final Matrix3f TURN = new Matrix3f(), PART = new Matrix3f();
    private static final Vector3f POINT = new Vector3f(), EULER = new Vector3f();
    private static final Map<ModelPart, Map<String, Optional<ModelPart>>> PARTS = new WeakHashMap<>();

    public static void apply(ModelPart root, Pose pose) {
        if (pose.species == null || !pose.any()) return;
        Pack pack = Library.current().pack(pose.species);
        if (pack == null) return;
        WAIST[0] = WAIST[1] = WAIST[2] = 0;
        ROOT[0] = ROOT[1] = ROOT[2] = 0;
        ROOT_POS[0] = ROOT_POS[1] = ROOT_POS[2] = 0;
        Map<String, Optional<ModelPart>> parts = PARTS.computeIfAbsent(root, r -> new HashMap<>());
        for (Pose.Layer layer : pose.layers) {
            if (!layer.active()) continue;
            Clip clip = layer.clip;
            float side = layer.mirror ? -1 : 1;
            for (int i = 0; i < clip.bones().length; i++) {
                String bone = layer.mirror ? clip.mirrored()[i] : clip.bones()[i];
                if (pose.holdingRight && bone.equals("right_arm") || pose.holdingLeft && bone.equals("left_arm")) continue;
                float w = layer.weight * (lower(bone) ? layer.lower : 1);
                if (w <= 0) continue;
                Track rot = clip.rotations()[i], pos = clip.positions()[i];
                if (bone.equals(Clip.WAIST) || bone.equals(Clip.ROOT)) {
                    float[] into = bone.equals(Clip.WAIST) ? WAIST : ROOT;
                    if (rot != null) {
                        rot.sample(layer.time, SAMPLE, 0);
                        into[0] += SAMPLE[0] * w;
                        into[1] += SAMPLE[1] * side * w;
                        into[2] += SAMPLE[2] * side * w;
                    }
                    if (pos != null) {
                        pos.sample(layer.time, SAMPLE, 0);
                        ROOT_POS[0] += SAMPLE[0] * side * w;
                        ROOT_POS[1] += SAMPLE[1] * w;
                        ROOT_POS[2] += SAMPLE[2] * w;
                    }
                    continue;
                }
                ModelPart part = part(root, parts, bone);
                if (part == null) continue;
                if (rot != null) {
                    rot.sample(layer.time, SAMPLE, 0);
                    part.xRot += SAMPLE[0] * w * Mth.DEG_TO_RAD;
                    part.yRot += SAMPLE[1] * side * w * Mth.DEG_TO_RAD;
                    part.zRot += SAMPLE[2] * side * w * Mth.DEG_TO_RAD;
                }
                if (pos != null) {
                    pos.sample(layer.time, SAMPLE, 0);
                    part.x += SAMPLE[0] * side * w;
                    part.y += SAMPLE[1] * w;
                    part.z += SAMPLE[2] * w;
                }
            }
        }
        if (turns(WAIST)) {
            rotation(WAIST);
            float hip = hip(root, parts, pack);
            for (String name : pack.upper()) {
                ModelPart part = part(root, parts, name);
                if (part != null) pivot(part, 0, hip, 0);
            }
        }
        if (turns(ROOT)) {
            rotation(ROOT);
            pivot(root, 0, pack.hip(), 0);   // a Cirri turns about its middle: it is in the air, not standing
        }
        root.x += ROOT_POS[0];
        root.y += ROOT_POS[1];
        root.z += ROOT_POS[2];
    }

    /**
     * Where this model's hips are: where its legs hang from (so a child, or a Lord a head taller, bends at its own
     * hips), or the pack's hip height for a people without legs.
     */
    private static float hip(ModelPart root, Map<String, Optional<ModelPart>> parts, Pack pack) {
        // only legs hung from the root give the hip height; a Cirri's legs hang from its body (their pose is relative
        // to it, so it says nothing about where the hips are): the pack's own hip height, then
        if (!root.hasChild("right_leg") || !root.hasChild("left_leg")) return pack.hip();
        ModelPart right = part(root, parts, "right_leg"), left = part(root, parts, "left_leg");
        return Math.min(right.getInitialPose().y(), left.getInitialPose().y());
    }

    /** A part by name anywhere in the model, or null; remembered per model. */
    static ModelPart part(ModelPart root, Map<String, Optional<ModelPart>> cache, String name) {
        return cache.computeIfAbsent(name, n -> Optional.ofNullable(find(root, n))).orElse(null);
    }

    private static ModelPart find(ModelPart root, String name) {
        if (root.hasChild(name)) return root.getChild(name);
        for (ModelPart p : root.getAllParts()) {
            if (p != root && p.hasChild(name)) return p.getChild(name);
        }
        return null;
    }

    private static boolean lower(String bone) {
        return bone.equals(Clip.ROOT) || bone.equals(Clip.WAIST) || bone.contains("leg") || bone.contains("shin") || bone.contains("foot");
    }

    private static boolean turns(float[] r) {
        return r[0] != 0 || r[1] != 0 || r[2] != 0;
    }

    private static void rotation(float[] r) {
        TURN.rotationZYX(r[2] * Mth.DEG_TO_RAD, r[1] * Mth.DEG_TO_RAD, r[0] * Mth.DEG_TO_RAD);
    }

    /** Turns a part about a fixed point in its parent's space, composing with its own rotation. */
    private static void pivot(ModelPart part, float px, float py, float pz) {
        POINT.set(part.x - px, part.y - py, part.z - pz);
        TURN.transform(POINT);
        part.x = POINT.x + px;
        part.y = POINT.y + py;
        part.z = POINT.z + pz;
        PART.rotationZYX(part.zRot, part.yRot, part.xRot);
        TURN.mul(PART, PART).getEulerAnglesZYX(EULER);
        part.setRotation(EULER.x, EULER.y, EULER.z);
    }

    private Poser() {}
}
