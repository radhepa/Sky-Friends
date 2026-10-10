package dev.skyfriends.block;

import dev.skyfriends.SkyBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import org.jspecify.annotations.Nullable;

/**
 * The Wind Stone under a sky village: the foot of the wind lift. It can't be broken (it belongs to
 * the village); see {@link WindStoneBlockEntity} for the lift itself.
 */
public class WindStoneBlock extends BaseEntityBlock {

    public WindStoneBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    /** Wisps rising off the stone: you can see from a distance where the wind stands. */
    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, net.minecraft.util.RandomSource random) {
        for (int i = 0; i < 2; i++) {
            level.addParticle(net.minecraft.core.particles.ParticleTypes.WHITE_ASH, pos.getX() + 0.5 + (random.nextDouble() - 0.5) * 2.4,
                    pos.getY() + 1.1 + random.nextDouble() * 4, pos.getZ() + 0.5 + (random.nextDouble() - 0.5) * 2.4, 0, 0.5, 0);
        }
        if (random.nextInt(3) == 0) {
            level.addParticle(net.minecraft.core.particles.ParticleTypes.CLOUD, pos.getX() + 0.5 + (random.nextDouble() - 0.5) * 2,
                    pos.getY() + 1.2, pos.getZ() + 0.5 + (random.nextDouble() - 0.5) * 2, 0, 0.35, 0);
        }
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new WindStoneBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return createTickerHelper(type, SkyBlocks.WIND_STONE_ENTITY, WindStoneBlockEntity::tick);
    }
}
