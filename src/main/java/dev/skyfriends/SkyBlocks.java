package dev.skyfriends;

import dev.skyfriends.block.CloudBlock;
import dev.skyfriends.block.SkyStairBlock;
import dev.skyfriends.block.SkywoodSaplingBlock;
import dev.skyfriends.block.WindChimeBlock;
import dev.skyfriends.block.WindHarpBlock;
import dev.skyfriends.block.WindStoneBlock;
import dev.skyfriends.block.WindStoneBlockEntity;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.function.Function;
import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.CarpetBlock;
import net.minecraft.world.level.block.FenceBlock;
import net.minecraft.world.level.block.FenceGateBlock;
import net.minecraft.world.level.block.LanternBlock;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.UntintedParticleLeavesBlock;
import net.minecraft.world.level.block.WallBlock;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.sounds.AmbientLeavesBlockSoundPlayer;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.properties.NoteBlockInstrument;
import net.minecraft.world.level.block.state.properties.WoodType;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;

/**
 * Every block in the mod, in the order of tools/blocks/catalog.py (the asset generator writes their
 * models, loot, tags and recipes from that list; the game test checks the two agree).
 */
public final class SkyBlocks {
    private SkyBlocks() {}

    private static final Map<String, Block> ALL = new LinkedHashMap<>();

    public static Map<String, Block> all() {
        return Collections.unmodifiableMap(ALL);
    }

    private static BlockBehaviour.Properties stone(MapColor color) {
        return BlockBehaviour.Properties.of().mapColor(color).instrument(NoteBlockInstrument.BASEDRUM).requiresCorrectToolForDrops()
                .strength(1.5F, 6.0F).sound(SoundType.STONE);
    }

    private static BlockBehaviour.Properties wood() {
        return BlockBehaviour.Properties.of().mapColor(MapColor.SAND).instrument(NoteBlockInstrument.BASS).strength(2.0F, 3.0F)
                .sound(SoundType.CHERRY_WOOD).ignitedByLava();
    }

    private static BlockBehaviour.Properties cloth(MapColor color) {
        return BlockBehaviour.Properties.of().mapColor(color).instrument(NoteBlockInstrument.GUITAR).strength(0.8F).sound(SoundType.WOOL).ignitedByLava();
    }

    private static Block add(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
        var id = SkyFriends.id(name);
        Block block = factory.apply(properties.setId(ResourceKey.create(Registries.BLOCK, id)));
        Registry.register(BuiltInRegistries.BLOCK, id, block);
        Registry.register(BuiltInRegistries.ITEM, id, new BlockItem(block,
                new Item.Properties().setId(ResourceKey.create(Registries.ITEM, id)).useBlockDescriptionPrefix()));
        ALL.put(name, block);
        return block;
    }

    private static Block cube(String name, BlockBehaviour.Properties properties) {
        return add(name, Block::new, properties);
    }

    private static Block stairs(String name, Block base) {
        return add(name, p -> new SkyStairBlock(base.defaultBlockState(), p), BlockBehaviour.Properties.ofFullCopy(base));
    }

    private static Block slab(String name, Block base) {
        return add(name, SlabBlock::new, BlockBehaviour.Properties.ofFullCopy(base));
    }

    // -- skystone ---------------------------------------------------------------------------------
    public static final Block SKYSTONE = cube("skystone", stone(MapColor.COLOR_LIGHT_GRAY));
    public static final Block SKYSTONE_STAIRS = stairs("skystone_stairs", SKYSTONE);
    public static final Block SKYSTONE_SLAB = slab("skystone_slab", SKYSTONE);
    public static final Block SKYSTONE_BRICKS = cube("skystone_bricks", stone(MapColor.COLOR_LIGHT_GRAY));
    public static final Block SKYSTONE_BRICK_STAIRS = stairs("skystone_brick_stairs", SKYSTONE_BRICKS);
    public static final Block SKYSTONE_BRICK_SLAB = slab("skystone_brick_slab", SKYSTONE_BRICKS);
    public static final Block SKYSTONE_BRICK_WALL = add("skystone_brick_wall", WallBlock::new,
            BlockBehaviour.Properties.ofFullCopy(SKYSTONE_BRICKS).forceSolidOn());
    public static final Block POLISHED_SKYSTONE = cube("polished_skystone", stone(MapColor.QUARTZ));
    public static final Block POLISHED_SKYSTONE_STAIRS = stairs("polished_skystone_stairs", POLISHED_SKYSTONE);
    public static final Block POLISHED_SKYSTONE_SLAB = slab("polished_skystone_slab", POLISHED_SKYSTONE);
    public static final Block GILDED_SKYSTONE = cube("gilded_skystone", stone(MapColor.GOLD));
    public static final Block SKYSTONE_PILLAR = add("skystone_pillar", RotatedPillarBlock::new, stone(MapColor.QUARTZ));

    // -- cloud ------------------------------------------------------------------------------------
    public static final Block CLOUD = add("cloud_block", CloudBlock::new, BlockBehaviour.Properties.of().mapColor(MapColor.SNOW)
            .strength(0.3F).sound(SoundType.WOOL).isValidSpawn((s, l, p, t) -> false));

    // -- skywood ----------------------------------------------------------------------------------
    public static final Block SKYWOOD_LOG = add("skywood_log", RotatedPillarBlock::new, wood());
    public static final Block SKYWOOD = add("skywood", RotatedPillarBlock::new, wood());
    public static final Block SKYWOOD_PLANKS = cube("skywood_planks", wood());
    public static final Block SKYWOOD_STAIRS = stairs("skywood_stairs", SKYWOOD_PLANKS);
    public static final Block SKYWOOD_SLAB = slab("skywood_slab", SKYWOOD_PLANKS);
    public static final Block SKYWOOD_FENCE = add("skywood_fence", FenceBlock::new, BlockBehaviour.Properties.ofFullCopy(SKYWOOD_PLANKS).forceSolidOn());
    public static final Block SKYWOOD_FENCE_GATE = add("skywood_fence_gate", p -> new FenceGateBlock(WoodType.CHERRY, p),
            BlockBehaviour.Properties.ofFullCopy(SKYWOOD_PLANKS).forceSolidOn());
    public static final Block SKYWOOD_LEAVES = add("skywood_leaves",
            p -> new UntintedParticleLeavesBlock(0.02F, ParticleTypes.PALE_OAK_LEAVES, AmbientLeavesBlockSoundPlayer.noAmbientSound(), p),
            BlockBehaviour.Properties.of().mapColor(MapColor.SNOW).strength(0.2F).randomTicks().sound(SoundType.CHERRY_LEAVES).noOcclusion()
                    .isValidSpawn((s, l, p, t) -> false).isSuffocating((s, l, p) -> false)
                    .ignitedByLava().pushReaction(PushReaction.POPPED));
    public static final Block SKYWOOD_SAPLING = add("skywood_sapling", SkywoodSaplingBlock::new, BlockBehaviour.Properties.of()
            .mapColor(MapColor.SNOW).noCollision().randomTicks().instabreak().sound(SoundType.CHERRY_SAPLING).pushReaction(PushReaction.POPPED));

    // -- veilcloth --------------------------------------------------------------------------------
    public static final Block WHITE_VEILCLOTH = cube("white_veilcloth", cloth(MapColor.SNOW));
    public static final Block SKY_VEILCLOTH = cube("sky_veilcloth", cloth(MapColor.COLOR_LIGHT_BLUE));
    public static final Block ROSE_VEILCLOTH = cube("rose_veilcloth", cloth(MapColor.COLOR_PINK));
    public static final Block WHITE_VEILCLOTH_CARPET = add("white_veilcloth_carpet", CarpetBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.SNOW).strength(0.1F).sound(SoundType.WOOL).ignitedByLava());
    public static final Block SKY_VEILCLOTH_CARPET = add("sky_veilcloth_carpet", CarpetBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_LIGHT_BLUE).strength(0.1F).sound(SoundType.WOOL).ignitedByLava());
    public static final Block ROSE_VEILCLOTH_CARPET = add("rose_veilcloth_carpet", CarpetBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_PINK).strength(0.1F).sound(SoundType.WOOL).ignitedByLava());

    // -- the Cirri's things -------------------------------------------------------------------------
    public static final Block WIND_CHIME = add("wind_chime", WindChimeBlock::new, BlockBehaviour.Properties.of().mapColor(MapColor.GOLD)
            .strength(0.5F).sound(SoundType.CHAIN).noOcclusion().noCollision().pushReaction(PushReaction.POPPED));
    public static final Block WIND_HARP = add("wind_harp", WindHarpBlock::new, BlockBehaviour.Properties.of().mapColor(MapColor.SAND)
            .strength(1.5F).sound(SoundType.CHERRY_WOOD).noOcclusion().ignitedByLava());
    public static final Block SKY_LANTERN = add("sky_lantern", LanternBlock::new, BlockBehaviour.Properties.of().mapColor(MapColor.GOLD)
            .strength(3.5F).sound(SoundType.LANTERN).lightLevel(s -> 15).noOcclusion().pushReaction(PushReaction.POPPED));
    public static final Block WIND_STONE = add("wind_stone", WindStoneBlock::new, BlockBehaviour.Properties.of().mapColor(MapColor.QUARTZ)
            .strength(-1.0F, 3600000.0F).sound(SoundType.STONE).lightLevel(s -> 7).noLootTable());

    public static final BlockEntityType<WindStoneBlockEntity> WIND_STONE_ENTITY = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE,
            SkyFriends.id("wind_stone"), FabricBlockEntityTypeBuilder.create(WindStoneBlockEntity::new, WIND_STONE).build());

    /** Loads the class (the fields above register everything). */
    public static void register() {}
}
