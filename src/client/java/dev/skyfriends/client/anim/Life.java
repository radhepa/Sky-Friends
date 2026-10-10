package dev.skyfriends.client.anim;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Objects;
import java.util.Random;
import java.util.Set;
import java.util.WeakHashMap;
import java.util.function.BiConsumer;
import java.util.function.Predicate;
import java.util.function.ToIntFunction;

import dev.skyfriends.anim.Clip;
import dev.skyfriends.anim.Library;

import net.minecraft.client.Minecraft;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;

/**
 * The client-side director for one person: what they act out from moment to moment. Standing folk idle and practise
 * their trade, chat with a neighbour beside them, greet a player who walks up, gesture while their line types out in
 * a conversation and listen while you choose, and react to what happens (a gift, a level of friendship, a blow).
 * Decisions happen on client ticks; the renderer samples the chosen clips every frame. Nothing is saved or synced.
 */
public final class Life {
    /**
     * How a people is animated: its pack, when it may act at all, the tags that pick its clips, who is a child, and
     * how much they are on the move this frame (0 still .. 1 going flat out: a walk's stride, or a Cirri's flight).
     */
    public record Kind(String species, Predicate<LivingEntity> able, BiConsumer<LivingEntity, Set<String>> tags, Predicate<LivingEntity> young,
                       Motion motion) {
        public Kind(String species, Predicate<LivingEntity> able, BiConsumer<LivingEntity, Set<String>> tags) {
            this(species, able, tags, LivingEntity::isBaby, (e, partial) -> Mth.clamp(e.walkAnimation.speed(partial), 0, 1) / .28F);
        }
    }

    /** How much someone is on the move (0..1) at a moment between ticks. */
    @FunctionalInterface
    public interface Motion {
        float at(LivingEntity e, float partial);
    }

    /** Someone moving faster than this isn't standing about: activities fade and reactions keep to the upper body. */
    private static final float MOVING = .22F;

    private static final Map<EntityType<?>, Kind> KINDS = new HashMap<>();
    private static final Map<LivingEntity, Life> LIVES = new WeakHashMap<>();
    private static final float FADE = 6;
    /** Whether the player is in a conversation with this entity: 0 no, 1 listening (choosing a reply), 2 it is speaking. */
    public static ToIntFunction<Entity> conversation = e -> 0;

    private static final class Playing {
        Clip clip;
        float start, speed = 1, fadeFrom = -1;
        boolean mirror;
        String trigger;

        boolean active() {
            return clip != null;
        }

        float time(float age) {
            return (age - start) / 20F * speed;
        }

        boolean over(float age) {
            return clip == null || time(age) > clip.length() || fadeFrom >= 0 && age - fadeFrom > FADE;
        }

        void fade(float age) {
            if (clip != null && fadeFrom < 0) fadeFrom = age;
        }

        float weight(float age) {
            if (clip == null) return 0;
            float w = clip.envelope(time(age));
            if (fadeFrom >= 0) w *= 1 - Clip.smooth((age - fadeFrom) / FADE);
            return w;
        }

        void clear() {
            clip = null;
            fadeFrom = -1;
            trigger = null;
        }

        void copy(Playing o) {
            clip = o.clip;
            start = o.start;
            speed = o.speed;
            fadeFrom = o.fadeFrom;
            mirror = o.mirror;
            trigger = o.trigger;
        }
    }

    private final Kind kind;
    private final Random random;
    private final boolean leftHanded;
    private final Playing activity = new Playing(), reaction = new Playing(), outgoing = new Playing();
    private int stillTicks, nextActivity, lastHurt, greetAt = -1, greetCooldown, partnerId = -1, partnerCheck, lastTick = -1;
    private boolean greeted, talking, speaking;
    private String recent, previous;

    private Life(LivingEntity entity, Kind kind) {
        this.kind = kind;
        long seed = entity.getUUID().getLeastSignificantBits() ^ entity.getUUID().getMostSignificantBits();
        this.random = new Random(seed ^ entity.getId() * 0x9E3779B9L);
        this.leftHanded = Math.floorMod(seed, 9) == 0;
        // neighbours loaded together shouldn't all start fidgeting on the same tick
        this.nextActivity = entity.tickCount + 20 + random.nextInt(100);
    }

    public static void register(EntityType<?> type, Kind kind) {
        KINDS.put(type, kind);
    }

    public static Kind kind(Entity entity) {
        return KINDS.get(entity.getType());
    }

    /** The director for this entity, or null if its people has no animations. */
    public static Life of(LivingEntity entity) {
        Kind kind = kind(entity);
        return kind == null ? null : LIVES.computeIfAbsent(entity, e -> new Life(e, kind));
    }

    /** The clip being acted out now (idle, chat or talk), or null. */
    public Clip activity() {
        return activity.clip;
    }

    /** The reaction playing now (greet, thanks, hurt...), or null. */
    public Clip reaction() {
        return reaction.clip;
    }

    public static void clear() {
        LIVES.clear();
    }

    // -- events ----------------------------------------------------------------------------------------------------

    /** A conversation moment for the person with this entity id (from the server, or the conversation window). */
    public static void cue(int entityId, String trigger) {
        var level = Minecraft.getInstance().level;
        if (level != null && level.getEntity(entityId) instanceof LivingEntity entity) {
            Life life = of(entity);
            if (life != null) life.react(entity, trigger);
        }
    }

    /** Plays a reaction now (tests and the conversation window use this too). */
    public void react(LivingEntity entity, String trigger) {
        float now = entity.tickCount;
        Clip clip = Library.current().pick(kind.species, trigger, tags(entity, -1), random, reaction.clip == null ? "" : reaction.clip.id());
        if (clip == null) return;
        start(reaction, clip, now, trigger);
        activity.fade(now);
        nextActivity = Math.max(nextActivity, (int) (now + clip.length() * 20 + 6));
    }

    /** Starts a clip by id as the activity (tests and films). */
    public boolean play(LivingEntity entity, String clipId) {
        for (Clip clip : Library.current().pack(kind.species).clips()) {
            if (clip.id().equals(clipId) || clip.id().endsWith(":" + clipId)) {
                reaction.clear();
                outgoing.clear();
                start(activity, clip, entity.tickCount, clip.trigger());
                activity.mirror = false;
                activity.speed = 1;
                nextActivity = entity.tickCount + (int) (clip.length() * 20) + 1000;
                return true;
            }
        }
        return false;
    }

    // -- per tick --------------------------------------------------------------------------------------------------

    public static void tickAll(Minecraft client) {
        if (client.level == null || client.isPaused()) return;
        Entity camera = client.getCameraEntity();
        for (Entity entity : client.level.entitiesForRendering()) {
            if (!(entity instanceof LivingEntity living) || kind(entity) == null) continue;
            if (camera != null && entity.distanceToSqr(camera) > 64 * 64) continue;
            of(living).tick(living, client);
        }
    }

    void tick(LivingEntity e, Minecraft client) {
        int now = e.tickCount;
        // a frozen or stepped world holds folk mid-motion, exactly like everything else
        if (now == lastTick) return;
        lastTick = now;
        boolean able = canAct(e);
        boolean moving = kind.motion.at(e, 0) > MOVING;
        stillTicks = able && !moving ? stillTicks + 1 : 0;
        if (reaction.over(now)) reaction.clear();
        if (outgoing.over(now)) outgoing.clear();
        if (activity.over(now)) {
            if (activity.active()) nextActivity = now + pause(e, activity.trigger);
            activity.clear();
        }
        if (!able) {
            activity.fade(now);
            reaction.fade(now);
            return;
        }
        if (e.hurtTime > lastHurt) react(e, "hurt");
        lastHurt = e.hurtTime;

        int talk = conversation.applyAsInt(e);
        boolean wasTalking = talking, wasSpeaking = speaking;
        talking = talk > 0;
        speaking = talk == 2;
        if (talking && !wasTalking && !reaction.active()) react(e, "greet");
        if (!talking && wasTalking && !reaction.active()) react(e, "farewell");
        // a new line starts: stop listening and start talking right away
        if (speaking && !wasSpeaking && activity.active() && !"talk".equals(activity.trigger)) {
            activity.fade(now);
            nextActivity = now + 2;
        }
        noticePlayer(e, client, now);
        if (activity.active() && moving && !talking) activity.fade(now);
        if (activity.active() || reaction.active() || now < nextActivity) return;

        String trigger = null;
        // in conversation they gesture while their line types out, then listen while you choose a reply
        if (talking) trigger = speaking ? "talk" : "listen";
        else if (stillTicks > 20) {
            int partner = partner(e, now);
            trigger = partner >= 0 && random.nextFloat() < .7F ? (speaker(e, partner) ? "chat_speak" : "chat_listen") : "idle";
        }
        if (trigger == null) return;
        Library library = Library.current();
        Set<String> tags = tags(e, trigger.startsWith("chat") ? partnerId : -1);
        Clip clip = library.pick(kind.species, trigger, tags, random, recent, previous);
        if (clip == null && trigger.startsWith("chat")) {
            trigger = "idle";
            clip = library.pick(kind.species, trigger, tags, random, recent, previous);
        }
        if (clip == null && trigger.equals("listen")) {
            trigger = "talk";
            clip = library.pick(kind.species, trigger, tags, random, recent, previous);
        }
        if (clip == null) {
            nextActivity = now + 40;
            return;
        }
        if (activity.active()) {
            outgoing.copy(activity);
            outgoing.fade(now);
        }
        start(activity, clip, now, trigger);
        previous = recent;
        recent = clip.id();
    }

    private void noticePlayer(LivingEntity e, Minecraft client, int now) {
        var player = client.player;
        if (player == null || talking) {
            greetAt = -1;
            return;
        }
        double distance = e.distanceToSqr(player);
        if (distance > 11 * 11) greeted = false;
        if (!greeted && now >= greetCooldown && distance < 5.5 * 5.5 && facing(e, player.getX(), player.getZ(), 80)) {
            greeted = true;
            greetCooldown = now + 1200;
            greetAt = now + 3 + random.nextInt(14);
        }
        if (greetAt >= 0 && now >= greetAt) {
            greetAt = -1;
            if (!reaction.active()) react(e, "greet");
        }
    }

    /** Another of their people standing close by and roughly in front of them: someone to chat with. */
    private int partner(LivingEntity e, int now) {
        if (now < partnerCheck) return partnerId;
        partnerCheck = now + 10;
        partnerId = -1;
        double best = Double.MAX_VALUE;
        for (LivingEntity other : e.level().getEntitiesOfClass(LivingEntity.class, e.getBoundingBox().inflate(3.2, 1, 3.2))) {
            if (other == e || !other.isAlive() || kind(other) == null || !kind(other).species().equals(kind.species)
                    || other.isSleeping() || kind(other).motion().at(other, 0) > MOVING) continue;
            if (!facing(e, other.getX(), other.getZ(), 70)) continue;
            double d = e.distanceToSqr(other);
            if (d < best) {
                best = d;
                partnerId = other.getId();
            }
        }
        return partnerId;
    }

    /** Two neighbours take turns: one speaks while the other listens, swapping every few seconds. */
    private static boolean speaker(LivingEntity e, int partner) {
        long slot = e.level().getGameTime() / 70;
        return (slot + (e.getId() < partner ? 0 : 1)) % 2 == 0;
    }

    private static boolean facing(LivingEntity e, double x, double z, float within) {
        float yaw = (float) Math.toDegrees(Math.atan2(-(x - e.getX()), z - e.getZ()));
        return Math.abs(Mth.wrapDegrees(yaw - e.getYHeadRot())) < within;
    }

    private Set<String> tags(LivingEntity e, int partner) {
        Set<String> tags = new HashSet<>();
        tags.add(kind.young.test(e) ? "child" : "adult");
        if (partner >= 0) tags.add("social");
        if (talking) tags.add("talking");
        kind.tags.accept(e, tags);
        return tags;
    }

    private void start(Playing slot, Clip clip, float now, String trigger) {
        slot.clip = clip;
        slot.start = now;
        slot.fadeFrom = -1;
        slot.trigger = trigger;
        slot.speed = .94F + random.nextFloat() * .12F;
        slot.mirror = switch (clip.mirror()) {
            case HAND -> leftHanded;
            case FREE -> leftHanded ^ random.nextFloat() < .4F;
            case NEVER -> false;
        };
    }

    private int pause(LivingEntity e, String trigger) {
        if ("talk".equals(trigger) || "listen".equals(trigger) || talking) return 4 + random.nextInt(14);
        if (trigger != null && trigger.startsWith("chat")) return 6 + random.nextInt(22);
        return kind.young.test(e) ? 10 + random.nextInt(50) : 25 + random.nextInt(110);
    }

    private boolean canAct(LivingEntity e) {
        return e.isAlive() && !e.isSleeping() && e.getPose() == net.minecraft.world.entity.Pose.STANDING && !e.isPassenger()
                && !e.isInWater() && !e.isUsingItem() && !e.isSwinging() && kind.able.test(e);
    }

    // -- per frame -------------------------------------------------------------------------------------------------

    /** Fills a render state's pose for this frame. */
    public void extract(LivingEntity e, Pose pose, float partialTicks) {
        float age = e.tickCount + partialTicks;
        pose.species = kind.species;
        float walk = Clip.smooth(Mth.clamp(kind.motion.at(e, partialTicks), 0, 1));
        float react = reaction.weight(age);
        if (react > 0) pose.layers[1].set(reaction.clip, reaction.time(age), react, reaction.mirror, 1 - walk);
        else pose.layers[1].clear();
        float act = activity.weight(age) * (1 - walk) * (1 - react);
        if (act > 0) pose.layers[0].set(activity.clip, activity.time(age), act, activity.mirror, 1);
        else pose.layers[0].clear();
        float out = outgoing.weight(age) * (1 - walk) * (1 - react);
        if (out > 0) pose.layers[2].set(outgoing.clip, Math.min(outgoing.time(age), outgoing.clip.length()), out, outgoing.mirror, 1);
        else pose.layers[2].clear();
    }

    /** Fills a pose for any entity this director knows (renderers call this). */
    public static void fill(Entity entity, Pose pose, float partialTicks) {
        if (entity instanceof LivingEntity living) {
            Life life = of(living);
            if (life != null) {
                life.extract(living, pose, partialTicks);
                return;
            }
        }
        pose.clear();
        pose.species = null;
    }

    /** The director's state for tests: the trigger of the activity and of the reaction. */
    public String describe() {
        return Objects.toString(activity.trigger) + "/" + Objects.toString(reaction.trigger);
    }
}
