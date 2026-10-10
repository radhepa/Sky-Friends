package dev.skyfriends.entity;

import dev.skyfriends.SkyItems;
import dev.skyfriends.SkySounds;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.util.Mth;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * Cloud Koi swim through the air in schools round the Cirri's koi pools (their home): each keeps a
 * little apart from its neighbours, swims the way they swim and toward the middle of the school, and
 * never strays far from home. Startled, a koi darts away. Now and then one sheds a Sky Scale, which
 * drifts down for whoever is below. Three colourings: kohaku, yamabuki and sora.
 */
public class CloudKoi extends PathfinderMob {
    private static final EntityDataAccessor<Byte> COAT = SynchedEntityData.defineId(CloudKoi.class, EntityDataSerializers.BYTE);
    public static final int COATS = 3;
    static final double SPEED = 0.13, DART = 0.4, RANGE = 9.0;

    private @Nullable BlockPos home;
    private int shedIn, dartTicks;
    private Vec3 wander = Vec3.ZERO;
    private List<CloudKoi> school = List.of();

    // client: tail-beat phase speeds up with speed
    public float swim, swimO;

    public CloudKoi(EntityType<? extends CloudKoi> type, Level level) {
        super(type, level);
        setNoGravity(true);
        shedIn = 6000 + random.nextInt(6000);
    }

    public static AttributeSupplier.Builder attributes() {
        return Mob.createMobAttributes().add(Attributes.MAX_HEALTH, 4.0).add(Attributes.MOVEMENT_SPEED, 0.2).add(Attributes.FLYING_SPEED, 0.2);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(COAT, (byte) 0);
    }

    public int coat() {
        return Math.floorMod(entityData.get(COAT), COATS);
    }

    public void setCoat(int coat) {
        entityData.set(COAT, (byte) Math.floorMod(coat, COATS));
    }

    public BlockPos home() {
        if (home == null) home = blockPosition();
        return home;
    }

    public void setHome(BlockPos home) {
        this.home = home;
    }

    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
                                                  @Nullable SpawnGroupData data) {
        // kohaku and yamabuki are common, the sky-blue sora rarer
        float r = random.nextFloat();
        setCoat(r < 0.45F ? 0 : r < 0.8F ? 1 : 2);
        home = blockPosition();
        return super.finalizeSpawn(level, difficulty, reason, data);
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (!isNoGravity()) setNoGravity(true);
        if (tickCount % 10 == 0) {
            school = level.getEntitiesOfClass(CloudKoi.class, getBoundingBox().inflate(6), k -> k != this && k.isAlive());
        }
        if (tickCount % 80 == 0 || wander == Vec3.ZERO) {
            wander = new Vec3((random.nextDouble() - 0.5) * 8, (random.nextDouble() - 0.5) * 3, (random.nextDouble() - 0.5) * 8);
        }
        Vec3 here = position();
        Vec3 sep = Vec3.ZERO, ali = Vec3.ZERO, coh = Vec3.ZERO;
        for (CloudKoi k : school) {
            Vec3 d = here.subtract(k.position());
            double len = d.length();
            if (len < 1.4 && len > 1.0E-4) sep = sep.add(d.scale(1.0 / (len * len)));
            ali = ali.add(k.getDeltaMovement());
            coh = coh.add(k.position());
        }
        if (!school.isEmpty()) {
            ali = ali.scale(1.0 / school.size());
            coh = coh.scale(1.0 / school.size()).subtract(here);
        }
        Vec3 toHome = Vec3.atCenterOf(home()).add(wander).subtract(here);
        double far = toHome.length();
        Vec3 want = sep.scale(1.6).add(ali.scale(6.0)).add(coh.scale(0.25)).add(toHome.scale(far > RANGE ? 0.3 : 0.06));
        // keep off the ground and out of walls
        BlockPos below = blockPosition().below();
        if (!level.getBlockState(below).getCollisionShape(level, below).isEmpty()) want = want.add(0, 0.6, 0);
        if (horizontalCollision) want = want.add(0, 0.4, 0).add(getDeltaMovement().scale(-3));
        double speed = dartTicks > 0 ? DART : SPEED;
        if (dartTicks > 0) dartTicks--;
        Vec3 v = want.lengthSqr() < 1.0E-6 ? getDeltaMovement() : want.normalize().scale(speed);
        setDeltaMovement(getDeltaMovement().scale(0.88).add(v.scale(0.12)));
        Vec3 nv = getDeltaMovement();
        if (nv.horizontalDistanceSqr() > 1.0E-5) {
            setYRot((float) (Mth.atan2(nv.z, nv.x) * Mth.RAD_TO_DEG) - 90.0F);
            yBodyRot = getYRot();
            setXRot((float) (-Mth.atan2(nv.y, nv.horizontalDistance()) * Mth.RAD_TO_DEG));
        }
        if (--shedIn <= 0) {
            shedIn = 6000 + random.nextInt(6000);
            spawnAtLocation(level, SkyItems.SKY_SCALE.getDefaultInstance());
            playSound(SkySounds.CLOUD_KOI_FLUTTER, 0.6F, 1.2F);
        }
    }

    @Override
    public void travel(Vec3 input) {
        if (isNoAi()) setDeltaMovement(getDeltaMovement().scale(0.8));
        move(MoverType.SELF, getDeltaMovement());
    }

    @Override
    public void tick() {
        super.tick();
        resetFallDistance();
        if (level().isClientSide()) {
            swimO = swim;
            double dx = getX() - xo, dz = getZ() - zo;
            swim += 0.25F + (float) Math.sqrt(dx * dx + dz * dz) * 3.0F;
        }
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        dartTicks = 40;
        return super.hurtServer(level, source, amount);
    }

    @Override public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) { return false; }
    @Override protected void checkFallDamage(double y, boolean onGround, BlockState state, BlockPos pos) {}
    @Override public boolean removeWhenFarAway(double distSqr) { return false; }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putByte("Coat", entityData.get(COAT));
        if (home != null) output.store("Home", BlockPos.CODEC, home);
        output.putInt("ShedIn", shedIn);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        entityData.set(COAT, input.getByteOr("Coat", (byte) 0));
        home = input.read("Home", BlockPos.CODEC).orElse(null);
        shedIn = input.getIntOr("ShedIn", 6000);
    }

    @Override protected SoundEvent getAmbientSound() { return SkySounds.CLOUD_KOI_FLUTTER; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SkySounds.CLOUD_KOI_FLUTTER; }
    @Override protected SoundEvent getDeathSound() { return SkySounds.CLOUD_KOI_FLUTTER; }
    @Override public int getAmbientSoundInterval() { return 400; }
    @Override protected float getSoundVolume() { return 0.4F; }
}
