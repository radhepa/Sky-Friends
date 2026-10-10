package dev.skyfriends.entity;

import dev.skyfriends.SkyEntities;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;

/**
 * Sends Cloud Whales across the overworld sky: about once every ten minutes per player, if no whale
 * is already near, one appears far off (beyond sight) high up and swims across the player's sky.
 * (The sky's other creatures, the Cirri and the Cloud Koi, live where the world placed them.)
 */
public final class SkySpawner {
    private SkySpawner() {}

    static final int EVERY = 600;           // ticks between tries
    static final float CHANCE = 0.06F;      // per player per try (one whale in about ten minutes)
    static final int MAX_LOADED = 6;

    public static void tick(ServerLevel level) {
        if (level.dimension() != Level.OVERWORLD || level.getGameTime() % EVERY != 0) return;
        if (!level.getGameRules().get(net.minecraft.world.level.gamerules.GameRules.SPAWN_MOBS)) return;
        var whales = level.getEntities(SkyEntities.CLOUD_WHALE, w -> true);
        if (whales.size() >= MAX_LOADED) return;
        for (ServerPlayer player : level.players()) {
            if (player.isSpectator() || level.getRandom().nextFloat() >= CHANCE) continue;
            if (!level.getEntitiesOfClass(CloudWhale.class, new AABB(player.blockPosition()).inflate(200), w -> true).isEmpty()) continue;
            spawnNear(level, player);
        }
    }

    /** One whale about 110 blocks off, swimming across the player's sky. */
    public static CloudWhale spawnNear(ServerLevel level, ServerPlayer player) {
        var random = level.getRandom();
        float bearing = random.nextFloat() * 360.0F;
        double rad = bearing * Mth.DEG_TO_RAD;
        double x = player.getX() + Math.cos(rad) * 110, z = player.getZ() + Math.sin(rad) * 110;
        int ground = level.getHeight(Heightmap.Types.MOTION_BLOCKING, Mth.floor(x), Mth.floor(z));
        int y = Math.max(190 + random.nextInt(45), ground + 40);
        if (y > level.getMaxY() - 12) return null;
        CloudWhale whale = SkyEntities.CLOUD_WHALE.create(level, EntitySpawnReason.NATURAL);
        if (whale == null) return null;
        // heading across the player's view: at right angles to the line between them, turned a little toward them
        float across = bearing + (random.nextBoolean() ? 90.0F : -90.0F) + (random.nextFloat() - 0.5F) * 40.0F;
        whale.snapTo(x, y, z, across, 0.0F);
        whale.launch(across, y);
        level.addFreshEntity(whale);
        return whale;
    }
}
