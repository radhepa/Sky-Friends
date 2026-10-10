package dev.skyfriends.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.skyfriends.SkyFriends;
import dev.skyfriends.client.model.Geometry;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.function.BiConsumer;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Mob;

/** Renderer for the sky creatures: the geometry's own scale, a texture per state, and a glow layer when the art has one. */
public class CreatureRenderer<T extends Mob, M extends EntityModel<CreatureRenderState>> extends MobRenderer<T, CreatureRenderState, M> {
    private final String id;
    private final BiConsumer<T, CreatureRenderState> extract;
    private final Map<String, Identifier> textures = new HashMap<>();
    private final Map<String, Optional<RenderType>> glows = new HashMap<>();

    public CreatureRenderer(EntityRendererProvider.Context context, String id, M model, float shadow, BiConsumer<T, CreatureRenderState> extract) {
        super(context, model, shadow);
        this.id = id;
        this.extract = extract;
        addLayer(new RenderLayer<>(this) {
            @Override
            public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, CreatureRenderState state, float yRot, float xRot) {
                RenderType glow = glows.computeIfAbsent(state.texture, t -> {
                    String path = "textures/entity/" + t + "_glow.png";
                    return CreatureRenderer.class.getResource("/assets/" + SkyFriends.MOD_ID + "/" + path) == null ? Optional.empty()
                            : Optional.of(RenderTypes.eyes(SkyFriends.id(path)));
                }).orElse(null);
                if (glow != null) collector.order(1).submitModel(getParentModel(), state, poseStack, glow, light, OverlayTexture.NO_OVERLAY, state.outlineColor);
            }
        });
    }

    @Override
    protected void scale(CreatureRenderState state, PoseStack poseStack) {
        float s = Geometry.scale(id);
        if (s != 1.0F) poseStack.scale(s, s, s);
    }

    @Override
    public Identifier getTextureLocation(CreatureRenderState state) {
        return textures.computeIfAbsent(state.texture, t -> SkyFriends.id("textures/entity/" + t + ".png"));
    }

    @Override
    public CreatureRenderState createRenderState() {
        return new CreatureRenderState();
    }

    @Override
    public void extractRenderState(T entity, CreatureRenderState state, float delta) {
        super.extractRenderState(entity, state, delta);
        state.texture = id;
        state.delta = delta;
        extract.accept(entity, state);
    }
}
