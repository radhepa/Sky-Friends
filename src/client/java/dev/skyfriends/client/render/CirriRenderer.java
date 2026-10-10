package dev.skyfriends.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.skyfriends.SkyFriends;
import dev.skyfriends.client.model.CirriModel;
import dev.skyfriends.client.model.Geometry;
import dev.skyfriends.entity.Cirri;
import dev.skyfriends.entity.CirriKin;
import dev.skyfriends.face.LivingFace;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

/**
 * Draws a Cirri: the woman's, man's or child's model, posed by how it is flying (or asleep, or at
 * work), in its own look (complexion and outfit), with its glowing sky-stones and gold thread, and
 * the living eyes looking back at a camera close in front of it, as Village Friends residents do.
 */
public class CirriRenderer extends MobRenderer<Cirri, CirriRenderState, CirriModel> {
    private final CirriModel woman, man, child;
    private final Map<String, Identifier> textures = new HashMap<>();
    private final Map<String, RenderType> glows = new HashMap<>();

    public CirriRenderer(EntityRendererProvider.Context context) {
        super(context, new CirriModel(context.bakeLayer(Geometry.layer("cirri")), "cirri"), 0.45F);
        this.woman = this.model;
        this.man = new CirriModel(context.bakeLayer(Geometry.layer("cirri_male")), "cirri_male");
        this.child = new CirriModel(context.bakeLayer(Geometry.layer("cirri_child")), "cirri_child");
        addLayer(new RenderLayer<>(this) {
            @Override
            public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, CirriRenderState state, float yRot, float xRot) {
                RenderType glow = glows.computeIfAbsent(state.texture, t -> RenderTypes.eyes(SkyFriends.id("textures/entity/" + t + "_glow.png")));
                collector.order(1).submitModel(getParentModel(), state, poseStack, glow, light, OverlayTexture.NO_OVERLAY, state.outlineColor);
            }
        });
    }

    private CirriModel modelFor(CirriRenderState state) {
        return state.isBaby ? child : state.female ? woman : man;
    }

    @Override
    public void submit(CirriRenderState state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        this.model = modelFor(state);
        super.submit(state, poseStack, collector, camera);
    }

    /** The child's model is drawn at its own size (the geometry's scale), not vanilla's baby scale. */
    @Override
    protected void scale(CirriRenderState state, PoseStack poseStack) {
        float s = Geometry.scale(modelFor(state).id());
        if (s != 1.0F) poseStack.scale(s, s, s);
    }

    @Override
    public Identifier getTextureLocation(CirriRenderState state) {
        return textures.computeIfAbsent(state.texture, t -> SkyFriends.id("textures/entity/" + t + ".png"));
    }

    @Override
    public CirriRenderState createRenderState() {
        return new CirriRenderState();
    }

    @Override
    public void extractRenderState(Cirri cirri, CirriRenderState state, float delta) {
        super.extractRenderState(cirri, state, delta);
        state.flight = Mth.lerp(delta, cirri.flightO, cirri.flight);
        state.bank = Mth.lerp(delta, cirri.bankO, cirri.bank);
        state.climb = Mth.lerp(delta, cirri.climbO, cirri.climb);
        state.sleeping = cirri.state() == Cirri.SLEEPING;
        state.working = cirri.state() == Cirri.WORKING;
        state.female = cirri.female();
        state.texture = cirri.isBaby() ? "cirri_child_" + (state.female ? "f" : "m") + "_" + cirri.complexion()
                : "cirri_" + (state.female ? "f" : "m") + "_" + cirri.complexion() + "_" + CirriKin.PALETTE_NAMES.get(cirri.palette());
        state.motionSeed = LivingFace.seed(cirri.getUUID());
        state.feminine = state.female;       // as in Village Friends: women wear the feminine details, men never
        // eye contact, as a Village Friends resident makes it: only with a camera close by and already in front of the face
        state.eyeLookX = state.eyeLookY = state.attention = 0;
        var camera = Minecraft.getInstance().getCameraEntity();
        if (camera != null && cirri.isAlive() && !state.sleeping) {
            Vec3 offset = camera.getEyePosition(delta).subtract(cirri.getEyePosition(delta));
            double horizontal = Math.sqrt(offset.x * offset.x + offset.z * offset.z);
            float yaw = (float) Math.toDegrees(Math.atan2(-offset.x, offset.z));
            float relative = Mth.wrapDegrees(yaw - Mth.rotLerp(delta, cirri.yHeadRotO, cirri.yHeadRot));
            float proximity = LivingFace.smooth((float) ((6 - offset.length()) / 2));
            float facing = LivingFace.smooth((65 - Math.abs(relative)) / 25);
            state.attention = proximity * facing;
            state.eyeLookX = Mth.clamp(relative / 65, -.28F, .28F) * state.attention;
            float pitch = (float) -Math.toDegrees(Math.atan2(offset.y, horizontal));
            state.eyeLookY = Mth.clamp((pitch - state.xRot) / 90, -.12F, .12F) * state.attention;
        }
    }
}
