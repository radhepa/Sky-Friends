package dev.skyfriends.world;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.List;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;

/**
 * One planned sky place (a village, a wild islet, a shrine, a ruin), written by
 * {@code tools/villages/compile.py}.
 *
 * <p>Layout space: x east, z south, y up, with y = 0 the floor (a village's court). {@code center}
 * is the column that lands on the structure's start. The plan is cut into {@code tiles}, templates
 * placed with their minimum corner at {@code offset} (canvas space: subtract the centre for layout
 * space). Islands are part of the tiles: in the sky there is nothing for them to meet.
 *
 * <p>{@code residents}: who lives there, their beds and work in layout space ({@link Resident}).
 * {@code lift}: a village's lift shaft (its centre at the dock floor) and where riders are set down.
 */
public record SkyLayout(String name, String kind, int width, int depth, int minY, int maxY, int centerX, int centerZ,
                        List<Tile> tiles, List<Integer> centre, List<Resident> residents, Optional<Lift> lift) {

    public record Tile(Identifier template, BlockPos offset) {
        public static final Codec<Tile> CODEC = RecordCodecBuilder.create(i -> i.group(
            Identifier.CODEC.fieldOf("template").forGetter(Tile::template),
            BlockPos.CODEC.fieldOf("offset").forGetter(Tile::offset)
        ).apply(i, Tile::new));
    }

    /** A Cirri (gender, child, bed, job, work, mother = an index in this list) or a creature released at its spot. */
    public record Resident(String type, String gender, boolean child, Optional<BlockPos> bed, String job, Optional<BlockPos> work, int mother) {
        public static final Codec<Resident> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.STRING.fieldOf("type").forGetter(Resident::type),
            Codec.STRING.optionalFieldOf("gender", "f").forGetter(Resident::gender),
            Codec.BOOL.optionalFieldOf("child", false).forGetter(Resident::child),
            BlockPos.CODEC.optionalFieldOf("bed").forGetter(Resident::bed),
            Codec.STRING.optionalFieldOf("job", "").forGetter(Resident::job),
            BlockPos.CODEC.optionalFieldOf("work").forGetter(Resident::work),
            Codec.INT.optionalFieldOf("mother", -1).forGetter(Resident::mother)
        ).apply(i, Resident::new));
    }

    public record Lift(BlockPos shaft, BlockPos landing) {
        public static final Codec<Lift> CODEC = RecordCodecBuilder.create(i -> i.group(
            BlockPos.CODEC.fieldOf("shaft").forGetter(Lift::shaft),
            BlockPos.CODEC.fieldOf("landing").forGetter(Lift::landing)
        ).apply(i, Lift::new));
    }

    public static final Codec<SkyLayout> CODEC = RecordCodecBuilder.create(i -> i.group(
        Codec.STRING.fieldOf("name").forGetter(SkyLayout::name),
        Codec.STRING.fieldOf("kind").forGetter(SkyLayout::kind),
        Codec.intRange(1, 512).fieldOf("width").forGetter(SkyLayout::width),
        Codec.intRange(1, 512).fieldOf("depth").forGetter(SkyLayout::depth),
        Codec.INT.fieldOf("min_y").forGetter(SkyLayout::minY),
        Codec.INT.fieldOf("max_y").forGetter(SkyLayout::maxY),
        Codec.INT.fieldOf("center_x").forGetter(SkyLayout::centerX),
        Codec.INT.fieldOf("center_z").forGetter(SkyLayout::centerZ),
        Tile.CODEC.listOf().fieldOf("tiles").forGetter(SkyLayout::tiles),
        Codec.INT.listOf().optionalFieldOf("centre", List.of(0, 2, 0)).forGetter(SkyLayout::centre),
        Resident.CODEC.listOf().optionalFieldOf("residents", List.of()).forGetter(SkyLayout::residents),
        Lift.CODEC.optionalFieldOf("lift").forGetter(SkyLayout::lift)
    ).apply(i, SkyLayout::new));

    public BlockPos centrePos() {
        return new BlockPos(centre.get(0), centre.get(1), centre.get(2));
    }
}
