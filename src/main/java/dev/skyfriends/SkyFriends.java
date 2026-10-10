package dev.skyfriends;

import dev.skyfriends.registry.MobRegistry;
import net.fabricmc.api.ModInitializer;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Sky Friends: the Cirri, a people of the high sky who fly on their veils and never touch the ground,
 * their villages on floating islands above the clouds, the wild sky islands, and the creatures of the sky.
 */
public final class SkyFriends implements ModInitializer {
    public static final String MOD_ID = "skyfriends";
    public static final Logger LOG = LoggerFactory.getLogger("Sky Friends");

    public static Identifier id(String path) {
        return Identifier.fromNamespaceAndPath(MOD_ID, path);
    }

    @Override
    public void onInitialize() {
        SkySounds.register();
        SkyBlocks.register();
        SkyEntities.register();
        MobRegistry.wireUp();
        SkyItems.register();
        dev.skyfriends.world.SkyWorld.register();
        net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_LEVEL_TICK.register(dev.skyfriends.entity.SkySpawner::tick);
    }
}
