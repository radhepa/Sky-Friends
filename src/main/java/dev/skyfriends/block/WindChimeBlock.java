package dev.skyfriends.block;

import dev.skyfriends.SkySounds;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ScheduledTickAccess;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * A wind chime: it hangs under a block and rings by itself now and then, more often (and louder) in
 * the rain and in thunderstorms, and whenever something brushes through it.
 */
public class WindChimeBlock extends Block {
    private static final VoxelShape SHAPE = Block.box(3, 3, 3, 13, 16, 13);

    public WindChimeBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPE;
    }

    @Override
    protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return Shapes.empty();
    }

    @Override
    protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        BlockPos above = pos.above();
        BlockState holder = level.getBlockState(above);
        return !holder.isAir() && (holder.isFaceSturdy(level, above, Direction.DOWN) || holder.is(net.minecraft.tags.BlockTags.FENCES)
                || holder.is(net.minecraft.tags.BlockTags.SLABS) || holder.is(net.minecraft.tags.BlockTags.WALLS) || holder.is(Blocks.IRON_CHAIN)
                || holder.is(net.minecraft.tags.BlockTags.LEAVES));
    }

    @Override
    protected BlockState updateShape(BlockState state, LevelReader level, ScheduledTickAccess ticks, BlockPos pos, Direction direction,
                                     BlockPos neighbourPos, BlockState neighbour, RandomSource random) {
        return direction == Direction.UP && !canSurvive(state, level, pos) ? Blocks.AIR.defaultBlockState()
                : super.updateShape(state, level, ticks, pos, direction, neighbourPos, neighbour, random);
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        boolean storm = level.isThundering(), rain = level.isRainingAt(pos.above(2)) || level.isRaining();
        int chance = storm ? 25 : rain ? 60 : 220;
        if (random.nextInt(chance) == 0) ring(level, pos, random, storm ? 1.0F : 0.55F);
    }

    @Override
    protected void entityInside(BlockState state, Level level, BlockPos pos, net.minecraft.world.entity.Entity entity,
                                net.minecraft.world.entity.InsideBlockEffectApplier effects, boolean intersects) {
        if (level.isClientSide() && entity.getDeltaMovement().lengthSqr() > 0.003 && level.getRandom().nextInt(12) == 0) {
            ring(level, pos, level.getRandom(), 0.8F);
        }
    }

    private static void ring(Level level, BlockPos pos, RandomSource random, float volume) {
        level.playLocalSound(pos.getX() + 0.5, pos.getY() + 0.4, pos.getZ() + 0.5, SkySounds.WIND_CHIME, SoundSource.BLOCKS,
                volume, 0.9F + random.nextFloat() * 0.2F, false);
    }
}
