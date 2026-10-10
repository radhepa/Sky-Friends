package dev.skyfriends.world;

import dev.skyfriends.SkyBlocks;
import dev.skyfriends.SkyFriends;
import dev.skyfriends.block.WindStoneBlockEntity;
import dev.skyfriends.entity.Cirri;
import dev.skyfriends.entity.CirriKin;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.TemplateStructurePiece;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceSerializationContext;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePiecesBuilder;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockIgnoreProcessor;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplateManager;

/** The pieces of a sky place: its template tiles, its residents, and a village's Wind Stone on the ground below. */
public final class SkyPieces {
    private SkyPieces() {}

    static void addPieces(StructurePiecesBuilder builder, StructureTemplateManager templates, SkyLayout layout, BlockPos start,
                          Rotation rotation, int liftGround) {
        for (var tile : layout.tiles()) {
            BlockPos off = tile.offset();
            BlockPos turned = turn(off.getX() - layout.centerX(), off.getZ() - layout.centerZ(), rotation);
            builder.addPiece(new TilePiece(templates, tile.template(), start.offset(turned.getX(), off.getY(), turned.getZ()), rotation));
        }
        if (!layout.residents().isEmpty()) builder.addPiece(new ResidentPiece(layout, start, rotation));
        layout.lift().ifPresent(lift -> {
            if (liftGround == Integer.MIN_VALUE) return;
            BlockPos shaft = place(start, lift.shaft(), rotation), landing = place(start, lift.landing(), rotation);
            if (liftGround < shaft.getY() - 12) builder.addPiece(new LiftPiece(new BlockPos(shaft.getX(), liftGround, shaft.getZ()),
                    shaft.getY() + 1, landing.getX(), landing.getZ()));
        });
    }

    /** A layout-space position (from the centre, y from the floor) in the world. */
    public static BlockPos place(BlockPos start, BlockPos local, Rotation rotation) {
        BlockPos turned = turn(local.getX(), local.getZ(), rotation);
        return start.offset(turned.getX(), local.getY(), turned.getZ());
    }

    static BlockPos turn(int x, int z, Rotation rotation) {
        return StructureTemplate.transform(new BlockPos(x, 0, z), Mirror.NONE, rotation, BlockPos.ZERO);
    }

    /** One tile of the plan: a template turned with the whole place. Air in a tile is placed too. */
    public static final class TilePiece extends TemplateStructurePiece {
        TilePiece(StructureTemplateManager templates, Identifier template, BlockPos position, Rotation rotation) {
            super(SkyWorld.TILE_PIECE, 0, templates, template, template.toString(), settings(rotation), position);
        }

        public TilePiece(StructureTemplateManager templates, CompoundTag tag) {
            super(SkyWorld.TILE_PIECE, tag, templates, location -> settings(tag.read("Rot", Rotation.LEGACY_CODEC).orElse(Rotation.NONE)));
        }

        private static StructurePlaceSettings settings(Rotation rotation) {
            return new StructurePlaceSettings().setRotation(rotation).setKnownShape(true).setIgnoreEntities(false)
                    .addProcessor(BlockIgnoreProcessor.STRUCTURE_BLOCK);
        }

        @Override
        protected void addAdditionalSaveData(StructurePieceSerializationContext context, CompoundTag tag) {
            super.addAdditionalSaveData(context, tag);
            tag.store("Rot", Rotation.LEGACY_CODEC, placeSettings.getRotation());
        }

        @Override
        protected void handleDataMarker(String marker, BlockPos position, ServerLevelAccessor level, RandomSource random, BoundingBox chunk) {
        }
    }

    /**
     * Who lives there. Each one is spawned, once, when the chunk holding their bed is generated, already
     * knowing their village, bed, job and work, and (children) their mother. Everyone's UUID comes from
     * the village and their place on the roster, so a child can name its mother before she exists.
     */
    public static final class ResidentPiece extends StructurePiece {
        private final BlockPos start, centre;
        private final List<SkyLayout.Resident> residents;

        ResidentPiece(SkyLayout layout, BlockPos start, Rotation rotation) {
            this(start, place(start, layout.centrePos(), rotation), layout.residents().stream().map(r -> new SkyLayout.Resident(r.type(),
                    r.gender(), r.child(), r.bed().map(b -> place(start, b, rotation)), r.job(), r.work().map(w -> place(start, w, rotation)),
                    r.mother(), r.partner())).toList());
        }

        private ResidentPiece(BlockPos start, BlockPos centre, List<SkyLayout.Resident> residents) {
            super(SkyWorld.RESIDENT_PIECE, 0, box(centre, residents));
            this.start = start;
            this.centre = centre;
            this.residents = residents;
        }

        public ResidentPiece(CompoundTag tag) {
            super(SkyWorld.RESIDENT_PIECE, tag);
            this.start = tag.read("Start", BlockPos.CODEC).orElse(BlockPos.ZERO);
            this.centre = tag.read("Centre", BlockPos.CODEC).orElse(BlockPos.ZERO);
            this.residents = tag.read("Residents", SkyLayout.Resident.CODEC.listOf()).orElse(List.of());
        }

        private static BoundingBox box(BlockPos centre, List<SkyLayout.Resident> residents) {
            List<BlockPos> all = new ArrayList<>();
            all.add(centre);
            residents.forEach(r -> all.add(spawnAt(r, centre)));
            return BoundingBox.encapsulatingPositions(all).orElseThrow();
        }

        private static BlockPos spawnAt(SkyLayout.Resident r, BlockPos centre) {
            return r.bed().orElse(r.work().orElse(centre));
        }

        public BlockPos centre() {
            return centre;
        }

        public List<SkyLayout.Resident> residents() {
            return residents;
        }

        @Override
        protected void addAdditionalSaveData(StructurePieceSerializationContext context, CompoundTag tag) {
            tag.store("Start", BlockPos.CODEC, start);
            tag.store("Centre", BlockPos.CODEC, centre);
            tag.store("Residents", SkyLayout.Resident.CODEC.listOf(), residents);
        }

        /** The UUID of the roster's {@code index}-th resident in the village that starts at {@code start}. */
        public static UUID uuid(BlockPos start, int index) {
            long a = start.asLong() * 0x9E3779B97F4A7C15L + index, b = (start.asLong() ^ 0x5DEECE66DL) * 0xC2B2AE3D27D4EB4FL - index * 31L;
            return new UUID(a, b);
        }

        @Override
        public void postProcess(WorldGenLevel level, StructureManager structures, ChunkGenerator generator, RandomSource random,
                                BoundingBox chunk, ChunkPos chunkPos, BlockPos reference) {
            for (int i = 0; i < residents.size(); i++) {
                var r = residents.get(i);
                BlockPos at = spawnAt(r, centre);
                if (!chunk.isInside(at)) continue;
                var type = BuiltInRegistries.ENTITY_TYPE.getOptional(SkyFriends.id(r.type()));
                if (type.isEmpty()) {
                    SkyFriends.LOG.warn("Unknown resident type {} in a sky village", r.type());
                    continue;
                }
                if (!(type.get().create(level.getLevel(), EntitySpawnReason.STRUCTURE) instanceof Mob mob)) continue;
                mob.setUUID(uuid(start, i));
                mob.snapTo(at.getX() + 0.5, at.getY() + 0.1, at.getZ() + 0.5, random.nextFloat() * 360.0F, 0.0F);
                mob.setPersistenceRequired();
                if (mob instanceof Cirri cirri) {
                    boolean female = "f".equals(r.gender());
                    UUID mother = r.mother() >= 0 ? uuid(start, r.mother()) : null;
                    // a family shares its complexion (the mother's, worked out from her UUID)
                    int complexion = Math.floorMod((mother != null ? mother : mob.getUUID()).hashCode(), CirriKin.COMPLEXIONS);
                    cirri.setLook(female, complexion, r.child() ? (female ? 0 : 2) : CirriKin.palette(r.job(), random));
                    cirri.setCustomName(Component.literal(CirriKin.name(female, random)));
                    if (r.child()) {
                        cirri.setBaby(true);
                        cirri.setAge(-24000 * 20);     // children here grow up slowly (twenty days)
                        cirri.raiseBy(centre, mother);
                    } else {
                        cirri.settle(centre, r.bed().orElse(null), r.work().orElse(null), r.job());
                        if (r.partner() >= 0) cirri.setPartner(uuid(start, r.partner()));
                    }
                } else {
                    mob.finalizeSpawn(level, level.getCurrentDifficultyAt(at), EntitySpawnReason.STRUCTURE, null);
                }
                level.addFreshEntityWithPassengers(mob);
            }
        }

        /** For tests: where a layout's residents land for a start and rotation. */
        public static ResidentPiece placed(SkyLayout layout, BlockPos start, Rotation rotation) {
            return new ResidentPiece(layout, start, rotation);
        }
    }

    /**
     * The foot of a village's wind lift: the Wind Stone on the ground straight under the dock's shaft,
     * in a ring of polished skystone and gilded stone with a sky lantern at each corner, connected to
     * the dock above.
     */
    public static final class LiftPiece extends StructurePiece {
        private final BlockPos stone;
        private final int top, landX, landZ;

        LiftPiece(BlockPos stone, int top, int landX, int landZ) {
            super(SkyWorld.LIFT_PIECE, 0, new BoundingBox(stone.getX() - 3, stone.getY() - 1, stone.getZ() - 3,
                    stone.getX() + 3, stone.getY() + 5, stone.getZ() + 3));
            this.stone = stone;
            this.top = top;
            this.landX = landX;
            this.landZ = landZ;
        }

        public LiftPiece(CompoundTag tag) {
            super(SkyWorld.LIFT_PIECE, tag);
            this.stone = tag.read("Stone", BlockPos.CODEC).orElse(BlockPos.ZERO);
            this.top = tag.getIntOr("Top", 0);
            this.landX = tag.getIntOr("LandX", 0);
            this.landZ = tag.getIntOr("LandZ", 0);
        }

        public BlockPos stone() {
            return stone;
        }

        @Override
        protected void addAdditionalSaveData(StructurePieceSerializationContext context, CompoundTag tag) {
            tag.store("Stone", BlockPos.CODEC, stone);
            tag.putInt("Top", top);
            tag.putInt("LandX", landX);
            tag.putInt("LandZ", landZ);
        }

        private static void set(WorldGenLevel level, BoundingBox chunk, BlockPos pos, BlockState state) {
            if (chunk.isInside(pos)) level.setBlock(pos, state, 2);
        }

        @Override
        public void postProcess(WorldGenLevel level, StructureManager structures, ChunkGenerator generator, RandomSource random,
                                BoundingBox chunk, ChunkPos chunkPos, BlockPos reference) {
            BlockState ring = SkyBlocks.POLISHED_SKYSTONE.defaultBlockState(), gilt = SkyBlocks.GILDED_SKYSTONE.defaultBlockState();
            BlockState air = Blocks.AIR.defaultBlockState();
            for (int dx = -3; dx <= 3; dx++) {
                for (int dz = -3; dz <= 3; dz++) {
                    double d = Math.sqrt(dx * dx + dz * dz);
                    if (d > 3.3) continue;
                    BlockPos floor = stone.offset(dx, 0, dz);
                    set(level, chunk, floor, d > 2.6 ? gilt : ring);
                    set(level, chunk, floor.below(), SkyBlocks.SKYSTONE.defaultBlockState());
                    for (int k = 1; k <= 4; k++) set(level, chunk, floor.above(k), air);
                }
            }
            for (int[] c : new int[][] {{-2, -2}, {2, -2}, {-2, 2}, {2, 2}}) {
                BlockPos post = stone.offset(c[0], 1, c[1]);
                set(level, chunk, post, SkyBlocks.SKYWOOD_FENCE.defaultBlockState());
                set(level, chunk, post.above(), SkyBlocks.SKY_LANTERN.defaultBlockState());
            }
            if (chunk.isInside(stone)) {
                level.setBlock(stone, SkyBlocks.WIND_STONE.defaultBlockState(), 2);
                if (level.getBlockEntity(stone) instanceof WindStoneBlockEntity be) be.connect(top, landX, landZ);
            }
        }
    }

    static Optional<BlockPos> none() {
        return Optional.empty();
    }
}
