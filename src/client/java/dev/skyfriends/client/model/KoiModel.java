package dev.skyfriends.client.model;

import dev.skyfriends.client.render.CreatureRenderState;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.util.Mth;

/** A Cloud Koi swimming through the air: the beat runs down its body to the long tail fin, its side fins flutter. */
public class KoiModel extends EntityModel<CreatureRenderState> {
    private final ModelPart body, head, tail, tail2, fluke, rightFin, leftFin, dorsal;

    public KoiModel(ModelPart root) {
        super(root, RenderTypes::entityCutout);
        body = Geometry.part(root, "cloud_koi", "body");
        head = Geometry.part(root, "cloud_koi", "head");
        tail = Geometry.part(root, "cloud_koi", "tail");
        tail2 = Geometry.part(root, "cloud_koi", "tail2");
        fluke = Geometry.part(root, "cloud_koi", "fluke");
        rightFin = Geometry.part(root, "cloud_koi", "right_fin");
        leftFin = Geometry.part(root, "cloud_koi", "left_fin");
        dorsal = Geometry.part(root, "cloud_koi", "dorsal");
    }

    @Override
    public void setupAnim(CreatureRenderState s) {
        super.setupAnim(s);
        float p = s.phase * 0.6F;
        body.xRot += s.xRot * Mth.DEG_TO_RAD;
        body.yRot += Mth.sin(p + 0.6F) * 0.06F;
        head.yRot -= Mth.sin(p) * 0.08F;
        tail.yRot += Mth.sin(p) * 0.35F;
        tail2.yRot += Mth.sin(p - 0.8F) * 0.45F;
        fluke.yRot += Mth.sin(p - 1.5F) * 0.5F;
        dorsal.zRot += Mth.sin(p - 0.4F) * 0.08F;
        rightFin.zRot += Mth.sin(p * 0.8F) * 0.4F;
        leftFin.zRot -= Mth.sin(p * 0.8F) * 0.4F;
        body.y += Mth.sin(s.ageInTicks * 0.1F) * 0.3F;
    }
}
