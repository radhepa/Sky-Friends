package dev.skyfriends.block;

import dev.skyfriends.SkyBlocks;
import dev.skyfriends.SkySounds;
import dev.skyfriends.entity.Cirri;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The wind lift. A column of rising wind stands over the stone, up to a sky village's Lift Dock
 * ({@link #top}, the dock's floor surface). Anyone in it rises (fast, easing off near the top),
 * comes to a stop just over the dock floor and is drawn sideways onto the dock ({@code landX},
 * {@code landZ}); anyone holding sneak in it sinks gently instead and lands softly by the stone.
 * Nobody takes fall damage in the wind.
 *
 * <p>Movement is worked out where it is authoritative: each client moves its own player, the server
 * moves mobs and items. The column clears itself of leaves and logs once (trees grow there after the
 * village is placed).
 */
public class WindStoneBlockEntity extends BlockEntity {
    /** How wide the column is (blocks from its centre). */
    public static final double RADIUS = 1.35;
    static final double RISE = 0.85, SINK = -0.32;

    private int top = Integer.MIN_VALUE, landX, landZ;
    private boolean cleared;

    public WindStoneBlockEntity(BlockPos pos, BlockState state) {
        super(SkyBlocks.WIND_STONE_ENTITY, pos, state);
    }

    /** Where the lift goes: the dock floor's surface y and the cell to set riders down on. */
    public void connect(int top, int landX, int landZ) {
        this.top = top;
        this.landX = landX;
        this.landZ = landZ;
        this.cleared = false;
        setChanged();
    }

    public boolean connected() {
        return top > worldPosition.getY() + 4;
    }

    public int top() {
        return top;
    }

    public BlockPos landing() {
        return new BlockPos(landX, top, landZ);
    }

    public static void tick(Level level, BlockPos pos, BlockState state, WindStoneBlockEntity be) {
        if (!be.connected()) return;
        double cx = pos.getX() + 0.5, cz = pos.getZ() + 0.5;
        if (!level.isClientSide() && !be.cleared) be.clearColumn(level);
        AABB column = new AABB(cx - RADIUS, pos.getY() + 0.5, cz - RADIUS, cx + RADIUS, be.top + 3.0, cz + RADIUS);
        for (Entity e : level.getEntitiesOfClass(Entity.class, column, e -> e.isAlive() && !e.isSpectator() && !(e instanceof Cirri))) {
            boolean mine = level.isClientSide() ? e.isLocalInstanceAuthoritative() : !(e instanceof Player);
            if (mine) be.carry(level, e, cx, cz, pos.getY());
        }
    }

    private void carry(Level level, Entity e, double cx, double cz, int base) {
        Vec3 v = e.getDeltaMovement();
        double y = e.getY();
        double vx = v.x * 0.85, vz = v.z * 0.85, vy;
        if (e.isShiftKeyDown()) {
            // sink gently; slow right down for the landing
            double floor = base + 1.0;
            vy = approach(v.y, y - floor < 3 ? -0.12 : SINK, 0.08);
        } else if (y < top - 0.15) {
            double target = Math.min(RISE, 0.22 + (top - y) * 0.09);
            vy = approach(v.y, target, 0.1);
            vx += (cx - e.getX()) * 0.04;            // stay in the middle of the column
            vz += (cz - e.getZ()) * 0.04;
            if (e.tickCount % 30 == 0 && level.isClientSide() && e instanceof Player) {
                level.playLocalSound(e.getX(), e.getY(), e.getZ(), SkySounds.WIND_STONE_LIFT, SoundSource.AMBIENT, 0.5F, 1.0F, false);
            }
        } else {
            // at the dock: hold just over the floor and drift onto the landing
            vy = Math.max(v.y * 0.5, 0.0) + (y < top + 0.25 ? 0.06 : -0.02);
            double tx = landX + 0.5 - e.getX(), tz = landZ + 0.5 - e.getZ();
            double d = Math.sqrt(tx * tx + tz * tz);
            if (d > 0.05) {
                vx = tx / d * Math.min(0.16, d * 0.2);
                vz = tz / d * Math.min(0.16, d * 0.2);
            }
        }
        e.setDeltaMovement(vx, vy, vz);
        e.resetFallDistance();
        if (!level.isClientSide()) {
            e.needsSync = true;
        } else if (e instanceof Player) {
            var random = level.getRandom();   // wisps of cloud streaming past the rider
            for (int i = 0; i < 2; i++) {
                level.addParticle(net.minecraft.core.particles.ParticleTypes.CLOUD, cx + (random.nextDouble() - 0.5) * 2.6,
                        e.getY() + random.nextDouble() * 3 - (vy > 0 ? 0 : -2), cz + (random.nextDouble() - 0.5) * 2.6, 0, vy > 0 ? -0.3 : 0.3, 0);
            }
        }
    }

    /** Clears leaves, logs, vines, snow and tall plants out of the column (once). */
    private void clearColumn(Level level) {
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        int x0 = worldPosition.getX(), z0 = worldPosition.getZ();
        for (int y = worldPosition.getY() + 1; y < top - 1; y++) {
            for (int dx = -1; dx <= 1; dx++) {
                for (int dz = -1; dz <= 1; dz++) {
                    p.set(x0 + dx, y, z0 + dz);
                    if (!level.isLoaded(p)) return;
                    BlockState s = level.getBlockState(p);
                    if (s.is(BlockTags.LEAVES) || s.is(BlockTags.LOGS) || s.is(Blocks.VINE) || s.is(Blocks.SNOW) || s.is(BlockTags.FLOWERS)
                            || s.is(Blocks.SHORT_GRASS) || s.is(Blocks.TALL_GRASS) || s.is(Blocks.BAMBOO)) {
                        level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
                    }
                }
            }
        }
        cleared = true;
        setChanged();
    }

    private static double approach(double value, double target, double step) {
        return value < target ? Math.min(target, value + step) : Math.max(target, value - step);
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        top = input.getIntOr("Top", Integer.MIN_VALUE);
        landX = input.getIntOr("LandX", 0);
        landZ = input.getIntOr("LandZ", 0);
        cleared = input.getBooleanOr("Cleared", false);
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        output.putInt("Top", top);
        output.putInt("LandX", landX);
        output.putInt("LandZ", landZ);
        output.putBoolean("Cleared", cleared);
    }

    /** The client needs the column's height too. */
    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        return saveWithoutMetadata(registries);
    }
}
