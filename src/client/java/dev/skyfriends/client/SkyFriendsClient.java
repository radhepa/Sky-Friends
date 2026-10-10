package dev.skyfriends.client;

import dev.skyfriends.SkyEntities;
import dev.skyfriends.client.model.Geometry;
import dev.skyfriends.client.model.KoiModel;
import dev.skyfriends.client.model.WhaleModel;
import dev.skyfriends.client.render.CirriRenderer;
import dev.skyfriends.client.render.CreatureRenderer;
import dev.skyfriends.entity.CloudKoi;
import dev.skyfriends.entity.CloudWhale;
import dev.skyfriends.registry.MobEntry;
import dev.skyfriends.registry.MobRegistry;
import java.util.List;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.minecraft.util.Mth;

/** Client wiring: a model layer per geometry file and a renderer per mob. */
public final class SkyFriendsClient implements ClientModInitializer {
    /** Geometry files that are not a mob of their own (the Cirri men and children). */
    private static final List<String> EXTRA_MODELS = List.of("cirri_male", "cirri_child");
    private static final String[] COATS = {"kohaku", "yamabuki", "sora"};

    @Override
    public void onInitializeClient() {
        for (MobEntry<?> e : MobRegistry.all()) ModelLayerRegistry.registerModelLayer(Geometry.layer(e.id), () -> Geometry.load(e.id));
        for (String id : EXTRA_MODELS) ModelLayerRegistry.registerModelLayer(Geometry.layer(id), () -> Geometry.load(id));
        EntityRendererRegistry.register(SkyEntities.CIRRI, CirriRenderer::new);
        EntityRendererRegistry.register(SkyEntities.CLOUD_KOI, ctx -> new CreatureRenderer<CloudKoi, KoiModel>(ctx, "cloud_koi",
                new KoiModel(ctx.bakeLayer(Geometry.layer("cloud_koi"))), 0.2F, (koi, s) -> {
                    s.texture = "cloud_koi_" + COATS[koi.coat()];
                    s.phase = Mth.lerp(s.delta, koi.swimO, koi.swim);
                }));
        EntityRendererRegistry.register(SkyEntities.CLOUD_WHALE, ctx -> new CreatureRenderer<CloudWhale, WhaleModel>(ctx, "cloud_whale",
                new WhaleModel(ctx.bakeLayer(Geometry.layer("cloud_whale"))), 2.5F,
                (whale, s) -> s.phase = Mth.lerp(s.delta, whale.waveO, whale.wave)));
    }
}
