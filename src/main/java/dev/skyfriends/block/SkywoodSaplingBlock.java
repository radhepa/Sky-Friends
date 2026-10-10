package dev.skyfriends.block;

import dev.skyfriends.SkyFriends;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.util.random.WeightedList;
import net.minecraft.world.level.block.SaplingBlock;
import net.minecraft.world.level.block.grower.TreeGrower;
import net.minecraft.world.level.levelgen.feature.Feature;

/** Grows the skywood tree (data/skyfriends/worldgen/feature/skywood.json). */
public class SkywoodSaplingBlock extends SaplingBlock {
    public static final ResourceKey<Feature> TREE = ResourceKey.create(Registries.FEATURE, SkyFriends.id("skywood"));
    public static final TreeGrower GROWER = new TreeGrower("skyfriends_skywood", WeightedList.of(TREE), WeightedList.of(), WeightedList.of(), TREE);

    public SkywoodSaplingBlock(Properties properties) {
        super(GROWER, properties);
    }
}
