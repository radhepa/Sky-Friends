package dev.skyfriends.talk;

import dev.skyfriends.SkyFriends;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * One conversation screen's worth of state, server to client. {@code voice} is woman, man or child (the typing
 * blips follow it); friendship is at {@code level} 0-10 with {@code points} between {@code levelFloor} and {@code
 * nextThreshold}. {@code tab} is talk, story or journal; {@code left} means they have cut the conversation short
 * (only the Journal still answers); {@code storyAlert} marks the Story tab when there is something to do there;
 * {@code emote} is the bubble they show; {@code merchant} adds the Trade button.
 */
public record TalkPayload(int entityId, UUID id, String name, String title, String home, String voice,
                          int level, String levelName, int points, int levelFloor, int nextThreshold,
                          String dialogue, String status, List<Choice> choices, int giftsLeft,
                          boolean levelUp, boolean opening, String tab, boolean left, boolean storyAlert, String emote,
                          boolean merchant) implements CustomPacketPayload {
    public static final int MAX_CHOICES = 8;

    /** A reply the player can pick; {@code hint} explains a locked one. */
    public record Choice(String id, String label, boolean enabled, String hint) {}

    public static final Type<TalkPayload> TYPE = new Type<>(SkyFriends.id("talk"));
    public static final StreamCodec<FriendlyByteBuf, TalkPayload> CODEC = StreamCodec.of(
        (buf, v) -> {
            buf.writeVarInt(v.entityId);
            buf.writeUUID(v.id);
            buf.writeUtf(v.name, 128);
            buf.writeUtf(v.title, 64);
            buf.writeUtf(v.home, 128);
            buf.writeUtf(v.voice, 16);
            buf.writeVarInt(v.level);
            buf.writeUtf(v.levelName, 64);
            buf.writeVarInt(v.points);
            buf.writeVarInt(v.levelFloor);
            buf.writeVarInt(v.nextThreshold);
            buf.writeUtf(v.dialogue, 8192);
            buf.writeUtf(v.status, 256);
            buf.writeVarInt(v.choices.size());
            for (Choice c : v.choices) {
                buf.writeUtf(c.id, 64);
                buf.writeUtf(c.label, 64);
                buf.writeBoolean(c.enabled);
                buf.writeUtf(c.hint, 128);
            }
            buf.writeVarInt(v.giftsLeft);
            buf.writeBoolean(v.levelUp);
            buf.writeBoolean(v.opening);
            buf.writeUtf(v.tab, 16);
            buf.writeBoolean(v.left);
            buf.writeBoolean(v.storyAlert);
            buf.writeUtf(v.emote, 16);
            buf.writeBoolean(v.merchant);
        },
        buf -> {
            int entityId = buf.readVarInt();
            UUID id = buf.readUUID();
            String name = buf.readUtf(128), title = buf.readUtf(64), home = buf.readUtf(128), voice = buf.readUtf(16);
            int level = buf.readVarInt();
            String levelName = buf.readUtf(64);
            int points = buf.readVarInt(), floor = buf.readVarInt(), next = buf.readVarInt();
            String dialogue = buf.readUtf(8192), status = buf.readUtf(256);
            int count = buf.readVarInt();
            if (count < 0 || count > MAX_CHOICES) throw new IllegalArgumentException("Invalid choice count " + count);
            List<Choice> choices = new ArrayList<>();
            for (int i = 0; i < count; i++) choices.add(new Choice(buf.readUtf(64), buf.readUtf(64), buf.readBoolean(), buf.readUtf(128)));
            int gifts = buf.readVarInt();
            boolean levelUp = buf.readBoolean(), opening = buf.readBoolean();
            String tab = buf.readUtf(16);
            boolean left = buf.readBoolean(), storyAlert = buf.readBoolean();
            String emote = buf.readUtf(16);
            boolean merchant = buf.readBoolean();
            return new TalkPayload(entityId, id, name, title, home, voice, level, levelName, points, floor, next,
                    dialogue, status, List.copyOf(choices), gifts, levelUp, opening, tab, left, storyAlert, emote, merchant);
        });

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
