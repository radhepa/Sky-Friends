package dev.skyfriends.registry;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import dev.skyfriends.SkyFriends;

import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.SpawnEggItem;

/** All registered mobs, in catalogue order, and the wiring every mob gets. */
public final class MobRegistry {
    private MobRegistry() {}

    private static final List<MobEntry<?>> ALL = new ArrayList<>();

    static void add(MobEntry<?> entry) {
        if (ALL.stream().anyMatch(e -> e.id.equals(entry.id))) throw new IllegalStateException("duplicate mob " + entry.id);
        ALL.add(entry);
    }

    public static List<MobEntry<?>> all() {
        return Collections.unmodifiableList(ALL);
    }

    /** Attributes, spawn eggs, spawn rules and biome spawns for every catalogued mob. */
    public static void wireUp() {
        for (MobEntry<?> e : ALL) {
            FabricDefaultAttributeRegistry.register(e.type, e.attributes.get());
            ResourceKey<Item> egg = ResourceKey.create(Registries.ITEM, Identifier.fromNamespaceAndPath(SkyFriends.MOD_ID, e.id + "_spawn_egg"));
            e.spawnEgg = Registry.register(BuiltInRegistries.ITEM, egg, new SpawnEggItem(new Item.Properties().setId(egg).spawnEgg(e.type)));
            e.registerSpawnPlacement();
            for (MobEntry.BiomeSpawn s : e.spawns) {
                if (e.spawnRule == null) throw new IllegalStateException(e.id + " has biome spawns but no spawn rule");
                BiomeModifications.addSpawn(s.biomes(), e.type.getCategory(), e.type, s.weight(), s.minGroup(), s.maxGroup());
            }
        }
        CreativeModeTabEvents.modifyOutputEvent(CreativeModeTabs.SPAWN_EGGS).register(out -> ALL.forEach(e -> out.accept(e.spawnEgg)));
    }
}
