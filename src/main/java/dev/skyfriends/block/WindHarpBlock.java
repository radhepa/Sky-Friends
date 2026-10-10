package dev.skyfriends.block;

import dev.skyfriends.SkySounds;
import dev.skyfriends.entity.Cirri;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * A wind harp. Play it (use it) and it sounds a phrase; every Cirri within twenty blocks turns and
 * drifts over to listen.
 */
public class WindHarpBlock extends HorizontalDirectionalBlock {
    private static final VoxelShape NORTH_SOUTH = Block.box(2, 0, 5, 14, 16, 11), EAST_WEST = Block.box(5, 0, 2, 11, 16, 14);
    /** When each harp may next be played (a phrase lasts a couple of seconds). */
    private static final Map<Long, Long> NEXT = new HashMap<>();

    public WindHarpBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return state.getValue(FACING).getAxis() == Direction.Axis.Z ? NORTH_SOUTH : EAST_WEST;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level instanceof ServerLevel server) play(server, pos, player);
        return InteractionResult.SUCCESS;
    }

    /** Plays the harp at {@code pos} (a player, or a Cirri harpist when {@code player} is null). */
    public static boolean play(ServerLevel level, BlockPos pos, Player player) {
        long now = level.getGameTime(), key = pos.asLong() ^ ((long) level.dimension().identifier().hashCode() << 40);
        if (NEXT.getOrDefault(key, 0L) > now) return false;
        NEXT.put(key, now + 50);
        if (NEXT.size() > 512) NEXT.values().removeIf(t -> t < now);
        level.playSound(null, pos, SkySounds.WIND_HARP, SoundSource.RECORDS, 1.0F, 1.0F);
        for (int i = 0; i < 4; i++) {
            level.sendParticles(ParticleTypes.NOTE, pos.getX() + 0.5, pos.getY() + 1.2 + i * 0.15, pos.getZ() + 0.5, 0,
                    level.getRandom().nextInt(25) / 24.0, 0, 0, 1);
        }
        if (player != null) {
            for (Cirri c : level.getEntitiesOfClass(Cirri.class, new AABB(pos).inflate(20), Cirri::isAlive)) c.listen(player, 160);
        }
        return true;
    }
}
