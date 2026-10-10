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
import dev.skyfriends.anim.Cue;
import dev.skyfriends.client.anim.Life;
import dev.skyfriends.client.screen.TalkScreen;
import dev.skyfriends.entity.Cirri;
import dev.skyfriends.life.ArrivalPayload;
import dev.skyfriends.life.Emote;
import dev.skyfriends.life.EmotePayload;
import dev.skyfriends.talk.TalkPayload;
import java.util.Set;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.LivingEntity;

/**
 * Client wiring: a model layer per geometry file and a renderer per mob; the conversation window opening (or
 * updating) whenever the server sends a {@link TalkPayload}; emote bubbles and the village title card; and the
 * Cirri's animation pack (docs/ANIMATIONS.md).
 */
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

        ClientPlayNetworking.registerGlobalReceiver(TalkPayload.TYPE, (payload, context) -> {
            var client = context.client();
            if (client.gui.screen() instanceof TalkScreen screen && screen.matches(payload)) screen.update(payload);
            else if (payload.opening() && client.player != null) client.gui.setScreen(new TalkScreen(payload));
        });
        ClientPlayNetworking.registerGlobalReceiver(EmotePayload.TYPE, (payload, context) ->
                EmoteBubbles.show(payload.entityId(), Emote.parse(payload.emote()), payload.delay()));
        ClientPlayNetworking.registerGlobalReceiver(ArrivalPayload.TYPE, (payload, context) ->
                ArrivalBanner.show(payload.village(), payload.above(), payload.below()));
        ClientTickEvents.END_CLIENT_TICK.register(EmoteBubbles::tick);
        ArrivalBanner.register();
        ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> client.execute(() -> {
            EmoteBubbles.clear();
            ArrivalBanner.clear();
            Life.clear();
        }));
        animations();
    }

    /**
     * The Cirri's animation pack: who plays it, when they can't (asleep, fleeing), how much they're on the move
     * (their flight: clips play while they hover), and the tags that pick clips (job, manner, at work).
     */
    static void animations() {
        Life.register(SkyEntities.CIRRI, new Life.Kind("cirri", e -> e instanceof Cirri c && !c.asleep(),
                SkyFriendsClient::tags, LivingEntity::isBaby, (e, partial) -> e instanceof Cirri c ? Mth.lerp(partial, c.flightO, c.flight) * 1.6F : 0F));
        // in a conversation: 2 while their line types out, 1 while you choose what to say
        Life.conversation = e -> Minecraft.getInstance().gui.screen() instanceof TalkScreen t && t.data().entityId() == e.getId()
                ? (t.speaking() ? 2 : 1) : 0;
        ClientTickEvents.END_CLIENT_TICK.register(Life::tickAll);
        ClientPlayNetworking.registerGlobalReceiver(Cue.TYPE, (cue, context) -> Life.cue(cue.entityId(), cue.trigger()));
    }

    /** job:&lt;job&gt;, manner:&lt;manner&gt; and routine:&lt;routine&gt; from the synced motion string, and working while at work. */
    static void tags(LivingEntity e, Set<String> tags) {
        if (!(e instanceof Cirri c)) return;
        String[] motion = c.motion().split("[|]");
        if (motion.length > 0 && !motion[0].isEmpty()) tags.add("job:" + motion[0]);
        if (motion.length > 1 && !motion[1].isEmpty()) tags.add("manner:" + motion[1]);
        if (motion.length > 2 && !motion[2].isEmpty()) tags.add("routine:" + motion[2]);
        if (c.state() == Cirri.WORKING) tags.add("working");
    }
}
