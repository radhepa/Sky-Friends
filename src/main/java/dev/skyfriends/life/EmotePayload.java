package dev.skyfriends.life;

import dev.skyfriends.SkyFriends;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Pops an emote bubble above a Cirri after {@code delay} ticks. */
public record EmotePayload(int entityId, String emote, int delay) implements CustomPacketPayload {
    public static final Type<EmotePayload> TYPE = new Type<>(SkyFriends.id("emote"));
    public static final StreamCodec<FriendlyByteBuf, EmotePayload> CODEC = StreamCodec.of(
        (buf, v) -> {
            buf.writeVarInt(v.entityId);
            buf.writeUtf(v.emote, 16);
            buf.writeVarInt(v.delay);
        },
        buf -> new EmotePayload(buf.readVarInt(), buf.readUtf(16), Math.clamp(buf.readVarInt(), 0, 200)));

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
