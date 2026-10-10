package dev.skyfriends.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.skyfriends.client.EmoteBubbles;
import dev.skyfriends.client.anim.Life;
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
    /** Set while the conversation window draws a portrait: no bubble over its head there (the window shows its own). */
    public static boolean portrait;
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
        if (state.bubble != null && state.distanceToCameraSq < 40 * 40) submitBubble(state, poseStack, collector, camera);
    }

    /** The emote bubble, as a card facing the camera above the head (and above the name, when shown). */
    private static void submitBubble(CirriRenderState state, PoseStack pose, SubmitNodeCollector collector, CameraRenderState camera) {
        var bubble = state.bubble;
        float age = state.bubbleAge;
        float scale = EmoteBubbles.scale(bubble, age);
        if (scale <= .01F) return;
        var anchor = state.nameTagAttachment;
        double y = state.nameTag != null && anchor != null ? anchor.y + .78 : state.boundingBoxHeight + .32;
        pose.pushPose();
        pose.translate(anchor == null ? 0 : anchor.x, y, anchor == null ? 0 : anchor.z);
        pose.rotate(camera.orientation);
        float pixel = .019F * scale;
        pose.scale(pixel, -pixel, pixel);
        float bob = EmoteBubbles.bob(age);
        int shape = EmoteBubbles.shape(bubble.emote()), symbol = EmoteBubbles.symbol(bubble.emote(), age);
        float[] motion = EmoteBubbles.symbolMotion(bubble.emote(), age);
        collector.submitCustomGeometry(pose, RenderTypes.text(EmoteBubbles.SHEET), (p, vc) -> {
            quad(p, vc, -16, -32 + bob, 32, 32, 0, shape * 32, 0, 0, 0);
            // the symbol sits in the middle of the bubble's body, a hair closer to the camera
            float cx = motion[0], cy = -19 + bob + motion[1], half = 7.5F * motion[2];
            quad(p, vc, cx - half, cy - half, half * 2, half * 2, 32 + symbol / 8 * 16, symbol % 8 * 16, 16, .3F, motion[3]);
        });
        pose.popPose();
    }

    /** One textured square in sheet pixels ({@code row} down, {@code column} across), optionally turned. */
    private static void quad(PoseStack.Pose p, VertexConsumer vc, float x, float y, float w, float h, int row, int column, int size, float z, float degrees) {
        int cell = size == 0 ? 32 : size;
        float u0 = column / 128F, v0 = row / 128F, u1 = (column + cell) / 128F, v1 = (row + cell) / 128F;
        float cx = x + w / 2, cy = y + h / 2, cos = Mth.cos(degrees * Mth.DEG_TO_RAD), sin = Mth.sin(degrees * Mth.DEG_TO_RAD);
        float[][] corners = {{x, y, u0, v0}, {x, y + h, u0, v1}, {x + w, y + h, u1, v1}, {x + w, y, u1, v0}};
        for (var c : corners) {
            float dx = c[0] - cx, dy = c[1] - cy;
            vc.addVertex(p, cx + dx * cos - dy * sin, cy + dx * sin + dy * cos, z).setColor(0xFFFFFFFF).setUv(c[2], c[3]).setLight(0xF000F0);
        }
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
        Life.fill(cirri, state.pose, delta);
        state.bubble = portrait ? null : EmoteBubbles.get(cirri.getId());
        // the conversation window already shows their name: no floating label behind the portrait
        if (Minecraft.getInstance().gui.screen() instanceof dev.skyfriends.client.screen.TalkScreen) state.nameTag = null;
        state.bubbleAge = state.bubble == null ? 0 : state.bubble.age(delta);
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
