package dev.skyfriends.registry;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Predicate;
import java.util.function.Supplier;
import java.util.function.UnaryOperator;

import dev.skyfriends.SkyFriends;

import net.fabricmc.fabric.api.biome.v1.BiomeSelectionContext;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.SpawnPlacementType;
import net.minecraft.world.entity.SpawnPlacementTypes;
import net.minecraft.world.entity.SpawnPlacements;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import org.jspecify.annotations.Nullable;

/**
 * Everything the mod needs to know about one mob, declared in one place (see {@link dev.skyfriends.SkyEntities}).
 * {@link MobRegistry} turns each entry into an entity type, default attributes, a spawn egg, spawn
 * rules and biome spawns. The client adds the model and renderer.
 */
public final class MobEntry<T extends Mob> {
    /** One biome spawn: weight and group size in the biomes the selector picks. */
    public record BiomeSpawn(Predicate<BiomeSelectionContext> biomes, int weight, int minGroup, int maxGroup) {}

    public final String id;
    public final EntityType<T> type;
    final Supplier<AttributeSupplier.Builder> attributes;
    final SpawnPlacementType placementType;
    final Heightmap.Types heightmap;
    final SpawnPlacements.@Nullable SpawnPredicate<T> spawnRule;
    final List<BiomeSpawn> spawns;
    final double solitary;
    Item spawnEgg;

    private MobEntry(Builder<T> b, EntityType<T> type) {
        this.id = b.id;
        this.type = type;
        this.attributes = b.attributes;
        this.placementType = b.placementType;
        this.heightmap = b.heightmap;
        this.spawnRule = b.spawnRule;
        this.spawns = List.copyOf(b.spawns);
        this.solitary = b.solitary;
    }

    public Item spawnEgg() { return this.spawnEgg; }
    public List<BiomeSpawn> spawns() { return this.spawns; }

    public static <T extends Mob> Builder<T> builder(String id, EntityType.EntityFactory<T> factory, MobCategory category) {
        return new Builder<>(id, EntityType.Builder.of(factory, category));
    }

    public static final class Builder<T extends Mob> {
        private final String id;
        private EntityType.Builder<T> type;
        private Supplier<AttributeSupplier.Builder> attributes;
        private SpawnPlacementType placementType = SpawnPlacementTypes.ON_GROUND;
        private Heightmap.Types heightmap = Heightmap.Types.MOTION_BLOCKING_NO_LEAVES;
        private SpawnPlacements.@Nullable SpawnPredicate<T> spawnRule;
        private final List<BiomeSpawn> spawns = new ArrayList<>();
        private double solitary;

        private Builder(String id, EntityType.Builder<T> type) {
            this.id = id;
            this.type = type.clientTrackingRange(8);
        }

        /** Hitbox in blocks, and eye height. */
        public Builder<T> size(float width, float height, float eyeHeight) {
            this.type = this.type.sized(width, height).eyeHeight(eyeHeight);
            return this;
        }

        /** Anything else on the vanilla entity type builder (fireImmune, passengerAttachments...). */
        public Builder<T> type(UnaryOperator<EntityType.Builder<T>> edit) {
            this.type = edit.apply(this.type);
            return this;
        }

        public Builder<T> attributes(Supplier<AttributeSupplier.Builder> attributes) {
            this.attributes = attributes;
            return this;
        }

        /** Natural spawn rule (light, ground block...). Mobs without one never spawn naturally. */
        public Builder<T> spawnRule(SpawnPlacements.SpawnPredicate<T> rule) {
            this.spawnRule = rule;
            return this;
        }

        public Builder<T> placement(SpawnPlacementType placementType, Heightmap.Types heightmap) {
            this.placementType = placementType;
            this.heightmap = heightmap;
            return this;
        }

        /** Spawn in these biomes with this weight (vanilla zombie is 95) and group size. */
        @SafeVarargs
        public final Builder<T> spawnsIn(int weight, int minGroup, int maxGroup, ResourceKey<Biome>... biomes) {
            this.spawns.add(new BiomeSpawn(BiomeSelectors.includeByKey(biomes), weight, minGroup, maxGroup));
            return this;
        }

        public Builder<T> spawnsIn(Predicate<BiomeSelectionContext> biomes, int weight, int minGroup, int maxGroup) {
            this.spawns.add(new BiomeSpawn(biomes, weight, minGroup, maxGroup));
            return this;
        }

        /**
         * A loner: it never spawns naturally within {@code radius} blocks of another of its kind
         * (spawners excepted), so a rare, dangerous mob stays rare.
         */
        public Builder<T> solitary(double radius) {
            this.solitary = radius;
            return this;
        }

        public EntityType<T> register() {
            if (this.attributes == null) throw new IllegalStateException(this.id + " has no attributes");
            ResourceKey<EntityType<?>> key = ResourceKey.create(Registries.ENTITY_TYPE, Identifier.fromNamespaceAndPath(SkyFriends.MOD_ID, this.id));
            EntityType<T> built = Registry.register(BuiltInRegistries.ENTITY_TYPE, key, this.type.build(key));
            MobRegistry.add(new MobEntry<>(this, built));
            return built;
        }
    }

    void registerSpawnPlacement() {
        if (this.spawnRule == null) return;
        SpawnPlacements.SpawnPredicate<T> rule = this.spawnRule;
        if (this.solitary > 0) {
            SpawnPlacements.SpawnPredicate<T> base = rule;
            double r = this.solitary;
            rule = (type, level, reason, pos, random) -> base.test(type, level, reason, pos, random)
                    && (EntitySpawnReason.isSpawner(reason) || level.getEntities(type, new AABB(pos).inflate(r), e -> true).isEmpty());
        }
        SpawnPlacements.register(this.type, this.placementType, this.heightmap, rule);
    }
}
