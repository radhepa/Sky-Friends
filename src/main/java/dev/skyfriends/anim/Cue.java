package dev.skyfriends.anim;

import dev.skyfriends.SkyFriends;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;

/**
 * Server to client: a moment someone reacts to ("happy", "thanks", "decline", "pleased", "annoyed"), so everyone
 * watching sees them act it out with a clip from their people's animation pack.
 */
public record Cue(int entityId, String trigger) implements CustomPacketPayload {
    public static final Type<Cue> TYPE = new Type<>(SkyFriends.id("cue"));
    public static final StreamCodec<FriendlyByteBuf, Cue> CODEC = StreamCodec.of(
            (buf, v) -> {
                buf.writeVarInt(v.entityId);
                buf.writeUtf(v.trigger, 32);
            },
            buf -> new Cue(buf.readVarInt(), buf.readUtf(32)));

    public static void init() {
        PayloadTypeRegistry.clientboundPlay().register(TYPE, CODEC);
    }

    /** Tells everyone who can see this person (and the player talking to them) to play the reaction. */
    public static void send(LivingEntity who, String trigger, ServerPlayer talker) {
        Cue cue = new Cue(who.getId(), trigger);
        boolean told = false;
        for (ServerPlayer p : PlayerLookup.tracking(who)) {
            ServerPlayNetworking.send(p, cue);
            told |= p == talker;
        }
        if (!told && talker != null) ServerPlayNetworking.send(talker, cue);
    }

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
