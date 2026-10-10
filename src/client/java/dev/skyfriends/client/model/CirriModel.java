package dev.skyfriends.client.model;

import dev.skyfriends.client.anim.Poser;
import dev.skyfriends.client.render.CirriRenderState;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.util.Mth;

/**
 * A Cirri never stands: it is always flying, and its pose blends between two ways of being in the air
 * by {@code flight} (0..1, from how fast it is really moving).
 *
 * <ul>
 *   <li><b>Hovering</b>: upright on nothing, bobbing gently; arms float out and drift as if treading
 *       water, legs hang with soft knees and tread slowly; the two veils float round it in slow,
 *       wide waves, flaring out at the sides like weed in a current.</li>
 *   <li><b>Cruising</b>: the body stretches out flat, chest first, the way the flying musicians are
 *       painted: legs together behind with one knee bent up, arms spread and swept back, the veils,
 *       hair, sash and wrist ribbons streaming behind in quick ripples that travel down their length.</li>
 * </ul>
 * Turning, it rolls into the turn (the inside arm dips); climbing, it lifts its chest; the neck keeps
 * the head level so it looks where it is going (and at you). The face has Village Friends' living eyes.
 */
public class CirriModel extends EntityModel<CirriRenderState> {
    private static final int VEIL = 4;

    private final ModelPart body, neck, head, hair, hair2, sash;
    private final ModelPart rightArm, leftArm, rightForearm, leftForearm, rightLeg, leftLeg, rightShin, leftShin;
    private final ModelPart rightRibbon, rightRibbon2, leftRibbon, leftRibbon2;
    private final ModelPart[] rightVeil = new ModelPart[VEIL], leftVeil = new ModelPart[VEIL];
    private final LivingEyes eyes;
    private final String id;

    public CirriModel(ModelPart root, String id) {
        super(root, RenderTypes::entityCutout);
        this.id = id;
        body = part("body");
        neck = part("neck");
        head = part("head");
        hair = part("hair");
        hair2 = part("hair2");
        sash = part("sash");
        rightArm = part("right_arm");
        leftArm = part("left_arm");
        rightForearm = part("right_forearm");
        leftForearm = part("left_forearm");
        rightLeg = part("right_leg");
        leftLeg = part("left_leg");
        rightShin = part("right_shin");
        leftShin = part("left_shin");
        rightRibbon = part("right_ribbon");
        rightRibbon2 = part("right_ribbon2");
        leftRibbon = part("left_ribbon");
        leftRibbon2 = part("left_ribbon2");
        for (int i = 0; i < VEIL; i++) {
            String n = i == 0 ? "" : String.valueOf(i + 1);
            rightVeil[i] = part("right_veil" + n);
            leftVeil[i] = part("left_veil" + n);
        }
        eyes = new LivingEyes(head);
    }

    private ModelPart part(String name) {
        return Geometry.part(root(), id, name);
    }

    public String id() {
        return id;
    }

    @Override
    public void setupAnim(CirriRenderState s) {
        super.setupAnim(s);
        if (s.sleeping) {
            sleep(s);
            eyes.animate(s);
            return;
        }
        float t = s.ageInTicks, f = s.flight, hov = 1.0F - f, bank = s.bank, climb = s.climb;
        float phase = (s.motionSeed & 1023) * 0.0061F;            // each Cirri drifts in its own time
        float tp = t + phase * 40.0F;

        // -- the whole body: upright hovering, stretched out cruising, nose up climbing, rolled into turns --
        float pitch = Mth.lerp(f, 0.06F, 1.3F) - climb * 0.35F * f;
        body.xRot += pitch;
        body.zRot += bank * 0.55F + Mth.sin(tp * 0.045F) * 0.035F * hov;
        body.y += Mth.sin(tp * 0.08F) * 0.9F * (hov + 0.3F) - f * 7.0F;

        // the neck undoes the body's pitch and most of its roll, so the head stays level and looks ahead
        neck.xRot -= pitch;
        neck.zRot -= body.zRot * 0.7F;
        head.yRot += s.yRot * Mth.DEG_TO_RAD;
        head.xRot += s.xRot * Mth.DEG_TO_RAD;

        // -- arms: drifting as if treading water, or spread and swept back --
        float drift = Mth.sin(tp * 0.06F), drift2 = Mth.sin(tp * 0.06F + 1.7F);
        float scull = Mth.sin(tp * 0.09F) * 0.08F;
        rightArm.zRot += Mth.lerp(f, 0.35F + drift * 0.12F, 1.15F + scull) + bank * 0.25F;
        leftArm.zRot -= Mth.lerp(f, 0.3F + drift2 * 0.12F, 1.15F - scull) - bank * 0.25F;
        rightArm.xRot += Mth.lerp(f, -0.25F + Mth.sin(tp * 0.05F) * 0.15F, 0.25F);
        leftArm.xRot += Mth.lerp(f, -0.1F + Mth.sin(tp * 0.05F + 2.0F) * 0.15F, 0.25F);
        rightForearm.xRot += Mth.lerp(f, -0.5F + drift * 0.15F, -0.12F);
        leftForearm.xRot += Mth.lerp(f, -0.35F + drift2 * 0.15F, -0.12F);

        // -- legs: hanging and treading, or together behind with the right knee bent up --
        float tread = Mth.sin(tp * 0.07F), kick = Mth.sin(tp * 0.12F) * 0.05F;
        rightLeg.xRot += Mth.lerp(f, -0.12F + tread * 0.12F, 0.05F + kick);
        leftLeg.xRot += Mth.lerp(f, -0.05F - tread * 0.12F, 0.22F - kick);
        rightShin.xRot += Mth.lerp(f, 0.3F + tread * 0.15F, 1.25F);
        leftShin.xRot += Mth.lerp(f, 0.25F - tread * 0.15F, 0.15F);
        rightLeg.zRot += 0.04F * hov;
        leftLeg.zRot -= 0.04F * hov;

        // -- cloth and hair: slow wide waves hovering, quick ripples streaming behind in flight --
        // The veils also twist about their length (more at speed), and the twist ripples down them like a
        // ribbon's, so they show their faces from the side as well as from above and behind.
        float w = Mth.lerp(f, 0.07F, 0.21F), amp = Mth.lerp(f, 0.32F, 0.2F);
        for (int i = 0; i < VEIL; i++) {
            float k = i == 0 ? 0.6F : 1.0F;
            rightVeil[i].xRot += amp * k * Mth.sin(tp * w - i * 0.9F);
            leftVeil[i].xRot += amp * k * Mth.sin(tp * w - i * 0.9F + 0.6F);
            float twist = Mth.sin(tp * w * 0.8F - i * 1.1F) * Mth.lerp(f, 0.22F, 0.35F);
            rightVeil[i].yRot += twist + Mth.cos(tp * w * 0.7F - i * 0.8F) * 0.12F * hov;
            leftVeil[i].yRot -= twist + Mth.cos(tp * w * 0.7F - i * 0.8F + 0.6F) * 0.12F * hov;
        }
        float flare = (0.25F + Mth.sin(tp * 0.04F) * 0.08F) * hov;
        float turnOut = Mth.lerp(f, 0.45F, 0.8F);
        rightVeil[0].zRot += flare + bank * 0.15F * f;
        leftVeil[0].zRot -= flare - bank * 0.15F * f;
        rightVeil[0].yRot += turnOut;
        leftVeil[0].yRot -= turnOut;
        rightVeil[0].xRot += 0.15F * f;
        leftVeil[0].xRot += 0.15F * f;

        hair.xRot += f * 0.9F + Mth.sin(tp * w - 0.5F) * 0.1F * (0.5F + f);
        hair2.xRot += f * 0.2F + Mth.sin(tp * w - 1.2F) * 0.18F;
        sash.xRot += f * 1.1F + Mth.sin(tp * 0.15F) * 0.1F;
        float rw = w * 1.3F;
        rightRibbon.xRot += Mth.sin(tp * rw - 0.4F) * 0.3F + f * 0.5F;
        rightRibbon2.xRot += Mth.sin(tp * rw - 1.2F) * 0.4F;
        leftRibbon.xRot += Mth.sin(tp * rw + 0.3F) * 0.3F + f * 0.5F;
        leftRibbon2.xRot += Mth.sin(tp * rw - 0.5F) * 0.4F;

        // while they act out a clip, their own working gestures rest
        if (s.working && !s.pose.any()) {
            // busy hands at their work, head bowed over it
            rightArm.xRot -= 0.85F + Mth.sin(tp * 0.25F) * 0.22F;
            leftArm.xRot -= 0.7F + Mth.cos(tp * 0.21F) * 0.2F;
            rightForearm.xRot -= 0.35F + Mth.sin(tp * 0.25F + 0.5F) * 0.2F;
            leftForearm.xRot -= 0.3F;
            rightArm.zRot -= 0.25F;
            leftArm.zRot += 0.2F;
            head.xRot += 0.3F;
        }
        Poser.apply(root(), s.pose);
        eyes.animate(s);
    }

    /** Asleep in the air over its cushion: curled up, knees drawn in, arms folded, head bowed, the veils drifting round it. */
    private void sleep(CirriRenderState s) {
        float t = s.ageInTicks, breathe = Mth.sin(t * 0.05F);
        body.xRot += 0.35F;
        body.y += 1.5F + breathe * 0.4F;
        neck.xRot -= 0.15F;
        head.xRot += 0.55F;
        rightLeg.xRot -= 1.1F;
        leftLeg.xRot -= 1.0F;
        rightShin.xRot += 1.7F;
        leftShin.xRot += 1.6F;
        rightArm.xRot -= 0.8F;
        leftArm.xRot -= 0.8F;
        rightArm.zRot -= 0.35F;
        leftArm.zRot += 0.35F;
        rightForearm.xRot -= 1.0F;
        leftForearm.xRot -= 1.0F;
        hair.xRot += 0.2F;
        for (int i = 0; i < VEIL; i++) {
            float wave = Mth.sin(t * 0.03F - i * 0.7F) * 0.18F;
            rightVeil[i].xRot += wave + (i == 0 ? -0.5F : 0.35F);
            leftVeil[i].xRot += wave + (i == 0 ? -0.5F : 0.35F);
        }
        rightVeil[0].zRot += 0.5F;
        leftVeil[0].zRot -= 0.5F;
    }
}
