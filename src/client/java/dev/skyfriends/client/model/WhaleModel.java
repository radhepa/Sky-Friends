package dev.skyfriends.client.model;

import dev.skyfriends.client.render.CreatureRenderState;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.util.Mth;

/** A Cloud Whale: a slow wave runs down its body to the flukes, its long flippers stroke, its great head nods. */
public class WhaleModel extends EntityModel<CreatureRenderState> {
    private final ModelPart body, head, tail, tail2, tail3, fluke, rightFlipper, leftFlipper;

    public WhaleModel(ModelPart root) {
        super(root, RenderTypes::entityCutout);
        body = Geometry.part(root, "cloud_whale", "body");
        head = Geometry.part(root, "cloud_whale", "head");
        tail = Geometry.part(root, "cloud_whale", "tail");
        tail2 = Geometry.part(root, "cloud_whale", "tail2");
        tail3 = Geometry.part(root, "cloud_whale", "tail3");
        fluke = Geometry.part(root, "cloud_whale", "fluke");
        rightFlipper = Geometry.part(root, "cloud_whale", "right_flipper");
        leftFlipper = Geometry.part(root, "cloud_whale", "left_flipper");
    }

    @Override
    public void setupAnim(CreatureRenderState s) {
        super.setupAnim(s);
        float w = s.phase;
        body.y += Mth.sin(w) * 1.0F;
        body.xRot += Mth.sin(w + 0.5F) * 0.03F;
        head.xRot += Mth.sin(w + 0.6F) * 0.04F;
        tail.xRot += Mth.sin(w) * 0.12F;
        tail2.xRot += Mth.sin(w - 0.7F) * 0.18F;
        tail3.xRot += Mth.sin(w - 1.4F) * 0.24F;
        fluke.xRot += Mth.sin(w - 2.1F) * 0.35F;
        rightFlipper.zRot += Mth.sin(w * 0.8F) * 0.25F;
        leftFlipper.zRot -= Mth.sin(w * 0.8F) * 0.25F;
        rightFlipper.xRot += Mth.sin(w * 0.8F + 0.5F) * 0.1F;
        leftFlipper.xRot += Mth.sin(w * 0.8F + 0.5F) * 0.1F;
    }
}
