package dev.skyfriends.world;

import dev.skyfriends.SkyFriends;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceType;

/**
 * Registers the sky structure type and its pieces. The places themselves are data:
 * {@code data/skyfriends/worldgen/structure/*.json} (sky villages, wild islets, wind shrines and
 * ruined belltowers), written by {@code tools/villages/compile.py} with every layout embedded.
 */
public final class SkyWorld {
    public static final StructurePieceType TILE_PIECE = Registry.register(BuiltInRegistries.STRUCTURE_PIECE,
            SkyFriends.id("sky_tile"), (StructurePieceType.StructureTemplateType) SkyPieces.TilePiece::new);
    public static final StructurePieceType RESIDENT_PIECE = Registry.register(BuiltInRegistries.STRUCTURE_PIECE,
            SkyFriends.id("sky_residents"), (StructurePieceType.ContextlessType) SkyPieces.ResidentPiece::new);
    public static final StructurePieceType LIFT_PIECE = Registry.register(BuiltInRegistries.STRUCTURE_PIECE,
            SkyFriends.id("wind_lift"), (StructurePieceType.ContextlessType) SkyPieces.LiftPiece::new);

    private SkyWorld() {}

    public static void register() {
        Registry.register(BuiltInRegistries.STRUCTURE_TYPE, SkyFriends.id("sky_structure"), SkyStructure.TYPE);
    }
}
