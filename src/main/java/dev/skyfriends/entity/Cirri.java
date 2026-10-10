package dev.skyfriends.entity;

import dev.skyfriends.SkyEntities;
import dev.skyfriends.SkySounds;
import dev.skyfriends.block.WindHarpBlock;
import dev.skyfriends.flight.Glide;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.util.Mth;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.BodyRotationControl;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.trading.Merchant;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.BellBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.pathfinder.Path;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Cirri: wingless sky-folk who fly on their veils and never set foot on the ground.
 *
 * <p><b>Flight.</b> A Cirri is always in the air. It soars in long arcs (its heading turns at a limited
 * rate, {@link Glide}), slows to hover upright, stops a few blocks from a player to watch them, and
 * flees up and away when hurt. Out in the open it keeps clear of the ground and climbs over anything
 * ahead; going somewhere in its village (its bed, its work, the court) it follows a flying path.
 *
 * <p><b>Life.</b> Women and men (and their children), each with a name, a look (one of three
 * complexions and four outfits) and a voice: hums, a greeting, cries when hurt. In a sky village
 * ({@link #settle}) they keep a day: at night they sleep floating over the cushions of their nests;
 * by day they work (harpists play the harps, the bellkeeper rings the bell at dawn and dusk), soar
 * round the village and gather at the court. Children keep close to their mothers. Now and then at
 * dawn a couple has a baby, while the village has room. The Skymerchant trades with guests.
 *
 * <p>The client reads only the look and whether it is asleep or working; how hard it is flying,
 * banking and climbing ({@link #flight}, {@link #bank}, {@link #climb}) is worked out on each client
 * from how it actually moves.
 */
public class Cirri extends AgeableMob implements Merchant {
    public enum Mode { SOAR, HOVER, WATCH, FLEE, SLEEP, WORK, GATHER, FOLLOW }

    public static final byte AWAKE = 0, SLEEPING = 1, WORKING = 2;
    /** bit 0 female, bits 1-2 complexion, bits 3-4 outfit, bit 7 chosen. */
    private static final EntityDataAccessor<Byte> LOOK = SynchedEntityData.defineId(Cirri.class, EntityDataSerializers.BYTE);
    private static final EntityDataAccessor<Byte> STATE = SynchedEntityData.defineId(Cirri.class, EntityDataSerializers.BYTE);

    /** Blocks per tick: cruising, and fleeing. */
    static final double CRUISE = 0.3, FLEE_SPEED = 0.55;
    /** Steering limits per tick: heading (radians), speed, climb. */
    static final double TURN = 0.055, ACCEL = 0.012, CLIMB = 0.02;
    /** How far from home a Cirri soars (in the wild, and in its village), and the height band it keeps. */
    static final int ROAM = 40, VILLAGE_ROAM = 30;
    static final double LOW = 7.0, HIGH = 20.0, CLEARANCE = 3.0, WATCH_DISTANCE = 5.5;
    /** The night, in ticks of the day, when settled Cirri sleep. */
    static final int NIGHT_START = 13000, NIGHT_END = 23300;
    /** How many Cirri a village holds before its couples stop having babies. */
    static final int VILLAGE_CAPACITY = 24;

    private Mode mode = Mode.SOAR;
    private @Nullable Vec3 target;
    private int modeTicks, targetTicks, watchCooldown, blockedTicks, workTicks;
    private @Nullable BlockPos home, bed, work;
    private String job = "";
    private @Nullable UUID mother;
    private boolean settled;
    private long lastDay = -1;
    private @Nullable Player watched;
    private @Nullable Path path;
    private @Nullable BlockPos pathGoal;
    private int pathAge;
    private @Nullable Player tradingPlayer;
    private @Nullable MerchantOffers offers;
    private @Nullable Vec3 lastGoal;
    private double bestDistance = Double.MAX_VALUE;
    private int stuckTicks;

    // -- client animation state: smoothed from the Cirri's real motion (0..1 flight, -1..1 bank and climb) --
    public float flight, flightO, bank, bankO, climb, climbO;

    public Cirri(EntityType<? extends Cirri> type, Level level) {
        super(type, level);
        setNoGravity(true);
    }

    public static AttributeSupplier.Builder attributes() {
        return Mob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 20.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FLYING_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 40.0);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(LOOK, (byte) 0);
        builder.define(STATE, AWAKE);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(1, new LookAtPlayerGoal(this, Player.class, 14.0F, 0.04F));
        goalSelector.addGoal(2, new RandomLookAroundGoal(this));
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        FlyingPathNavigation nav = new FlyingPathNavigation(this, level);
        nav.setCanOpenDoors(false);
        nav.setCanFloat(true);
        return nav;
    }

    /** The body faces where the Cirri flies (its yaw, set by the flight below); the head turns at most 75 degrees from it. */
    @Override
    protected BodyRotationControl createBodyControl() {
        return new BodyRotationControl(this) {
            @Override
            public void clientTick() {
                yBodyRot = getYRot();
                yHeadRot = yBodyRot + Mth.clamp(Mth.wrapDegrees(yHeadRot - yBodyRot), -75.0F, 75.0F);
            }
        };
    }

    // -- who it is --------------------------------------------------------------------------------

    public boolean female() {
        return (entityData.get(LOOK) & 1) != 0;
    }

    public int complexion() {
        return (entityData.get(LOOK) >> 1) & 3;
    }

    public int palette() {
        return (entityData.get(LOOK) >> 3) & 3;
    }

    public void setLook(boolean female, int complexion, int palette) {
        entityData.set(LOOK, (byte) (0x80 | (female ? 1 : 0) | (Math.floorMod(complexion, CirriKin.COMPLEXIONS) << 1)
                | (Math.floorMod(palette, CirriKin.PALETTES) << 3)));
    }

    private boolean lookChosen() {
        return (entityData.get(LOOK) & 0x80) != 0;
    }

    public byte state() {
        return entityData.get(STATE);
    }

    public boolean asleep() {
        return state() == SLEEPING;
    }

    public String job() {
        return job;
    }

    public Mode mode() {
        return mode;
    }

    public boolean settled() {
        return settled;
    }

    public BlockPos home() {
        if (home == null) home = blockPosition();
        return home;
    }

    public @Nullable BlockPos bed() {
        return bed;
    }

    public @Nullable BlockPos work() {
        return work;
    }

    public @Nullable UUID mother() {
        return mother;
    }

    /** Soar round this point from now on. */
    public void setHome(BlockPos home) {
        this.home = home;
        this.target = null;
    }

    /**
     * Make this Cirri a villager: the village's centre (where it soars round and gathers), its bed
     * (the air cell it sleeps floating in), its work spot and job (or none).
     */
    public void settle(BlockPos centre, @Nullable BlockPos bed, @Nullable BlockPos work, String job) {
        this.home = centre;
        this.bed = bed;
        this.work = work;
        this.job = job == null ? "" : job;
        this.settled = true;
        this.target = null;
        setPersistenceRequired();
    }

    /** A child of this mother, living in the village round {@code centre}. */
    public void raiseBy(BlockPos centre, UUID mother) {
        this.home = centre;
        this.mother = mother;
        this.settled = false;
        setPersistenceRequired();
    }

    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
                                                  @Nullable SpawnGroupData data) {
        SpawnGroupData out = super.finalizeSpawn(level, difficulty, reason, data);
        if (!lookChosen()) setLook(random.nextBoolean(), random.nextInt(CirriKin.COMPLEXIONS), CirriKin.palette(job, random));
        if (!hasCustomName()) setCustomName(Component.literal(CirriKin.name(female(), random)));
        return out;
    }

    /** A child who grows up becomes one of the village: it keeps to its mother's nest until it has one of its own. */
    @Override
    protected void ageBoundaryReached() {
        super.ageBoundaryReached();
        if (!isBaby() && mother != null && level() instanceof ServerLevel s) {
            Cirri m = mum(s);
            settle(home(), m != null && m.bed != null ? m.bed.above() : null, null, "");
        }
    }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return SkyEntities.CIRRI.create(level, EntitySpawnReason.BREEDING);
    }

    // -- the flight plan --------------------------------------------------------------------------

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (!isNoGravity()) setNoGravity(true);
        dawn(level);
        plan(level);
        fly(level);
        unstick(level);
        entityData.set(STATE, mode == Mode.SLEEP && arrived(bedSpot(), 0.9) ? SLEEPING
                : mode == Mode.WORK && work != null && arrived(spot(work), 1.2) ? WORKING : AWAKE);
    }

    private long dayTime(Level level) {
        return level.getOverworldClockTime();
    }

    private boolean night(Level level) {
        long t = dayTime(level) % 24000;
        return t >= NIGHT_START && t < NIGHT_END;
    }

    private void setMode(Mode mode, int ticks) {
        if (this.mode != mode) path = null;
        this.mode = mode;
        this.modeTicks = ticks;
        if (mode != Mode.WATCH) watched = null;
    }

    private void plan(ServerLevel level) {
        if (watchCooldown > 0) watchCooldown--;
        if (modeTicks > 0) modeTicks--;
        LivingEntity attacker = getLastHurtByMob();
        if (attacker != null && tickCount - getLastHurtByMobTimestamp() < 3 && mode != Mode.FLEE) {
            // up and away from whoever hurt it
            Vec3 away = position().subtract(attacker.position()).multiply(1, 0, 1);
            away = away.lengthSqr() < 1.0E-4 ? new Vec3(random.nextDouble() - 0.5, 0, random.nextDouble() - 0.5) : away;
            target = position().add(away.normalize().scale(24)).add(0, 10, 0);
            stopTrading();
            setMode(Mode.FLEE, 100);
            return;
        }
        if (mode == Mode.FLEE) {
            if (modeTicks == 0) routine(level);
            return;
        }
        if (tradingPlayer != null) {
            if (!stillValid(tradingPlayer)) stopTrading();
            else if (mode != Mode.WATCH || watched != tradingPlayer) watch(tradingPlayer, 100);
        }
        if (mode == Mode.WATCH) {
            if (modeTicks == 0 || watched == null || !watched.isAlive() || watched.isSpectator() || distanceToSqr(watched) > 22 * 22) {
                watchCooldown = 400 + random.nextInt(400);
                routine(level);
            }
            return;
        }
        // night: to bed (villagers, and any child following its mother home)
        boolean sleepy = night(level) && (settled || (isBaby() && mother != null));
        if (sleepy && mode != Mode.SLEEP) {
            setMode(Mode.SLEEP, 0);
            return;
        }
        if (!sleepy && mode == Mode.SLEEP) {
            routine(level);
            return;
        }
        switch (mode) {
            case HOVER, WORK, GATHER -> {
                if (modeTicks == 0) routine(level);
                else if (mode != Mode.WORK) lookForCompany(level, 80);
                if (mode == Mode.WORK) work(level);
            }
            case FOLLOW -> {
                if (modeTicks == 0 || mum(level) == null) routine(level);
            }
            case SOAR -> {
                targetTicks++;
                if (target == null || targetTicks > 400 || position().distanceToSqr(target) < 3.0 * 3.0) {
                    if (modeTicks == 0 && settled) routine(level);
                    else if (target != null && random.nextInt(4) == 0) setMode(Mode.HOVER, 60 + random.nextInt(100));
                    else newCourse(level);
                } else {
                    lookForCompany(level, 120);
                }
            }
            default -> {}
        }
    }

    /** What to do next: a child keeps near its mother; a villager works, gathers or soars round the village. */
    private void routine(ServerLevel level) {
        if (isBaby() && mum(level) != null) {
            setMode(Mode.FOLLOW, 400 + random.nextInt(400));
            return;
        }
        if (settled && !isBaby()) {
            float r = random.nextFloat();
            if (work != null && r < 0.5F) {
                setMode(Mode.WORK, 600 + random.nextInt(600));
                return;
            }
            if (r < 0.68F) {
                target = Vec3.atCenterOf(home()).add((random.nextDouble() - 0.5) * 10, 1.5 + random.nextDouble() * 2, (random.nextDouble() - 0.5) * 10);
                setMode(Mode.GATHER, 400 + random.nextInt(400));
                return;
            }
            setMode(Mode.SOAR, 500 + random.nextInt(500));
            target = pickTarget(level);
            targetTicks = 0;
            return;
        }
        newCourse(level);
    }

    private @Nullable Cirri mum(ServerLevel level) {
        if (mother == null) return null;
        var e = level.getEntity(mother);
        return e instanceof Cirri c && c.isAlive() && distanceToSqr(c) < 64 * 64 ? c : null;
    }

    /** Sometimes stop to watch a player nearby (1 in {@code chance} each tick). */
    private void lookForCompany(ServerLevel level, int chance) {
        if (watchCooldown > 0 || random.nextInt(chance) != 0) return;
        Player player = level.getNearestPlayer(this, 14.0);
        if (player != null && !player.isSpectator() && hasLineOfSight(player)) watch(player, 120 + random.nextInt(120));
    }

    /** Hover at a respectful distance and look at this player for a while. */
    public void watch(Player player, int ticks) {
        boolean already = mode == Mode.WATCH && watched == player;
        setMode(Mode.WATCH, ticks);
        watched = player;
        if (!already && !level().isClientSide()) playSound(greetSound(), getSoundVolume(), getVoicePitch());
    }

    /** Someone is playing music for it (a wind harp, a flute): come and listen, unless asleep. */
    public void listen(Player player, int ticks) {
        if (mode == Mode.SLEEP || mode == Mode.FLEE) return;
        watch(player, ticks);
    }

    /** Stop and hover here for a while. */
    public void hover(int ticks) {
        setMode(Mode.HOVER, ticks);
    }

    private void newCourse(ServerLevel level) {
        setMode(Mode.SOAR, settled ? 500 + random.nextInt(500) : 0);
        target = pickTarget(level);
        targetTicks = 0;
    }

    /** A point 12-32 blocks off in the open sky, never more than the roaming distance from home. */
    private Vec3 pickTarget(ServerLevel level) {
        BlockPos h = home();
        int roam = settled ? VILLAGE_ROAM : ROAM;
        for (int i = 0; i < 12; i++) {
            double angle = random.nextDouble() * Math.PI * 2, dist = 12 + random.nextDouble() * 20;
            double x = getX() + Math.cos(angle) * dist, z = getZ() + Math.sin(angle) * dist;
            if (Math.hypot(x - h.getX(), z - h.getZ()) > roam) {
                // turn back toward home: a point somewhere inside the roaming circle
                double a = random.nextDouble() * Math.PI * 2, r = random.nextDouble() * roam * 0.6;
                x = h.getX() + Math.cos(a) * r;
                z = h.getZ() + Math.sin(a) * r;
            }
            if (!level.hasChunkAt(BlockPos.containing(x, getY(), z))) continue;
            int ground = level.getHeight(Heightmap.Types.MOTION_BLOCKING, Mth.floor(x), Mth.floor(z));
            // a villager keeps to its village's height even where the land lies far below
            double floor = settled ? Math.max(ground, h.getY() - 4) : ground;
            double y = Math.min(floor + LOW + random.nextDouble() * (HIGH - LOW), level.getMaxY() - 6);
            return new Vec3(x, y, z);
        }
        return position().add(0, 3, 0);
    }

    private static Vec3 spot(BlockPos cell) {
        return new Vec3(cell.getX() + 0.5, cell.getY() + 0.1, cell.getZ() + 0.5);
    }

    private @Nullable Vec3 bedSpot() {
        if (bed != null) return spot(bed);
        if (isBaby() && level() instanceof ServerLevel s) {
            Cirri m = mum(s);
            if (m != null) {
                BlockPos b = m.bed != null ? m.bed : m.blockPosition();
                return spot(b).add(0.6, 0.3, 0.6);
            }
        }
        return settled ? spot(home()).add(0, 2, 0) : null;
    }

    private boolean arrived(@Nullable Vec3 spot, double within) {
        return spot != null && position().distanceToSqr(spot) < within * within;
    }

    /**
     * A Cirri that has got no closer to where it is going for ten seconds (wedged in a tight room, say) and that no
     * player is near enough to see slips free: into its bed or to its work when that is where it
     * was going, otherwise out to the open sky above it.
     */
    private void unstick(ServerLevel level) {
        if (tickCount % 20 != 0) return;
        boolean going = mode == Mode.SOAR || mode == Mode.WORK || mode == Mode.GATHER || mode == Mode.SLEEP || mode == Mode.FLEE;
        Vec3 goal = mode == Mode.SLEEP ? bedSpot() : mode == Mode.WORK && work != null ? spot(work) : target;
        if (!going || goal == null || arrived(goal, 1.5)) {
            stuckTicks = 0;
            lastGoal = null;
            return;
        }
        double d = position().distanceTo(goal);
        if (lastGoal == null || lastGoal.distanceToSqr(goal) > 4.0 || d < bestDistance - 1.0) {
            lastGoal = goal;                    // a new goal, or real headway toward it
            bestDistance = d;
            stuckTicks = 0;
            return;
        }
        stuckTicks += 20;
        if (stuckTicks < 200) return;
        stuckTicks = 0;
        lastGoal = null;
        path = null;
        if (level.getNearestPlayer(getX(), getY(), getZ(), 24.0, p -> !p.isSpectator()) != null) return;
        if ((mode == Mode.SLEEP || mode == Mode.WORK) && d < 48) {
            snapTo(goal.x, goal.y, goal.z, getYRot(), 0.0F);
            return;
        }
        BlockPos.MutableBlockPos p = blockPosition().mutable();
        for (int up = 0; up < 24; up++, p.move(0, 1, 0)) {
            if (level.canSeeSky(p) && level.getBlockState(p).getCollisionShape(level, p).isEmpty()
                    && level.getBlockState(p.above()).getCollisionShape(level, p.above()).isEmpty()) {
                snapTo(p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, getYRot(), 0.0F);
                return;
            }
        }
    }

    /** For tests: what it is doing and where it is going. */
    public String debug() {
        return String.format("mode %s target %s indoors %s path %s goal %s v %.3f bed %s", mode,
                target == null ? "-" : BlockPos.containing(target).toShortString(), indoors(),
                path == null ? "none" : (path.getNextNodeIndex() + "/" + path.getNodeCount() + (path.canReach() ? " reaches" : " partial")),
                pathGoal == null ? "-" : pathGoal.toShortString(), getDeltaMovement().length(), bed == null ? "-" : bed.toShortString());
    }

    /** Under a roof (it can't see the sky): it must find its way out before flying anywhere far. */
    private boolean indoors() {
        return !level().canSeeSky(BlockPos.containing(getEyePosition()));
    }

    /**
     * The next point on the way somewhere: straight there over open sky while far off (aiming a few
     * blocks above it); from indoors, or once close, along a flying path round walls and out through
     * doorways, windows and balconies. Far from the goal and indoors, the path leads to a point of open
     * sky about 18 blocks toward it.
     */
    private Vec3 waypoint(Vec3 goal) {
        Vec3 target = goal;
        if (position().distanceToSqr(goal) > 24 * 24) {
            if (!indoors()) return goal.add(0, 5, 0);
            Vec3 dir = goal.subtract(position()).multiply(1, 0, 1);
            dir = dir.lengthSqr() < 1.0E-4 ? new Vec3(1, 0, 0) : dir.normalize();
            target = position().add(dir.scale(18)).add(0, 4, 0);
        }
        BlockPos goalCell = BlockPos.containing(target);
        if (path == null || !goalCell.equals(pathGoal) || path.isDone() || ++pathAge > 80) {
            path = getNavigation().createPath(goalCell, 1);
            if (path == null && target != goal) path = getNavigation().createPath(goalCell.above(6), 2);
            pathGoal = goalCell;
            pathAge = 0;
        }
        if (path == null || path.isDone()) return target;
        BlockPos node = path.getNextNodePos();
        Vec3 at = new Vec3(node.getX() + 0.5, node.getY() + 0.2, node.getZ() + 0.5);
        if (position().distanceToSqr(at) < 1.0) {
            path.advance();
            if (path.isDone()) return target;
            node = path.getNextNodePos();
            at = new Vec3(node.getX() + 0.5, node.getY() + 0.2, node.getZ() + 0.5);
        }
        return path.getNextNodeIndex() >= path.getNodeCount() - 1 ? target : at;
    }

    /** At work: harpists play the harp by their spot now and then; the bellkeeper rings at dawn and dusk. */
    private void work(ServerLevel level) {
        if (work == null || !arrived(spot(work), 1.2) || ++workTicks % 20 != 0) return;
        long t = dayTime(level) % 24000;
        if ("harpist".equals(job) && random.nextInt(5) == 0) {
            BlockPos harp = find(level, work, s -> s.getBlock() instanceof WindHarpBlock);
            if (harp != null) WindHarpBlock.play(level, harp, null);
        } else if ("bellkeeper".equals(job) && (t < 400 || (t >= 12000 && t < 12400)) && workTicks % 60 == 0) {
            BlockPos bell = find(level, work, s -> s.getBlock() instanceof BellBlock);
            if (bell != null && level.getBlockState(bell).getBlock() instanceof BellBlock b) b.attemptToRing(this, level, bell, Direction.NORTH);
        }
    }

    private static @Nullable BlockPos find(ServerLevel level, BlockPos around, java.util.function.Predicate<BlockState> test) {
        for (BlockPos p : BlockPos.betweenClosed(around.offset(-4, -3, -4), around.offset(4, 3, 4))) {
            if (test.test(level.getBlockState(p))) return p.immutable();
        }
        return null;
    }

    /** Steer toward what the plan wants, keep clear of the ground and of anything ahead, and move. */
    private void fly(ServerLevel level) {
        Vec3 here = position();
        double[] want;
        boolean open = true;      // out in the open sky: keep clear of the ground and of what's ahead
        switch (mode) {
            case HOVER -> want = new double[] {0, Mth.sin(tickCount * 0.05F) * 0.02, 0};
            case WATCH -> {
                Vec3 eye = watched.getEyePosition();
                Vec3 from = here.subtract(eye).multiply(1, 0, 1);
                from = from.lengthSqr() < 1.0E-4 ? new Vec3(1, 0, 0) : from.normalize();
                Vec3 spot = eye.add(from.scale(WATCH_DISTANCE)).add(0, 0.6, 0);
                want = Glide.toward(arr(here), arr(spot), 0.18, 4.0);
                open = false;
            }
            case FLEE -> {
                boolean in = indoors();
                want = Glide.toward(arr(here), arr(in ? waypoint(target) : target), in ? 0.3 : FLEE_SPEED, 2.0);
                open = !in;
            }
            case SLEEP, WORK -> {
                Vec3 goal = mode == Mode.SLEEP ? bedSpot() : work != null ? spot(work) : null;
                if (goal == null) {
                    want = new double[] {0, 0, 0};
                } else if (arrived(goal, 1.0)) {
                    want = Glide.toward(arr(here), arr(goal.add(0, mode == Mode.SLEEP ? Mth.sin(tickCount * 0.04F) * 0.08 : 0, 0)), 0.06, 1.0);
                } else {
                    want = Glide.toward(arr(here), arr(waypoint(goal)), 0.22, 2.0);
                }
                open = false;
            }
            case GATHER -> {
                want = target == null ? new double[] {0, 0, 0} : arrived(target, 1.5) ? new double[] {0, Mth.sin(tickCount * 0.05F) * 0.02, 0}
                        : Glide.toward(arr(here), arr(waypoint(target)), 0.24, 3.0);
                open = target == null || position().distanceToSqr(target) > 24 * 24;
            }
            case FOLLOW -> {
                Cirri m = mum(level);
                Vec3 by = m == null ? here : m.position().add(Math.cos(tickCount * 0.03) * 2.2, 0.8 + Math.sin(tickCount * 0.05) * 0.5,
                        Math.sin(tickCount * 0.03) * 2.2);
                want = Glide.toward(arr(here), arr(by), 0.34, 3.0);
                open = false;
            }
            default -> {
                if (target == null) {
                    want = new double[] {0, 0, 0};
                } else if (indoors()) {
                    want = Glide.toward(arr(here), arr(waypoint(target)), 0.22, 2.0);   // find the way out first
                    open = false;
                } else {
                    want = Glide.toward(arr(here), arr(target), CRUISE, 5.0);
                }
            }
        }

        Vec3 v = getDeltaMovement();
        if (open) {
            // never low over the ground: climb when within CLEARANCE of it (or of water)
            int ground = level.getHeight(Heightmap.Types.MOTION_BLOCKING, getBlockX(), getBlockZ());
            if (getY() < ground + CLEARANCE) want[1] = Math.max(want[1], 0.18);
            // something ahead: climb over it, slowing down; after a while give up on that heading
            if (blockedAhead(level, v) || horizontalCollision) {
                want[0] *= 0.3;
                want[2] *= 0.3;
                want[1] = Math.max(want[1], 0.22);
                if (++blockedTicks > 30 && mode == Mode.SOAR) {
                    target = pickTarget(level).add(0, 6, 0);
                    targetTicks = 0;
                    blockedTicks = 0;
                }
            } else {
                blockedTicks = 0;
            }
        } else if (horizontalCollision && mode != Mode.SLEEP) {
            want[1] = Math.max(want[1], 0.12);       // brushed a wall on the way: lift a little
        }
        if (isInWater() || isInLava()) want[1] = 0.3;

        double turn = mode == Mode.FLEE ? TURN * 2 : mode == Mode.SOAR ? TURN : TURN * 2.5;
        double[] nv = Glide.steer(arr(v), want, turn, mode == Mode.FLEE ? ACCEL * 2 : ACCEL * 1.5, CLIMB * 1.5);
        setDeltaMovement(nv[0], nv[1], nv[2]);

        // the body faces where it flies; hovering, working or watching, it turns slowly to where it looks
        double speed = Math.hypot(nv[0], nv[2]);
        if (mode == Mode.WATCH && watched != null) {
            getLookControl().setLookAt(watched, 30.0F, 30.0F);
            Vec3 to = watched.position().subtract(here);
            float face = (float) (Mth.atan2(to.z, to.x) * Mth.RAD_TO_DEG) - 90.0F;
            setYRot(Mth.rotLerp(0.08F, getYRot(), face));
        } else if (speed > 0.06) {
            setYRot((float) (Mth.atan2(nv[2], nv[0]) * Mth.RAD_TO_DEG) - 90.0F);
        } else if (mode != Mode.SLEEP) {
            setYRot(Mth.rotLerp(0.05F, getYRot(), yHeadRot));
        }
        yBodyRot = getYRot();
    }

    /** Is there something solid 1-3 blocks ahead (at the feet, the middle or the head)? */
    private boolean blockedAhead(ServerLevel level, Vec3 v) {
        double speed = Math.hypot(v.x, v.z);
        if (speed < 0.02) return false;
        double dx = v.x / speed, dz = v.z / speed;
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        double h = getBbHeight();
        for (int d = 1; d <= 3; d++) {
            for (double up : new double[] {0.2, h * 0.5, h * 0.92}) {
                p.set(getX() + dx * d, getY() + up + v.y * d * 3, getZ() + dz * d);
                BlockState state = level.getBlockState(p);
                if (!state.getCollisionShape(level, p).isEmpty() || !state.getFluidState().isEmpty()) return true;
            }
        }
        return false;
    }

    private static double[] arr(Vec3 v) {
        return new double[] {v.x, v.y, v.z};
    }

    /** It moves exactly as it steers: no gravity, no ground friction (a Cirri without AI just eases to a stop). */
    @Override
    public void travel(Vec3 input) {
        if (isNoAi()) setDeltaMovement(getDeltaMovement().scale(0.8));
        move(MoverType.SELF, getDeltaMovement());
    }

    @Override
    public void tick() {
        super.tick();
        resetFallDistance();
        if (level().isClientSide()) animate();
    }

    /** Client: smooth how hard it is flying, banking and climbing, from how it actually moved this tick. */
    private void animate() {
        flightO = flight;
        bankO = bank;
        climbO = climb;
        double dx = getX() - xo, dy = getY() - yo, dz = getZ() - zo;
        float speed = (float) Math.sqrt(dx * dx + dz * dz) / (isBaby() ? 0.8F : 1.0F);
        flight += (Mth.clamp(speed / 0.26F, 0.0F, 1.0F) - flight) * 0.1F;
        float turning = Mth.wrapDegrees(yBodyRot - yBodyRotO);
        bank += (Mth.clamp(turning / 4.0F, -1.0F, 1.0F) * flight - bank) * 0.12F;
        climb += (Mth.clamp((float) dy / 0.2F, -1.0F, 1.0F) - climb) * 0.1F;
        if (flight > 0.8F && random.nextInt(10) == 0) {
            // a faint wisp trailing from the veils
            Vec3 back = Vec3.directionFromRotation(0, yBodyRot).scale(-1.2);
            level().addParticle(ParticleTypes.CLOUD, getX() + back.x, getY() + 0.9, getZ() + back.z, 0, 0, 0);
        }
    }

    // -- dawn: restocking, and now and then a baby --------------------------------------------------

    private void dawn(ServerLevel level) {
        long time = dayTime(level), day = time / 24000;
        if (day == lastDay || time % 24000 > 3000) return;
        boolean first = lastDay < 0;
        lastDay = day;
        if (offers != null) offers.forEach(MerchantOffer::resetUses);
        if (!first) maybeHaveBaby(level);
    }

    /** A woman of a village whose husband shares her nest, with fewer than two little ones, may have a baby at dawn. */
    void maybeHaveBaby(ServerLevel level) {
        if (isBaby() || !female() || !settled || bed == null || random.nextInt(4) != 0) return;
        haveBaby(level);
    }

    /** The birth itself, if the village has room and her husband shares her nest (the game test calls this directly). */
    public @Nullable Cirri haveBaby(ServerLevel level) {
        if (isBaby() || !female() || !settled || bed == null) return null;
        BlockPos centre = home();
        List<Cirri> village = level.getEntitiesOfClass(Cirri.class, new AABB(centre).inflate(64), c -> c.isAlive() && centre.equals(c.home));
        if (village.size() >= VILLAGE_CAPACITY) return null;
        boolean husband = village.stream().anyMatch(c -> !c.isBaby() && !c.female() && c.bed != null && c.bed.distSqr(bed) < 8 * 8);
        long mine = village.stream().filter(c -> c.isBaby() && getUUID().equals(c.mother)).count();
        if (!husband || mine >= 2) return null;
        Cirri baby = SkyEntities.CIRRI.create(level, EntitySpawnReason.BREEDING);
        if (baby == null) return null;
        Vec3 at = spot(bed).add(0.5, 0.4, 0.5);
        baby.snapTo(at.x, at.y, at.z, getYRot(), 0.0F);
        baby.setBaby(true);
        boolean girl = random.nextBoolean();
        baby.setLook(girl, random.nextBoolean() ? complexion() : random.nextInt(CirriKin.COMPLEXIONS), girl ? 0 : 2);
        baby.setCustomName(Component.literal(CirriKin.name(girl, random)));
        baby.raiseBy(centre, getUUID());
        level.addFreshEntity(baby);
        level.sendParticles(ParticleTypes.HEART, at.x, at.y + 0.6, at.z, 5, 0.5, 0.4, 0.5, 0.0);
        playSound(greetSound(), getSoundVolume(), getVoicePitch());
        return baby;
    }

    // -- people -----------------------------------------------------------------------------------

    /** Right-click: the Skymerchant trades; anyone else (awake) turns to you and says hello. */
    @Override
    protected InteractionResult mobInteract(Player player, InteractionHand hand) {
        if (level().isClientSide()) return InteractionResult.SUCCESS;
        if (asleep() || mode == Mode.FLEE) return InteractionResult.PASS;
        if ("skymerchant".equals(job) && !isBaby() && tradingPlayer == null && !getOffers().isEmpty()) {
            setTradingPlayer(player);
            watch(player, 400);
            openTradingScreen(player, getDisplayName(), 1);
        } else {
            watch(player, 200);
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    public void die(DamageSource source) {
        setNoGravity(false);   // the veils give out
        stopTrading();
        super.die(source);
    }

    @Override public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) { return false; }
    @Override protected void checkFallDamage(double y, boolean onGround, BlockState state, BlockPos pos) {}
    @Override public boolean onClimbable() { return false; }
    @Override public boolean removeWhenFarAway(double distSqr) { return false; }
    @Override public int getMaxHeadXRot() { return 40; }
    @Override public boolean isPushable() { return !asleep(); }

    // -- trading (the Skymerchant) ---------------------------------------------------------------------

    @Override public void setTradingPlayer(@Nullable Player player) { this.tradingPlayer = player; }
    @Override public @Nullable Player getTradingPlayer() { return tradingPlayer; }

    @Override
    public MerchantOffers getOffers() {
        if (offers == null) offers = "skymerchant".equals(job) ? CirriKin.wares() : new MerchantOffers();
        return offers;
    }

    @Override public void overrideOffers(MerchantOffers offers) {}

    @Override
    public void notifyTrade(MerchantOffer offer) {
        offer.increaseUses();
        ambientSoundTime = -getAmbientSoundInterval();
        if (level() instanceof ServerLevel server) {
            server.sendParticles(ParticleTypes.HAPPY_VILLAGER, getX(), getEyeY() + 0.3, getZ(), 4, 0.4, 0.3, 0.4, 0.0);
        }
    }

    @Override public void notifyTradeUpdated(ItemStack stack) {}
    @Override public int getVillagerXp() { return 0; }
    @Override public void overrideXp(int xp) {}
    @Override public boolean showProgressBar() { return false; }
    @Override public SoundEvent getNotifyTradeSound() { return greetSound(); }
    @Override public boolean isClientSide() { return level().isClientSide(); }

    @Override
    public boolean stillValid(Player player) {
        return tradingPlayer == player && isAlive() && distanceToSqr(player) < 10 * 10;
    }

    private void stopTrading() {
        tradingPlayer = null;          // the trading screen sees stillValid() turn false and closes
    }

    // -- saving ----------------------------------------------------------------------------------------

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putByte("Look", entityData.get(LOOK));
        output.putString("Job", job);
        output.putBoolean("Settled", settled);
        output.putLong("LastDay", lastDay);
        if (home != null) output.store("Home", BlockPos.CODEC, home);
        if (bed != null) output.store("Bed", BlockPos.CODEC, bed);
        if (work != null) output.store("Work", BlockPos.CODEC, work);
        if (mother != null) output.store("Mother", net.minecraft.core.UUIDUtil.CODEC, mother);
        if (offers != null && !offers.isEmpty()) output.store("Offers", MerchantOffers.CODEC, offers);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        entityData.set(LOOK, input.getByteOr("Look", (byte) 0));
        job = input.getStringOr("Job", "");
        settled = input.getBooleanOr("Settled", false);
        lastDay = input.getLongOr("LastDay", -1L);
        home = input.read("Home", BlockPos.CODEC).orElse(null);
        bed = input.read("Bed", BlockPos.CODEC).orElse(null);
        work = input.read("Work", BlockPos.CODEC).orElse(null);
        mother = input.read("Mother", net.minecraft.core.UUIDUtil.CODEC).orElse(null);
        Optional<MerchantOffers> saved = input.read("Offers", MerchantOffers.CODEC);
        offers = saved.orElse(null);
    }

    // -- voices: wordless humming, like Village Friends villagers ------------------------------------------

    private SoundEvent greetSound() {
        return isBaby() ? SkySounds.CIRRI_CHILD_GREET : female() ? SkySounds.CIRRI_FEMALE_GREET : SkySounds.CIRRI_MALE_GREET;
    }

    @Override
    protected SoundEvent getAmbientSound() {
        if (asleep()) return SkySounds.CIRRI_SLEEP;
        return isBaby() ? SkySounds.CIRRI_CHILD_HUM : female() ? SkySounds.CIRRI_FEMALE_HUM : SkySounds.CIRRI_MALE_HUM;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return isBaby() ? SkySounds.CIRRI_CHILD_HURT : female() ? SkySounds.CIRRI_FEMALE_HURT : SkySounds.CIRRI_MALE_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return isBaby() ? SkySounds.CIRRI_CHILD_DEATH : female() ? SkySounds.CIRRI_FEMALE_DEATH : SkySounds.CIRRI_MALE_DEATH;
    }

    @Override public int getAmbientSoundInterval() { return asleep() ? 160 : 320; }
    @Override public float getVoicePitch() { return 0.94F + random.nextFloat() * 0.12F; }
    @Override protected float getSoundVolume() { return asleep() ? 0.35F : 0.8F; }
}
