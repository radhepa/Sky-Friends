package dev.skyfriends.world;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.List;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureType;

/**
 * A place in the sky: one of a few pre-planned layouts (islands and all), turned to a random side,
 * floating at a height within {@link Altitude}, and always at least {@code clearance} blocks over the
 * highest ground beneath its islands (over a mountain it floats higher, or not at all). A village
 * also gets its Wind Stone, on the ground straight under its Lift Dock.
 */
public final class SkyStructure extends Structure {
    /** The floor's height range, and how far the islands' undersides keep above the ground. */
    public record Altitude(int minFloor, int maxFloor, int clearance) {
        public static final Codec<Altitude> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.INT.fieldOf("min_floor").forGetter(Altitude::minFloor),
            Codec.INT.fieldOf("max_floor").forGetter(Altitude::maxFloor),
            Codec.intRange(0, 256).fieldOf("clearance").forGetter(Altitude::clearance)
        ).apply(i, Altitude::new));
    }

    public static final MapCodec<SkyStructure> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
        settingsCodec(i),
        SkyLayout.CODEC.listOf().fieldOf("layouts").forGetter(s -> s.layouts),
        Altitude.CODEC.fieldOf("altitude").forGetter(s -> s.altitude)
    ).apply(i, SkyStructure::new));
    public static final StructureType<SkyStructure> TYPE = () -> CODEC;

    private final List<SkyLayout> layouts;
    private final Altitude altitude;

    public SkyStructure(StructureSettings settings, List<SkyLayout> layouts, Altitude altitude) {
        super(settings);
        this.layouts = layouts;
        this.altitude = altitude;
    }

    public List<SkyLayout> layouts() {
        return layouts;
    }

    @Override
    public StructureType<?> type() {
        return TYPE;
    }

    private static int ground(GenerationContext c, int x, int z) {
        return c.chunkGenerator().getBaseHeight(x, z, Heightmap.Types.WORLD_SURFACE_WG, c.heightAccessor(), c.randomState());
    }

    @Override
    protected Optional<GenerationStub> findGenerationPoint(GenerationContext context) {
        if (layouts.isEmpty()) return Optional.empty();
        var random = context.random();
        SkyLayout layout = layouts.get(random.nextInt(layouts.size()));
        Rotation rotation = Rotation.getRandom(random);
        int cx = context.chunkPos().getMiddleBlockX(), cz = context.chunkPos().getMiddleBlockZ();
        // the highest ground under the layout's footprint (either way round)
        int reach = Math.max(layout.width(), layout.depth()) / 2 + 2, highest = Integer.MIN_VALUE;
        for (int dx = -reach; dx <= reach; dx += 8) {
            for (int dz = -reach; dz <= reach; dz += 8) highest = Math.max(highest, ground(context, cx + dx, cz + dz));
        }
        int floor = altitude.minFloor() + random.nextInt(Math.max(1, altitude.maxFloor() - altitude.minFloor() + 1));
        floor = Math.max(floor, highest + altitude.clearance() - layout.minY());
        int top = context.heightAccessor().getMaxY() - 2;
        if (floor + layout.maxY() > top) return Optional.empty();
        BlockPos start = new BlockPos(cx, floor, cz);
        Optional<Integer> liftGround = layout.lift().map(l -> {
            BlockPos shaft = SkyPieces.place(start, l.shaft(), rotation);
            return ground(context, shaft.getX(), shaft.getZ()) - 1;
        });
        return Optional.of(new GenerationStub(start, builder -> SkyPieces.addPieces(builder, context.structureTemplateManager(), layout,
                start, rotation, liftGround.orElse(Integer.MIN_VALUE))));
    }
}
