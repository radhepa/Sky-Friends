package dev.skyfriends.client.model;

import dev.skyfriends.client.render.CirriRenderState;
import dev.skyfriends.face.LivingFace;
import dev.skyfriends.face.LivingFace.EyeStyle;
import dev.skyfriends.face.LivingFace.Swatch;
import java.util.Set;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.core.Direction;
import net.minecraft.util.Mth;

/**
 * The living eyes of Village Friends residents, on a Sky Friends head: eye whites, pupils, irises, a
 * skin lid, the lash line, a feminine lash wing, brows, a mouth or rosy lips and a blush, each a
 * one-pixel plane in front of the clean face, sampling one colour of the face swatch strip. The
 * placement, blinking, glances and eye contact are Village Friends' own (its ResidentModel), so the
 * two mods' people have the same eyes. The head must be the usual 8x8x8 head at (-4, -8, -4).
 */
public final class LivingEyes {
    private final ModelPart[] scleras = new ModelPart[2], pupils = new ModelPart[2], irises = new ModelPart[2], lids = new ModelPart[2];
    private final ModelPart[] lashes = new ModelPart[2], wings = new ModelPart[2], brows = new ModelPart[2], browTails = new ModelPart[2], blushes = new ModelPart[2];
    private final ModelPart mouth, lips;

    public LivingEyes(ModelPart head) {
        for (int i = 0; i < 2; i++) {
            ModelPart eye = head.getChild("eye" + i);
            scleras[i] = eye.getChild("sclera");
            pupils[i] = eye.getChild("pupil");
            irises[i] = eye.getChild("iris");
            lids[i] = eye.getChild("lid");
            lashes[i] = eye.getChild("lash");
            wings[i] = eye.getChild("wing");
            brows[i] = head.getChild("brow" + i);
            browTails[i] = head.getChild("browTail" + i);
            blushes[i] = head.getChild("blush" + i);
        }
        mouth = head.getChild("mouth");
        lips = head.getChild("lips");
    }

    /** The planes, placed exactly as on a Village Friends resident; {@code (u, v)} is the swatch strip. */
    static void addPlanes(PartDefinition head, int u, int v) {
        for (int i = 0; i < 2; i++) {
            int side = i == 0 ? -1 : 1;
            PartDefinition eye = head.addOrReplaceChild("eye" + i, CubeListBuilder.create(), PartPose.ZERO);
            plane(eye, "sclera", u, v, Swatch.TINT, side * 2F, -3.5F, -4.03F, 2, 1);
            plane(eye, "white", u, v, Swatch.WHITE, side * 2F, -2.5F, -4.03F, 2, 1);
            plane(eye, "pupil", u, v, Swatch.PUPIL, side * 1.5F, -3.5F, -4.045F, 1, 1);
            plane(eye, "iris", u, v, Swatch.IRIS, side * 1.5F, -2.5F, -4.045F, 1, 1);
            plane(eye, "lid", u, v, Swatch.LID, side * 2F, -4.5F, -4.065F, 2, 0);
            plane(eye, "lash", u, v, Swatch.LASH, side * 2F, -4.5F, -4.08F, 2, 1);
            plane(eye, "wing", u, v, Swatch.LASH, side * 3.5F, -3.5F, -4.08F, 1, 1);
            plane(head, "brow" + i, u, v, Swatch.BROW, side * 2F, -5.725F, -4.03F, 2, .55F);
            plane(head, "browTail" + i, u, v, Swatch.BROW, side * 2.75F, -5.625F, -4.03F, .5F, .35F);
            plane(head, "blush" + i, u, v, Swatch.BLUSH, side * 2.875F, -1.725F, -4.02F, 1.25F, .55F);
        }
        plane(head, "mouth", u, v, Swatch.LIP, 0, -1.425F, -4.02F, 1.5F, .45F);
        plane(head, "lips", u, v, Swatch.ROSE_LIP, 0, -1.45F, -4.02F, 1, .5F);
    }

    private static void plane(PartDefinition parent, String name, int u, int v, Swatch swatch, float x, float y, float z, float w, float h) {
        parent.addOrReplaceChild(name, CubeListBuilder.create().texOffs(u + swatch.ordinal(), v)
                        .addBox(-.5F, -.5F, 0, 1, 1, 0, Set.of(Direction.NORTH)),
                PartPose.ZERO.scaled(w, h, 1).translated(x, y, z));
    }

    /** Blink, glance and keep eye contact, as a Village Friends resident does. */
    public void animate(CirriRenderState s) {
        boolean closed = s.deathTime > 0 || s.sleeping;
        float blink = Mth.clamp(closed ? 1 : LivingFace.blink(s.ageInTicks, s.motionSeed), 0, 1);
        float glance = LivingFace.glance(s.ageInTicks, s.motionSeed);
        float gazeX = Mth.clamp(s.eyeLookX + glance * (1 - s.attention), -.28F, .28F);
        float gazeY = Mth.clamp(s.eyeLookY, -.09F, .09F);

        EyeStyle style = LivingFace.eyeStyle(s.motionSeed);
        boolean starlit = style == EyeStyle.STARLIT;
        boolean feminine = s.feminine;
        float top = LivingFace.eyeTop(style), bottom = LivingFace.EYE_BOTTOM;
        float lashHeight = LivingFace.lashHeight(blink), lashBottom = LivingFace.lashBottom(style, blink);
        float lidTop = top - 1, lidBottom = lashBottom - lashHeight;
        float wingHeight = LivingFace.wingHeight(blink), wingTop = LivingFace.wingTop(style, blink);
        float browTop = LivingFace.browTop(style);
        for (int i = 0; i < 2; i++) {
            float side = i == 0 ? -1 : 1, inner = side * 1.5F, near = side < 0 ? -3 : 1, far = side < 0 ? -1 : 3;
            // the iris rests in the inner column and glances by sliding, trimmed to the eye's edges
            scleras[i].visible = starlit;
            fit(pupils[i], starlit, inner + gazeX, -3.5F + gazeY, near, far, top, bottom);
            fit(irises[i], true, inner + gazeX, -2.5F + gazeY, near, far, top, bottom);
            // the lash line sweeps down over the eye; the skin lid follows behind it
            lids[i].visible = lidBottom - lidTop > .001F;
            lids[i].y = (lidTop + lidBottom) / 2;
            lids[i].yScale = lidBottom - lidTop;
            lashes[i].y = lashBottom - lashHeight / 2;
            lashes[i].yScale = lashHeight;
            wings[i].visible = feminine;
            wings[i].y = wingTop + wingHeight / 2;
            wings[i].yScale = wingHeight;
            // straight, fuller brows for masculine faces; a finer arch with a dipping tail for feminine
            browTails[i].visible = feminine;
            blushes[i].visible = feminine;
            if (feminine) {
                brows[i].x = side * 1.75F;
                brows[i].xScale = 1.5F;
                brows[i].y = browTop + .175F;
                brows[i].yScale = .45F;
                browTails[i].y = browTop + .375F;
            } else {
                brows[i].y = browTop + .275F;
            }
        }
        mouth.visible = !feminine;
        lips.visible = feminine;
    }

    /** Places a one-pixel plane at a centre, trimmed to the open eye. */
    private static void fit(ModelPart part, boolean shown, float x, float y, float left, float right, float top, float bottom) {
        float x0 = Math.max(x - .5F, left), x1 = Math.min(x + .5F, right), y0 = Math.max(y - .5F, top), y1 = Math.min(y + .5F, bottom);
        part.visible = shown && x1 > x0 && y1 > y0;
        part.x = (x0 + x1) / 2;
        part.y = (y0 + y1) / 2;
        part.xScale = Math.max(0, x1 - x0);
        part.yScale = Math.max(0, y1 - y0);
    }
}
