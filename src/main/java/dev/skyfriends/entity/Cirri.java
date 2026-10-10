package dev.skyfriends.entity;

import dev.skyfriends.SkyEntities;
import dev.skyfriends.SkySounds;
import dev.skyfriends.block.WindHarpBlock;
import dev.skyfriends.flight.Glide;
import dev.skyfriends.life.Chronicle;
import dev.skyfriends.life.Emote;
import dev.skyfriends.life.VillageLife;
import dev.skyfriends.talk.Conversation;
import dev.skyfriends.talk.Manner;
import dev.skyfriends.talk.TalkState;
import java.util.List;
import java.util.Locale;
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
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.util.Mth;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.Entity;
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
 * complexions and four outfits), a voice and a personality. In a sky village ({@link #settle}) they keep
 * a day: at night they sleep floating over the cushions of their nests; by day they work (harpists play
 * the harps, the bellkeeper rings the bell at dawn and dusk), soar round the village and gather at the
 * court, and (arranged by {@link VillageLife}) stop to chat in pairs, gather to sing the Evensong at dusk,
 * fly out to swim beside a passing Cloud Whale, shelter in their nests from thunder, and bring a close
 * friend a little present. Children keep close to their mothers and play tag. Now and then at dawn a couple
 * has a baby, while the village has room. The Skymerchant trades with guests.
 *
 * <p><b>Talk.</b> Right-click to talk ({@link Conversation}); while you talk they hover in front of you by
 * their manner ({@link TalkState}).
 *
 * <p>The client reads the look, whether it is asleep or working, and its job and manner (for the animations);
 * how hard it is flying, banking and climbing ({@link #flight}, {@link #bank}, {@link #climb}) is worked out on
 * each client from how it actually moves.
 */
public class Cirri extends AgeableMob implements Merchant {
    public enum Mode { SOAR, HOVER, WATCH, FLEE, SLEEP, WORK, GATHER, FOLLOW, TALK, CHAT, EVENSONG, ESCORT, PLAY, SHELTER, BRING }

    public static final byte AWAKE = 0, SLEEPING = 1, WORKING = 2;
    /** bit 0 female, bits 1-2 complexion, bits 3-4 outfit, bit 7 chosen. */
    private static final EntityDataAccessor<Byte> LOOK = SynchedEntityData.defineId(Cirri.class, EntityDataSerializers.BYTE);
    private static final EntityDataAccessor<Byte> STATE = SynchedEntityData.defineId(Cirri.class, EntityDataSerializers.BYTE);
    /** "job|manner|routine", for the client's animations. */
    private static final EntityDataAccessor<String> MOTION = SynchedEntityData.defineId(Cirri.class, EntityDataSerializers.STRING);

    /** Blocks per tick: cruising, and fleeing. */
    static final double CRUISE = 0.3, FLEE_SPEED = 0.55;
    /** Steering limits per tick: heading (radians), speed, climb. */
    static final double TURN = 0.055, ACCEL = 0.012, CLIMB = 0.02;
    /** How far from home a Cirri soars (in the wild, and in its village), and the height band it keeps. */
    static final int ROAM = 40, VILLAGE_ROAM = 30;
    // watching you, they hover close enough to talk to (within reach of a right-click)
    static final double LOW = 7.0, HIGH = 20.0, CLEARANCE = 3.0, WATCH_DISTANCE = 3.0;
    /** The night, in ticks of the day, when settled Cirri sleep; the Evensong is sung just before it. */
    public static final int NIGHT_START = 13000, NIGHT_END = 23300, EVENSONG_START = 11800, EVENSONG_END = 12900;
    /** How many Cirri a village holds before its couples stop having babies. */
    static final int VILLAGE_CAPACITY = 24;

    private Mode mode = Mode.SOAR, beforeTalk = Mode.HOVER;
    private @Nullable Vec3 target;
    private int modeTicks, targetTicks, watchCooldown, blockedTicks, workTicks, loopTicks, loopTimer;
    private @Nullable BlockPos home, bed, work;
    private String job = "";
    private @Nullable UUID mother, partner;
    private boolean settled, chasing;
    private long lastDay = -1;
    private @Nullable Player watched;
    /** Who they're with: a neighbour they chat with or play tag with, the whale they escort, the friend they bring a present to. */
    private @Nullable Entity companion;
    private @Nullable Path path;
    private @Nullable BlockPos pathGoal;
    private int pathAge;
    private @Nullable Player tradingPlayer;
    private @Nullable MerchantOffers offers;
    private @Nullable Vec3 lastGoal;
    private double bestDistance = Double.MAX_VALUE;
    private int stuckTicks;
    private final TalkState talk = new TalkState(this);

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
        builder.define(MOTION, "");
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

    /** "job|manner|routine" as the client knows it, for the animations. */
    public String motion() {
        return entityData.get(MOTION);
    }

    public String job() {
        return job;
    }

    /** Their job as shown under their name. */
    public String title() {
        if (isBaby()) return "Child";
        if (job.isEmpty()) return "Villager";
        return Character.toUpperCase(job.charAt(0)) + job.substring(1);
    }

    /** Their name (a Cirri has just the one). */
    public String firstName() {
        return hasCustomName() ? getCustomName().getString() : "Cirri";
    }

    public String villageName() {
        return settled || mother != null ? CirriKin.villageName(home()) : "the open sky";
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

    /** The one they share a nest with, if anyone. */
    public @Nullable UUID partner() {
        return partner;
    }

    public void setPartner(@Nullable UUID partner) {
        this.partner = partner;
    }

    public TalkState talk() {
        return talk;
    }

    public boolean isMerchant() {
        return "skymerchant".equals(job) && !isBaby();
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
            talk.grewUp();
            Chronicle.report(s, home(), dayNumber(), "grew_up", firstName(), "");
            Emote.SPARKLE.show(this, 0);
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
        talk.tick();
        dawn(level);
        plan(level);
        fly(level);
        unstick(level);
        entityData.set(STATE, mode == Mode.SLEEP && arrived(bedSpot(), 0.9) ? SLEEPING
                : mode == Mode.WORK && work != null && arrived(spot(work), 1.2) ? WORKING : AWAKE);
        if (tickCount % 20 == 0) {
            String motion = job + "|" + talk.manner().name().toLowerCase(Locale.ROOT) + "|" + routineTag();
            if (!motion.equals(entityData.get(MOTION))) entityData.set(MOTION, motion);
        }
    }

    /** The time of day on the overworld clock, 0-23999 (and the day number). */
    public long dayTime() {
        return Math.floorMod(level().getOverworldClockTime(), 24000L);
    }

    public long dayNumber() {
        return Math.floorDiv(level().getOverworldClockTime(), 24000L);
    }

    private boolean night(Level level) {
        long t = dayTime();
        return t >= NIGHT_START && t < NIGHT_END;
    }

    private void setMode(Mode mode, int ticks) {
        if (this.mode != mode) path = null;
        this.mode = mode;
        this.modeTicks = ticks;
        if (mode != Mode.WATCH) watched = null;
        if (mode != Mode.CHAT && mode != Mode.PLAY && mode != Mode.ESCORT && mode != Mode.BRING) companion = null;
    }

    /** What they were doing, for what they say ("work", "gather", "evensong"... children: "play", "follow"...). */
    public String routineTag() {
        Mode m = mode == Mode.TALK ? beforeTalk : mode;
        if (isBaby()) {
            return switch (m) {
                case PLAY -> "play";
                case FOLLOW -> "follow";
                case EVENSONG -> "evensong";
                case SHELTER -> "shelter";
                default -> "idle";
            };
        }
        return switch (m) {
            case WORK -> "work";
            case GATHER -> "gather";
            case SOAR, FLEE -> "soar";
            case CHAT -> "chat";
            case EVENSONG -> "evensong";
            case ESCORT -> "escort";
            case SHELTER -> "shelter";
            default -> "idle";
        };
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
            talk.stop();
            setMode(Mode.FLEE, 100);
            return;
        }
        if (mode == Mode.FLEE) {
            if (modeTicks == 0) routine(level);
            return;
        }
        // talking: they keep to you until the conversation ends
        if (talk.talking()) {
            if (mode != Mode.TALK) {
                beforeTalk = mode;
                setMode(Mode.TALK, 0);
                loopTimer = 120 + random.nextInt(120);
            }
            return;
        }
        if (mode == Mode.TALK) {
            routine(level);
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
        boolean villager = settled || (isBaby() && mother != null);
        boolean sleepy = night(level) && villager;
        if (sleepy && mode != Mode.SLEEP) {
            setMode(Mode.SLEEP, 0);
            return;
        }
        if (!sleepy && mode == Mode.SLEEP) {
            routine(level);
            return;
        }
        // thunder: everyone home to their nest, awake, till it passes
        if (villager && level.isThundering() && mode != Mode.SLEEP && mode != Mode.SHELTER) {
            setMode(Mode.SHELTER, 0);
            Emote.SWEAT.show(this, random.nextInt(20));
            return;
        }
        switch (mode) {
            case SHELTER -> {
                if (!level.isThundering()) routine(level);
            }
            case HOVER, WORK, GATHER -> {
                if (modeTicks == 0) routine(level);
                else if (mode != Mode.WORK) lookForCompany(level, 80);
                if (mode == Mode.WORK) work(level);
            }
            case FOLLOW -> {
                if (modeTicks == 0 || mum(level) == null) routine(level);
            }
            case CHAT -> {
                if (modeTicks == 0 || !(companion instanceof Cirri other) || !other.isAlive() || other.mode != Mode.CHAT || other.companion != this) {
                    routine(level);
                } else if (modeTicks % 70 == 35 && getId() < other.getId()) {
                    VillageLife.chatter(this, other);
                }
            }
            case EVENSONG -> {
                long t = dayTime();
                if (t < EVENSONG_START || t >= EVENSONG_END) routine(level);
                else if (random.nextInt(140) == 0) VillageLife.singOut(this);
            }
            case ESCORT -> {
                if (modeTicks == 0 || !(companion instanceof CloudWhale whale) || !whale.isAlive()
                        || whale.distanceToSqr(Vec3.atCenterOf(home())) > 170 * 170) {
                    routine(level);
                } else if (random.nextInt(200) == 0) {
                    VillageLife.singOut(this);
                }
            }
            case PLAY -> {
                if (modeTicks == 0 || !(companion instanceof Cirri other) || !other.isAlive() || other.mode != Mode.PLAY) {
                    routine(level);
                } else if (chasing && distanceToSqr(other) < 1.7 * 1.7) {
                    // tag! now the other one chases (after counting to three)
                    chasing = false;
                    other.chasing = true;
                    other.modeTicks = Math.min(other.modeTicks, modeTicks);
                    other.loopTicks = 30;
                    Emote.NOTE.show(this, 0);
                    Emote.EXCLAIM.show(other, 4);
                    target = null;
                }
            }
            case BRING -> {
                if (modeTicks == 0 || !(companion instanceof ServerPlayer p) || !p.isAlive() || p.isSpectator()) {
                    routine(level);
                } else if (distanceToSqr(p) < 2.6 * 2.6) {
                    VillageLife.present(this, p);
                    watch(p, 100);
                }
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

    /** Free for village life to ask something of: awake, not talking, working, fleeing, sheltering or already busy with someone. */
    public boolean free() {
        return isAlive() && !talk.talking() && tradingPlayer == null && switch (mode) {
            case SOAR, HOVER, GATHER, FOLLOW, WATCH -> true;
            default -> false;
        };
    }

    // -- village life (arranged by VillageLife) ------------------------------------------------------

    /** Hover facing a neighbour and chat for a while (they do the same). */
    public void chatWith(Cirri other, int ticks) {
        setMode(Mode.CHAT, ticks);
        companion = other;
    }

    /** Join the Evensong: circle over the Veil Court with the village, singing the day down. */
    public void joinEvensong() {
        setMode(Mode.EVENSONG, 0);
        target = null;
    }

    /** Fly out and swim alongside a passing Cloud Whale for a while; {@code slot} keeps escorts apart. */
    public void escort(CloudWhale whale, int slot, int ticks) {
        setMode(Mode.ESCORT, ticks);
        companion = whale;
        targetTicks = slot;
        Emote.EXCLAIM.show(this, random.nextInt(10));
    }

    /** Play tag with another child: one chases, the other flees. */
    public void play(Cirri other, boolean chaser, int ticks) {
        setMode(Mode.PLAY, ticks);
        companion = other;
        chasing = chaser;
        target = null;
    }

    /** Fly over to a close friend with a little present. */
    public void bring(ServerPlayer player) {
        setMode(Mode.BRING, 400);
        companion = player;
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

    /** Someone is playing music for it (a wind harp, a flute): come and listen, unless asleep or busy with someone. */
    public void listen(Player player, int ticks) {
        if (mode == Mode.SLEEP || mode == Mode.FLEE || mode == Mode.TALK || mode == Mode.SHELTER) return;
        watch(player, ticks);
        Emote.NOTE.show(this, random.nextInt(16));
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
        boolean going = mode == Mode.SOAR || mode == Mode.WORK || mode == Mode.GATHER || mode == Mode.SLEEP || mode == Mode.FLEE
                || mode == Mode.SHELTER || mode == Mode.EVENSONG;
        Vec3 goal = mode == Mode.SLEEP || mode == Mode.SHELTER ? bedSpot() : mode == Mode.WORK && work != null ? spot(work)
                : mode == Mode.EVENSONG ? Vec3.atCenterOf(home()).add(0, 6, 0) : target;
        if (!going || goal == null || arrived(goal, mode == Mode.EVENSONG ? 16 : 1.5)) {   // in the ring is there
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
        // only unseen: a player close by who can see them (not one out in the court while they're in their nest)
        for (Player p : level.players()) {
            if (!p.isSpectator() && p.distanceToSqr(this) < 24 * 24 && p.hasLineOfSight(this)) return;
        }
        if ((mode == Mode.SLEEP || mode == Mode.SHELTER || mode == Mode.WORK) && d < 48) {
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
        // a path is kept until its goal really moves (the way out of a house shifts a little as they go, the
        // Evensong ring turns slowly): re-planning every tick, they'd never get past the first step
        if (path == null || pathGoal == null || pathGoal.distSqr(goalCell) > 16 || path.isDone() || ++pathAge > 80) {
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
        long t = dayTime();
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
        Entity facing = null;     // who they turn to face, if anyone
        switch (mode) {
            case HOVER -> want = new double[] {0, Mth.sin(tickCount * 0.05F) * 0.02, 0};
            case WATCH -> {
                want = Glide.toward(arr(here), arr(before(watched, WATCH_DISTANCE, 0.6)), 0.18, 4.0);
                open = false;
                facing = watched;
            }
            case TALK -> {
                ServerPlayer p = talk.partner();
                want = p == null ? new double[] {0, 0, 0} : Glide.toward(arr(here), arr(talkSpot(p)), 0.22, 2.0);
                open = false;
                facing = loopTicks > 0 ? null : p;
            }
            case CHAT -> {
                if (companion instanceof Cirri other) {
                    Vec3 from = here.subtract(other.position()).multiply(1, 0, 1);
                    from = from.lengthSqr() < 1.0E-4 ? new Vec3(1, 0, 0) : from.normalize();
                    double gap = isBaby() || other.isBaby() ? 1.8 : 2.4;
                    Vec3 spot = other.position().add(from.scale(gap));
                    spot = new Vec3(spot.x, (here.y + other.getY()) / 2 + Mth.sin(tickCount * 0.05F) * 0.08, spot.z);
                    want = Glide.toward(arr(here), arr(arrived(spot, 6) ? spot : waypoint(spot)), 0.2, 2.0);
                    facing = other;
                } else {
                    want = new double[] {0, 0, 0};
                }
                open = false;
            }
            case EVENSONG -> {
                // a slow ring over the Veil Court, each at their own height and distance
                long seed = getUUID().getLeastSignificantBits();
                double radius = (isBaby() ? 4.0 : 6.0) + Math.floorMod(seed, 5);
                double angle = (tickCount + Math.floorMod(seed >> 8, 400)) * 0.008 * (Math.floorMod(seed, 2) == 0 ? 1 : -1);
                Vec3 c = Vec3.atCenterOf(home());
                Vec3 spot = new Vec3(c.x + Math.cos(angle) * radius, c.y + 6.0 + Math.floorMod(seed >> 4, 3) + Mth.sin(tickCount * 0.04F) * 0.4,
                        c.z + Math.sin(angle) * radius);
                boolean near = arrived(spot, 12);
                want = Glide.toward(arr(here), arr(arrived(spot, 20) ? spot : waypoint(spot)), near ? 0.16 : 0.3, 3.0);
                open = false;
            }
            case ESCORT -> {
                if (companion instanceof CloudWhale whale) {
                    double rad = whale.heading() * Mth.DEG_TO_RAD;
                    Vec3 ahead = new Vec3(-Math.sin(rad), 0, Math.cos(rad)), side = new Vec3(ahead.z, 0, -ahead.x);
                    int slot = targetTicks;
                    double out = (slot % 2 == 0 ? 1 : -1) * (whale.getBbWidth() * 0.9 + 2.5 + slot);
                    Vec3 spot = whale.position().add(side.scale(out)).add(ahead.scale(slot - 1.0)).add(0, whale.getBbHeight() * 0.5 + Mth.sin(tickCount * 0.06F + slot), 0);
                    want = Glide.toward(arr(here), arr(spot), 0.42, 5.0);
                } else {
                    want = new double[] {0, 0, 0};
                }
            }
            case PLAY -> {
                if (loopTicks > 0) {
                    loopTicks--;           // counting to three before giving chase
                    want = new double[] {0, Mth.sin(tickCount * 0.3F) * 0.03, 0};
                } else if (chasing && companion instanceof Cirri other) {
                    want = Glide.toward(arr(here), arr(other.position()), 0.3, 1.0);
                } else {
                    if (target == null || arrived(target, 2.0)) {
                        Vec3 c = Vec3.atCenterOf(home());
                        target = new Vec3(c.x + (random.nextDouble() - 0.5) * 20, c.y + 3 + random.nextDouble() * 5, c.z + (random.nextDouble() - 0.5) * 20);
                    }
                    want = Glide.toward(arr(here), arr(waypoint(target)), 0.27, 2.0);
                }
                open = false;
            }
            case BRING -> {
                want = companion instanceof Player p ? Glide.toward(arr(here), arr(before(p, 1.8, 0.4)), 0.3, 2.0) : new double[] {0, 0, 0};
                open = false;
                facing = companion;
            }
            case FLEE -> {
                boolean in = indoors();
                want = Glide.toward(arr(here), arr(in ? waypoint(target) : target), in ? 0.3 : FLEE_SPEED, 2.0);
                open = !in;
            }
            case SLEEP, WORK, SHELTER -> {
                Vec3 goal = mode == Mode.WORK ? work != null ? spot(work) : null : bedSpot();
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

        double turn = mode == Mode.FLEE ? TURN * 2 : mode == Mode.SOAR || mode == Mode.ESCORT ? TURN : TURN * 2.5;
        double[] nv = Glide.steer(arr(v), want, turn, mode == Mode.FLEE || mode == Mode.PLAY ? ACCEL * 2 : ACCEL * 1.5, CLIMB * 1.5);
        setDeltaMovement(nv[0], nv[1], nv[2]);

        // the body faces where it flies; with someone (watching, talking, chatting), it turns to them
        double speed = Math.hypot(nv[0], nv[2]);
        if (facing != null && speed < 0.12) {
            getLookControl().setLookAt(facing, 30.0F, 30.0F);
            Vec3 to = facing.position().subtract(here);
            float face = (float) (Mth.atan2(to.z, to.x) * Mth.RAD_TO_DEG) - 90.0F;
            setYRot(Mth.rotLerp(0.1F, getYRot(), face));
        } else if (speed > 0.06) {
            setYRot((float) (Mth.atan2(nv[2], nv[0]) * Mth.RAD_TO_DEG) - 90.0F);
        } else if (mode != Mode.SLEEP) {
            setYRot(Mth.rotLerp(0.05F, getYRot(), yHeadRot));
        }
        yBodyRot = getYRot();
    }

    /** A spot {@code distance} in front of someone (on the side the Cirri is on), {@code lift} above their eyes less a Cirri's eye height. */
    private Vec3 before(Entity who, double distance, double lift) {
        Vec3 eye = who.getEyePosition();
        Vec3 from = position().subtract(eye).multiply(1, 0, 1);
        from = from.lengthSqr() < 1.0E-4 ? who.getLookAngle().multiply(1, 0, 1) : from;
        from = from.lengthSqr() < 1.0E-4 ? new Vec3(1, 0, 0) : from.normalize();
        return eye.add(from.scale(distance)).add(0, lift - getEyeHeight() * 0.9, 0);
    }

    /**
     * Where to hover while you talk, by their manner: close in front of you at about your eye level; the shy a
     * little further (and further still if you crowd them); the restless drift round you; the flighty now and
     * then dart up into a quick loop and come straight back.
     */
    private Vec3 talkSpot(ServerPlayer p) {
        Manner manner = talk.manner();
        double dist = manner == Manner.SHY ? (distanceToSqr(p) < 3.0 * 3.0 ? 4.6 : 4.0) : isBaby() ? 2.2 : 2.6;
        Vec3 eye = p.getEyePosition();
        Vec3 from = position().subtract(eye).multiply(1, 0, 1);
        from = from.lengthSqr() < 1.0E-4 ? p.getLookAngle().multiply(1, 0, 1) : from;
        from = from.lengthSqr() < 1.0E-4 ? new Vec3(1, 0, 0) : from.normalize();
        if (manner == Manner.RESTLESS) {
            double a = Mth.sin(talk.ticks() * 0.02F) * 0.035;      // a slow sway round you, a little each tick
            from = new Vec3(from.x * Math.cos(a) - from.z * Math.sin(a), 0, from.x * Math.sin(a) + from.z * Math.cos(a));
        }
        // eyes a little above yours: a Cirri floats, feet clear of whatever you stand on
        Vec3 spot = eye.add(from.scale(dist)).add(0, -getEyeHeight() + (isBaby() ? 0.4 : 0.6) + Mth.sin(tickCount * 0.06F) * 0.12, 0);
        if (manner == Manner.FLIGHTY) {
            if (loopTicks > 0) {
                double a = (40 - --loopTicks) / 40.0 * Math.PI * 2;
                Vec3 side = new Vec3(from.z, 0, -from.x);
                spot = spot.add(0, (1 - Math.cos(a)) * 1.6, 0).add(side.scale(Math.sin(a) * 1.3));
            } else if (--loopTimer <= 0) {
                loopTimer = 160 + random.nextInt(140);
                loopTicks = 40;
            }
        }
        return spot;
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
        long time = level.getOverworldClockTime(), day = Math.floorDiv(time, 24000L);
        if (day == lastDay || Math.floorMod(time, 24000L) > 3000) return;
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
        Cirri husband = village.stream().filter(c -> !c.isBaby() && !c.female() && (getUUID().equals(c.partner)
                || c.getUUID().equals(partner) || partner == null && c.partner == null && c.bed != null && c.bed.distSqr(bed) < 8 * 8))
                .findFirst().orElse(null);
        long mine = village.stream().filter(c -> c.isBaby() && getUUID().equals(c.mother)).count();
        if (husband == null || mine >= 2) return null;
        if (partner == null) {
            // a couple from before nests were shared by name: they are partners now
            partner = husband.getUUID();
            husband.partner = getUUID();
        }
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
        Chronicle.report(level, centre, dayNumber(), "born", baby.firstName(), firstName());
        Emote.SPARKLE.show(this, 0);
        Emote.HEART.show(husband, 8);
        return baby;
    }

    // -- people -----------------------------------------------------------------------------------

    /** Right-click: talk (the Skymerchant's wares are a button in the conversation). */
    @Override
    protected InteractionResult mobInteract(Player player, InteractionHand hand) {
        if (hand != InteractionHand.MAIN_HAND) return InteractionResult.PASS;
        if (level().isClientSide()) return InteractionResult.SUCCESS;
        if (mode == Mode.FLEE || !isAlive()) return InteractionResult.PASS;
        if (!(player instanceof ServerPlayer sp)) return InteractionResult.PASS;
        if (talk.talking() && !talk.isTalkingTo(player)) {
            sp.sendOverlayMessage(Component.literal(firstName() + " is talking with someone else."));
            return InteractionResult.SUCCESS;
        }
        Conversation.open(sp, this);
        return InteractionResult.SUCCESS;
    }

    /** The conversation has started: they turn to you (and, woken, wake). */
    public void beginTalk(ServerPlayer player) {
        if (mode != Mode.TALK) beforeTalk = mode == Mode.SLEEP ? Mode.HOVER : mode;
        playSound(greetSound(), getSoundVolume(), getVoicePitch());
    }

    /** The conversation is over. */
    public void endTalk() {
        talk.stop();
    }

    /** The Skymerchant opens their wares. */
    public void openTrade(Player player) {
        if (!isMerchant() || getOffers().isEmpty()) return;
        setTradingPlayer(player);
        watch(player, 400);
        openTradingScreen(player, getDisplayName(), 1);
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        if (source.getEntity() instanceof ServerPlayer player && !player.isCreative()) {
            var bond = talk.bond(player);
            bond.today(dayNumber());
            bond.points = Math.max(0, bond.points - 15);
            bond.hurtUntil = level.getGameTime() + 6000;
            bond.grudge = Math.min(dev.skyfriends.talk.Bond.MAX_GRUDGE, bond.grudge + 1);
            talk.tale(player).remember(dayNumber(), "You struck " + firstName() + ".");
            if (talk.isTalkingTo(player)) talk.stop();
            if (settled || mother != null) Chronicle.report(level, home(), dayNumber(), "struck", firstName(), player.getName().getString());
            Emote.ANGER.show(this, 2);
        }
        return super.hurtServer(level, source, damage);
    }

    @Override
    public void die(DamageSource source) {
        setNoGravity(false);   // the veils give out
        stopTrading();
        talk.stop();
        if (level() instanceof ServerLevel level && (settled || mother != null)) {
            Chronicle.report(level, home(), dayNumber(), "passed", firstName(), "");
        }
        super.die(source);
    }

    @Override public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) { return false; }
    @Override protected void checkFallDamage(double y, boolean onGround, BlockState state, BlockPos pos) {}
    @Override public boolean onClimbable() { return false; }
    @Override public boolean removeWhenFarAway(double distSqr) { return false; }
    @Override public int getMaxHeadXRot() { return 40; }
    /** Asleep, or holding their place in the air while you talk, they aren't shoved about. */
    @Override public boolean isPushable() { return !asleep() && mode != Mode.TALK; }

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
        if (partner != null) output.store("Partner", net.minecraft.core.UUIDUtil.CODEC, partner);
        if (offers != null && !offers.isEmpty()) output.store("Offers", MerchantOffers.CODEC, offers);
        talk.save(output);
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
        partner = input.read("Partner", net.minecraft.core.UUIDUtil.CODEC).orElse(null);
        Optional<MerchantOffers> saved = input.read("Offers", MerchantOffers.CODEC);
        offers = saved.orElse(null);
        talk.load(input);
    }

    // -- voices: wordless humming, like Village Friends villagers ------------------------------------------

    public SoundEvent greetSound() {
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

    /** At the Evensong they hum far more often. */
    @Override public int getAmbientSoundInterval() { return asleep() ? 160 : mode == Mode.EVENSONG ? 90 : 320; }
    @Override public float getVoicePitch() { return 0.94F + random.nextFloat() * 0.12F; }
    @Override protected float getSoundVolume() { return asleep() ? 0.35F : 0.8F; }
}
