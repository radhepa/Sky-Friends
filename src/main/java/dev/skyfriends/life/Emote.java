package dev.skyfriends.life;

import dev.skyfriends.entity.Cirri;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.server.level.ServerLevel;

/**
 * The little cloud bubbles a Cirri pops above their head, Tomodachi Life style (as Village Friends residents
 * do): a "!" when they spot you, a heart for a sweetheart, notes while they sing, "..." while they chat, "Zz"
 * while they sleep. The server decides when; the client draws and animates them.
 */
public enum Emote {
    EXCLAIM, QUESTION, HEART, NOTE, ANGER, SWEAT, DOTS, SLEEP, SPARKLE, IDEA, GLOOM, BLUSH;

    public static Emote parse(String name) {
        if (name == null || name.isEmpty()) return null;
        try {
            return valueOf(name);
        } catch (IllegalArgumentException ignored) {
            return null;
        }
    }

    /** Pops this bubble over a Cirri for everyone nearby, after {@code delay} ticks. */
    public void show(Cirri cirri, int delay) {
        if (!(cirri.level() instanceof ServerLevel) || !cirri.isAlive()) return;
        var payload = new EmotePayload(cirri.getId(), name(), delay);
        for (var player : PlayerLookup.tracking(cirri)) {
            if (player.distanceToSqr(cirri) < 48 * 48 && ServerPlayNetworking.canSend(player, EmotePayload.TYPE)) {
                ServerPlayNetworking.send(player, payload);
            }
        }
    }
}
