package dev.skyfriends.entity;

import dev.skyfriends.SkySounds;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * A Cloud Whale: a huge, gentle whale swimming slowly across the high sky in long, almost straight
 * lines, turning a little now and then, rising over mountains, blowing a puff of cloud and singing
 * (heard from far away). It harms nobody; hurt, it swims off faster. Whales come and go: the
 * {@link SkySpawner} sends one past a player now and then, and one far from everyone swims away.
 */
public class CloudWhale extends PathfinderMob {
    static final double CRUISE = 0.11, HURRY = 0.24;
    static final int MIN_Y = 160;

    private float heading;
    private int altitude, turnIn, songIn, blowIn, hurry;

    // client: the slow wave down the body
    public float wave, waveO;

    public CloudWhale(EntityType<? extends CloudWhale> type, Level level) {
        super(type, level);
        setNoGravity(true);
        heading = random.nextFloat() * 360.0F;
        altitude = 205;
        songIn = 200 + random.nextInt(400);
        blowIn = 100 + random.nextInt(300);

    }

    public static AttributeSupplier.Builder attributes() {
        return Mob.createMobAttributes().add(Attributes.MAX_HEALTH, 120.0).add(Attributes.MOVEMENT_SPEED, 0.1)
                .add(Attributes.FLYING_SPEED, 0.1).add(Attributes.KNOCKBACK_RESISTANCE, 1.0);
    }

    /** Set it off: swimming this way, at this height. */
    /** Which way it swims, in degrees (as yaw). */
    public float heading() {
        return heading;
    }

    public void launch(float heading, int altitude) {
        this.heading = heading;
        this.altitude = altitude;
        setYRot(heading);
        yBodyRot = heading;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (!isNoGravity()) setNoGravity(true);
        if (--turnIn <= 0) {
            turnIn = 200 + random.nextInt(400);
            heading += (random.nextFloat() - 0.5F) * 50.0F;
        }
        // rise over high ground well ahead
        double rad = heading * Mth.DEG_TO_RAD;
        int aheadX = Mth.floor(getX() - Math.sin(rad) * 28), aheadZ = Mth.floor(getZ() + Math.cos(rad) * 28);
        int ground = Math.max(level.getHeight(Heightmap.Types.MOTION_BLOCKING, getBlockX(), getBlockZ()),
                level.hasChunkAt(new BlockPos(aheadX, 0, aheadZ)) ? level.getHeight(Heightmap.Types.MOTION_BLOCKING, aheadX, aheadZ) : 0);
        double wantY = Math.max(Math.max(altitude, ground + 30), MIN_Y) + Mth.sin(tickCount * 0.01F) * 3;
        double speed = hurry > 0 ? HURRY : CRUISE;
        if (hurry > 0) hurry--;
        Vec3 want = new Vec3(-Math.sin(rad) * speed, Mth.clamp((wantY - getY()) * 0.02, -0.05, 0.08), Math.cos(rad) * speed);
        setDeltaMovement(getDeltaMovement().add(want.subtract(getDeltaMovement()).scale(0.04)));
        setYRot(Mth.rotLerp(0.02F, getYRot(), heading));
        yBodyRot = getYRot();
        if (horizontalCollision) heading += 90.0F;
        if (--songIn <= 0) {
            songIn = 500 + random.nextInt(700);
            level.playSound(null, getX(), getY(), getZ(), SkySounds.CLOUD_WHALE_SONG, SoundSource.NEUTRAL, 6.0F, 0.9F + random.nextFloat() * 0.2F);
        }
        if (--blowIn <= 0) {
            blowIn = 200 + random.nextInt(400);
            Vec3 head = position().add(-Math.sin(rad) * 6, getBbHeight() + 0.5, Math.cos(rad) * 6);
            level.sendParticles(ParticleTypes.CLOUD, head.x, head.y, head.z, 24, 0.4, 0.8, 0.4, 0.06);
        }
    }

    /** A whale far from every player swims off into the distance. */
    @Override
    public void checkDespawn() {
        Player near = level().getNearestPlayer(this, -1.0);
        if (near == null || near.distanceToSqr(this) > 240 * 240) discard();
    }

    @Override
    public void travel(Vec3 input) {
        if (isNoAi()) setDeltaMovement(getDeltaMovement().scale(0.9));
        move(MoverType.SELF, getDeltaMovement());
    }

    @Override
    public void tick() {
        super.tick();
        resetFallDistance();
        if (level().isClientSide()) {
            waveO = wave;
            wave += 0.035F + (hurry > 0 ? 0.03F : 0.0F);
        }
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        hurry = 200;
        if (source.getEntity() != null) {
            Vec3 away = position().subtract(source.getEntity().position());
            heading = (float) (Mth.atan2(away.z, away.x) * Mth.RAD_TO_DEG) - 90.0F;
        }
        return super.hurtServer(level, source, amount);
    }

    @Override public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) { return false; }
    @Override protected void checkFallDamage(double y, boolean onGround, BlockState state, BlockPos pos) {}
    @Override public boolean isPushable() { return false; }
    @Override public int getMaxHeadYRot() { return 10; }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putFloat("Heading", heading);
        output.putInt("Altitude", altitude);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        heading = input.getFloatOr("Heading", 0.0F);
        altitude = input.getIntOr("Altitude", 205);
    }

    @Override protected SoundEvent getAmbientSound() { return null; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SkySounds.CLOUD_WHALE_HURT; }
    @Override protected SoundEvent getDeathSound() { return SkySounds.CLOUD_WHALE_DEATH; }
    @Override protected float getSoundVolume() { return 4.0F; }
}
