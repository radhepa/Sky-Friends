package dev.skyfriends.talk;

import dev.skyfriends.SkyFriends;
import java.util.UUID;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** A reply, tab or dock button pressed in the conversation screen, client to server. */
public record TalkActionPayload(int entityId, UUID id, String action) implements CustomPacketPayload {
    public static final Type<TalkActionPayload> TYPE = new Type<>(SkyFriends.id("talk_action"));
    public static final StreamCodec<FriendlyByteBuf, TalkActionPayload> CODEC = StreamCodec.of(
        (buf, v) -> {
            buf.writeVarInt(v.entityId);
            buf.writeUUID(v.id);
            buf.writeUtf(v.action, 64);
        },
        buf -> new TalkActionPayload(buf.readVarInt(), buf.readUUID(), buf.readUtf(64)));

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
