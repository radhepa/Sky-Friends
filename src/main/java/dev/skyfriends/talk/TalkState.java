package dev.skyfriends.talk;

import com.mojang.serialization.Codec;
import dev.skyfriends.entity.Cirri;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import net.minecraft.core.UUIDUtil;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jspecify.annotations.Nullable;

/**
 * A Cirri's side of talking: who they are ({@link Personality}, their story), what they know of every player
 * ({@link Bond}, {@link Tale}), and the conversation going on now. While you talk they hover in front of you,
 * by their manner (the Cirri's flight does that); some cut the conversation short (see {@link #leaveReason}):
 * anyone still upset with you for striking them (they turn away), the busy (later for close friends) and anyone
 * woken at night.
 */
public final class TalkState {
    private static final Codec<Map<UUID, Bond>> BONDS = Codec.unboundedMap(UUIDUtil.STRING_CODEC, Bond.CODEC);
    private static final Codec<Map<UUID, Tale>> TALES = Codec.unboundedMap(UUIDUtil.STRING_CODEC, Tale.CODEC);
    /** A conversation nobody has touched for this long (five minutes) is over. */
    private static final int MAX_IDLE = 6000;

    private record Snub(String reason, long until) {}

    private final Cirri cirri;
    private final Map<UUID, Bond> bonds = new HashMap<>();
    private final Map<UUID, Tale> tales = new HashMap<>();
    private String personality = "", story = "";
    private @Nullable UUID talkingTo;
    private int talkIdle, talkTicks, leaveAt = -1;
    private String leaveReason = "";
    private boolean woken;
    private final Map<UUID, Snub> snubs = new HashMap<>();
    /** The last line said, so the next one isn't the same. */
    public String lastLine = "";

    public TalkState(Cirri cirri) {
        this.cirri = cirri;
    }

    // -- who they are -----------------------------------------------------------------------------

    public Personality personality() {
        Personality p = Personality.of(personality, cirri.isBaby(), cirri.getRandom());
        personality = p.name();
        return p;
    }

    /** Sets their personality (tests), or lets a child who has grown up become the grown-up they were going to be. */
    public void setPersonality(Personality p) {
        personality = p.name();
    }

    public Manner manner() {
        return personality().manner;
    }

    /** Their story, chosen the first time it's needed (a child who grows up gets a grown-up's). */
    public StoryBook.@Nullable Story story() {
        StoryBook book = StoryBook.get(cirri.isBaby() ? "cirri_child" : "cirri");
        if (story.isEmpty() || book.story(story) == null) {
            StoryBook.Story pick = book.pickStory(cirri.job(), cirri.getRandom());
            story = pick == null ? "" : pick.id();
        }
        return book.story(story);
    }

    /** Grown up: a grown-up's nature and a grown-up's story (their old tales with players are kept). */
    public void grewUp() {
        try {
            personality = Personality.grownUp(Personality.valueOf(personality)).name();
        } catch (IllegalArgumentException e) {
            personality = "";
        }
        story = "";
        tales.values().forEach(t -> {
            if (t.chapter < Tale.ENDED) t.chapter = Tale.UNTOLD;
        });
    }

    public Bond bond(Player player) {
        return bonds.computeIfAbsent(player.getUUID(), id -> new Bond());
    }

    public Tale tale(Player player) {
        return tales.computeIfAbsent(player.getUUID(), id -> new Tale());
    }

    /** Their friendship level with this player (0 if they have never met). */
    public int level(Player player) {
        Bond b = bonds.get(player.getUUID());
        return b == null ? 0 : b.level();
    }

    public Map<UUID, Bond> bonds() {
        return bonds;
    }

    // -- the conversation now ---------------------------------------------------------------------

    public void start(ServerPlayer player) {
        woken = cirri.asleep();
        talkingTo = player.getUUID();
        talkIdle = 0;
        talkTicks = 0;
        leaveReason = "";
        leaveAt = -1;
        planLeave(player);
    }

    public void stop() {
        talkingTo = null;
        leaveAt = -1;
        leaveReason = "";
    }

    public boolean talking() {
        return talkingTo != null;
    }

    public boolean isTalkingTo(Player player) {
        return player.getUUID().equals(talkingTo);
    }

    public @Nullable ServerPlayer partner() {
        if (talkingTo == null || !(cirri.level() instanceof ServerLevel server)) return null;
        return server.getPlayerByUUID(talkingTo) instanceof ServerPlayer p ? p : null;
    }

    /** Called on every reply, so a conversation left open doesn't hold them forever. */
    public void keep() {
        talkIdle = 0;
    }

    /** How long this conversation has gone on, in ticks. */
    public int ticks() {
        return talkTicks;
    }

    /**
     * Works out whether (and why) they'll cut this conversation short; called when it starts and after every
     * reply, so an apology or a new level can change their mind. A reason that stays the same keeps its time.
     */
    public void planLeave(ServerPlayer player) {
        String reason = leaveReason(player);
        if (reason.isEmpty()) {
            leaveReason = "";
            leaveAt = -1;
            return;
        }
        if (reason.equals(leaveReason)) return;
        leaveReason = reason;
        boolean friends = bond(player).level() >= 6;
        var random = cirri.getRandom();
        leaveAt = talkTicks + switch (reason) {
            case "dislike" -> 140 + random.nextInt(60);
            case "sleep" -> 300 + random.nextInt(120);
            // the busy make time for close friends, but not all day
            default -> friends ? 2400 + random.nextInt(1200) : 500 + random.nextInt(400);
        };
    }

    /**
     * Why they would end it, or "" if they'll stay as long as you like: dislike (still upset with you for
     * striking them), sleep (woken at night, unless you are very dear to them) or busy (a busy personality).
     */
    public String leaveReason(ServerPlayer player) {
        Bond bond = bond(player);
        if (bond.grudge > 0) return "dislike";
        if (woken && bond.level() < 8) return "sleep";
        return manner() == Manner.BUSY ? "busy" : "";
    }

    /** Why they are going to cut the conversation short ("" if they aren't). */
    public String leaving() {
        return leaveReason;
    }

    /** Brings their leaving forward to within {@code ticks} (tests). */
    public void hurryLeave(int ticks) {
        if (leaveAt >= 0) leaveAt = Math.min(leaveAt, talkTicks + ticks);
    }

    /** They've had enough: they say so, end the conversation, and won't talk to this player again just yet. */
    public void walkOff(ServerPlayer partner) {
        String reason = leaveReason.isEmpty() ? "busy" : leaveReason;
        Conversation.walkOff(partner, cirri, reason);
        stop();
        long now = cirri.level().getGameTime();
        snubs.put(partner.getUUID(), new Snub(reason, now + switch (reason) {
            case "dislike" -> 200;
            case "sleep" -> 600;
            default -> 900;
        }));
    }

    /** Why they won't talk to this player again just yet, or null if they will. */
    public @Nullable String snubbedBy(Player player) {
        Snub snub = snubs.get(player.getUUID());
        if (snub == null) return null;
        if (cirri.level().getGameTime() >= snub.until()) {
            snubs.remove(player.getUUID());
            return null;
        }
        return snub.reason();
    }

    /** A tick of the conversation: it ends when the player goes or nobody touches it, or when they decide to leave. */
    public void tick() {
        if (talkingTo == null) return;
        ServerPlayer partner = partner();
        talkTicks++;
        if (partner == null || !partner.isAlive() || partner.distanceToSqr(cirri) > (talkTicks < 100 ? 32 * 32 : 12 * 12) || ++talkIdle > MAX_IDLE) stop();
        else if (leaveAt >= 0 && talkTicks >= leaveAt) walkOff(partner);
    }

    // -- saving -----------------------------------------------------------------------------------

    public void save(ValueOutput output) {
        output.store("Bonds", BONDS, bonds);
        output.store("Tales", TALES, tales);
        output.putString("Personality", personality);
        output.putString("Story", story);
    }

    public void load(ValueInput input) {
        bonds.clear();
        bonds.putAll(input.read("Bonds", BONDS).orElse(Map.of()));
        tales.clear();
        tales.putAll(input.read("Tales", TALES).orElse(Map.of()));
        personality = input.getStringOr("Personality", "");
        story = input.getStringOr("Story", "");
    }
}
