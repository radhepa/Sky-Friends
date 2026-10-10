package dev.skyfriends.life;

import dev.skyfriends.SkyFriends;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** The title card shown when a player comes into a sky village: its name, and the lines above and below it. */
public record ArrivalPayload(String village, String above, String below) implements CustomPacketPayload {
    public static final Type<ArrivalPayload> TYPE = new Type<>(SkyFriends.id("arrival"));
    public static final StreamCodec<FriendlyByteBuf, ArrivalPayload> CODEC = StreamCodec.of(
        (buf, v) -> {
            buf.writeUtf(v.village, 64);
            buf.writeUtf(v.above, 64);
            buf.writeUtf(v.below, 96);
        },
        buf -> new ArrivalPayload(buf.readUtf(64), buf.readUtf(64), buf.readUtf(96)));

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
