package dev.skyfriends.life;

import dev.skyfriends.SkyEntities;
import dev.skyfriends.SkyItems;
import dev.skyfriends.entity.Cirri;
import dev.skyfriends.entity.CirriKin;
import dev.skyfriends.entity.CloudWhale;
import dev.skyfriends.talk.Bond;
import dev.skyfriends.talk.Friendship;
import dev.skyfriends.talk.TalkWorld;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.UUID;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A sky village going about its day, seen from outside: neighbours stopping in pairs to chat (with bubbles that
 * show how they feel about each other), the whole village circling over the Veil Court at dusk to sing the
 * Evensong, Cirri flying out to swim beside a passing Cloud Whale, children playing tag, news of storms and
 * whales, and how they greet you: the village's name as you arrive, a heart from close friends, and once a day
 * a close friend flying over with a little present. Runs on the server, a few times a second.
 */
public final class VillageLife {
    private static final Random RANDOM = new Random();
    /** The village each player was last in (its home), to show the title card once per visit. */
    private static final Map<UUID, BlockPos> VISITING = new HashMap<>();

    private VillageLife() {}

    public static void register() {
        PayloadTypeRegistry.clientboundPlay().register(EmotePayload.TYPE, EmotePayload.CODEC);
        PayloadTypeRegistry.clientboundPlay().register(ArrivalPayload.TYPE, ArrivalPayload.CODEC);
    }

    public static void tick(ServerLevel level) {
        long now = level.getGameTime();
        if (now % 20 != 7) return;
        List<? extends Cirri> all = level.getEntities(SkyEntities.CIRRI, Cirri::isAlive);
        Map<BlockPos, List<Cirri>> villages = new HashMap<>();
        for (Cirri c : all) if (c.settled() || c.mother() != null) villages.computeIfAbsent(c.home(), h -> new ArrayList<>()).add(c);
        long time = Math.floorMod(level.getOverworldClockTime(), 24000L), day = Math.floorDiv(level.getOverworldClockTime(), 24000L);
        for (var e : villages.entrySet()) live(level, e.getKey(), e.getValue(), now, time, day);
        if (now % 40 == 7) for (ServerPlayer player : level.players()) visit(level, player, villages, day);
    }

    private static void live(ServerLevel level, BlockPos home, List<Cirri> folk, long now, long time, long day) {
        // the Evensong: everyone free (but the bellkeeper and the lamplighter, busy at dusk) circles over the court
        if (time >= Cirri.EVENSONG_START && time < Cirri.EVENSONG_END) {
            for (Cirri c : folk) {
                if (c.free() && !c.job().equals("bellkeeper") && !c.job().equals("lamplighter") && c.mode() != Cirri.Mode.EVENSONG) {
                    c.joinEvensong();
                    if (RANDOM.nextInt(3) == 0) Emote.NOTE.show(c, RANDOM.nextInt(30));
                }
            }
        }
        if (level.isThundering() && !Chronicle.reportedToday(level, home, day, "storm")) Chronicle.report(level, home, day, "storm", "", "");
        if (now % 100 == 7) whales(level, home, folk, day);
        if (now % 200 == 7) {
            chats(folk);
            games(folk);
        }
    }

    /** A Cloud Whale passing within sight: two or three fly out to swim beside it and sing (once a day it's news). */
    private static void whales(ServerLevel level, BlockPos home, List<Cirri> folk, long day) {
        var whales = level.getEntitiesOfClass(CloudWhale.class, new AABB(home).inflate(140, 90, 140), CloudWhale::isAlive);
        if (whales.isEmpty()) return;
        CloudWhale whale = whales.getFirst();
        if (folk.stream().anyMatch(c -> c.mode() == Cirri.Mode.ESCORT)) return;
        var keen = new ArrayList<>(folk.stream().filter(c -> c.free() && !c.isBaby()).toList());
        if (keen.isEmpty()) return;
        Collections.shuffle(keen, RANDOM);
        int n = Math.min(keen.size(), 2 + RANDOM.nextInt(2));
        for (int i = 0; i < n; i++) keen.get(i).escort(whale, i, 500 + RANDOM.nextInt(400));
        if (!Chronicle.reportedToday(level, home, day, "whale")) Chronicle.report(level, home, day, "whale", keen.getFirst().firstName(), "");
    }

    /** Neighbours close to each other sometimes stop to chat: a pair at a time, now and then. */
    private static void chats(List<Cirri> folk) {
        var free = new ArrayList<>(folk.stream().filter(Cirri::free).toList());
        Collections.shuffle(free, RANDOM);
        int started = 0;
        for (int i = 0; i < free.size() && started < 2; i++) {
            Cirri a = free.get(i);
            if (a.mode() == Cirri.Mode.CHAT) continue;
            for (int j = i + 1; j < free.size(); j++) {
                Cirri b = free.get(j);
                if (b.mode() == Cirri.Mode.CHAT || a.distanceToSqr(b) > 12 * 12 || a.isBaby() != b.isBaby() && !Kin.family(a, b)) continue;
                if (RANDOM.nextFloat() > 0.45F) break;
                int ticks = 240 + RANDOM.nextInt(240);
                a.chatWith(b, ticks);
                b.chatWith(a, ticks);
                chatter(a, b);
                started++;
                break;
            }
        }
    }

    /** Children at a loose end play tag: one chases, the other flees, and it swaps on a tag. */
    private static void games(List<Cirri> folk) {
        var kids = new ArrayList<>(folk.stream().filter(c -> c.isBaby() && c.free()).toList());
        if (kids.size() < 2 || RANDOM.nextFloat() > 0.5F) return;
        Collections.shuffle(kids, RANDOM);
        int ticks = 400 + RANDOM.nextInt(400);
        kids.get(0).play(kids.get(1), true, ticks);
        kids.get(1).play(kids.get(0), false, ticks);
        Emote.IDEA.show(kids.get(0), 0);
        Emote.EXCLAIM.show(kids.get(1), 6);
    }

    /** One turn of two neighbours' chat: bubbles that say how they feel about each other. */
    public static void chatter(Cirri a, Cirri b) {
        boolean speakerA = RANDOM.nextBoolean();
        Cirri speaker = speakerA ? a : b, listener = speakerA ? b : a;
        int roll = RANDOM.nextInt(100);
        Emote[] pair;
        var village = Kin.village(a);
        if (a.getUUID().equals(b.partner()) || b.getUUID().equals(a.partner())) {
            pair = new Emote[] {Emote.HEART, roll < 50 ? Emote.HEART : Emote.BLUSH};
        } else if (Kin.family(a, b)) {
            pair = new Emote[] {roll < 50 ? Emote.NOTE : Emote.EXCLAIM, roll % 3 == 0 ? Emote.HEART : Emote.NOTE};
        } else if (Kin.friend(a, village) == b || Kin.friend(b, village) == a) {
            pair = new Emote[] {roll < 35 ? Emote.NOTE : roll < 70 ? Emote.IDEA : Emote.EXCLAIM, roll % 2 == 0 ? Emote.NOTE : Emote.SPARKLE};
        } else if (Kin.crush(a, village) == b || Kin.crush(b, village) == a) {
            pair = new Emote[] {Emote.BLUSH, roll < 50 ? Emote.QUESTION : Emote.NOTE};
        } else if (!a.job().isEmpty() && a.job().equals(b.job())) {
            pair = new Emote[] {roll < 50 ? Emote.IDEA : Emote.DOTS, roll < 50 ? Emote.QUESTION : Emote.IDEA};
        } else {
            pair = new Emote[] {roll < 50 ? Emote.DOTS : Emote.IDEA, roll < 33 ? Emote.EXCLAIM : roll < 66 ? Emote.QUESTION : Emote.NOTE};
        }
        pair[0].show(speaker, 0);
        pair[1].show(listener, 26 + RANDOM.nextInt(14));
    }

    /** A Cirri lifting their voice at the Evensong or beside a whale: a hum, notes in the air, a bubble. */
    public static void singOut(Cirri c) {
        if (!(c.level() instanceof ServerLevel level)) return;
        c.playSound(c.isBaby() ? dev.skyfriends.SkySounds.CIRRI_CHILD_HUM : c.female() ? dev.skyfriends.SkySounds.CIRRI_FEMALE_HUM
                : dev.skyfriends.SkySounds.CIRRI_MALE_HUM, 1.2F, c.getVoicePitch());
        level.sendParticles(ParticleTypes.NOTE, c.getX(), c.getEyeY() + 0.5, c.getZ(), 2, 0.4, 0.2, 0.4, 1.0);
        Emote.NOTE.show(c, 0);
    }

    // -- the player in a village ------------------------------------------------------------------

    private static void visit(ServerLevel level, ServerPlayer player, Map<BlockPos, List<Cirri>> villages, long day) {
        if (player.isSpectator()) return;
        UUID id = player.getUUID();
        BlockPos was = VISITING.get(id);
        if (was != null && (player.level() != level || horizontal(player, was) > 140 * 140)) {
            VISITING.remove(id);
            was = null;
        }
        BlockPos here = null;
        double best = 76 * 76;
        for (BlockPos home : villages.keySet()) {
            double d = horizontal(player, home);
            if (d < best && Math.abs(player.getY() - home.getY()) < 60) {
                best = d;
                here = home;
            }
        }
        if (here == null) return;
        List<Cirri> folk = villages.get(here);
        if (!here.equals(was)) {
            VISITING.put(id, here);
            arrive(level, player, here, folk, day);
        }
        greet(player, folk, day);
    }

    private static double horizontal(ServerPlayer p, BlockPos at) {
        double dx = p.getX() - at.getX() - 0.5, dz = p.getZ() - at.getZ() - 0.5;
        return dx * dx + dz * dz;
    }

    /** The village's name on a title card, once a visit, and (once a day) the village notices its guest. */
    private static void arrive(ServerLevel level, ServerPlayer player, BlockPos home, List<Cirri> folk, long day) {
        int grown = (int) folk.stream().filter(c -> !c.isBaby()).count(), young = folk.size() - grown;
        String below = grown + " Cirri" + (young > 0 ? " and " + young + (young == 1 ? " child" : " children") : "") + " live here";
        if (ServerPlayNetworking.canSend(player, ArrivalPayload.TYPE)) {
            ServerPlayNetworking.send(player, new ArrivalPayload(CirriKin.villageName(home), "A sky village of the Cirri", below));
        }
        Chronicle.report(level, home, day, "visitor", player.getName().getString(), "");
    }

    /**
     * The village sees you: a close friend nearby waves you over with a heart (once a day), a friend with fresh
     * news pops an idea bubble, and once a day a close friend who sees you flies over with a little present.
     */
    private static void greet(ServerPlayer player, List<Cirri> folk, long day) {
        boolean brought = false;
        for (Cirri c : folk) {
            if (c.asleep() || !c.isAlive()) continue;
            Bond bond = c.talk().bonds().get(player.getUUID());
            if (bond == null || bond.grudge > 0) continue;
            int level = bond.level();
            double d = c.distanceToSqr(player);
            if (level >= Friendship.PRESENTS && d < 10 * 10 && bond.waved != day) {
                bond.waved = day;
                Emote.HEART.show(c, 4);
            }
            if (!brought && level >= Friendship.PRESENTS && bond.brought != day && d < 22 * 22 && c.free() && c.hasLineOfSight(player)) {
                bond.brought = day;
                c.bring(player);
                brought = true;
            }
        }
    }

    /** A close friend has flown over with a present: they give it, say a word, and it's in your Journal. */
    public static void present(Cirri c, ServerPlayer player) {
        ItemStack gift = presentFor(c);
        // named before it's handed over: giving moves the stack into the inventory and leaves this one empty
        String what = (gift.getCount() > 1 ? gift.getCount() + " " : "") + gift.getHoverName().getString();
        String line = TalkWorld.say(c, player, "gift.bring");
        TalkWorld.give(player, gift);
        player.sendSystemMessage(Component.literal(c.firstName() + " brings you " + what.toLowerCase(java.util.Locale.ROOT)
                + (line == null ? "." : ": \"" + line + "\"")).withStyle(ChatFormatting.LIGHT_PURPLE));
        c.talk().tale(player).remember(c.dayNumber(), c.firstName() + " flew over with a present: " + what + ".");
        Emote.HEART.show(c, 0);
        if (c.level() instanceof ServerLevel level) level.sendParticles(ParticleTypes.HAPPY_VILLAGER, player.getX(), player.getEyeY(), player.getZ(), 6, 0.4, 0.4, 0.4, 0);
    }

    private static ItemStack presentFor(Cirri c) {
        var kinds = c.isBaby()
                ? List.of(new ItemStack(Items.CORNFLOWER), new ItemStack(Items.FEATHER, 2), new ItemStack(SkyItems.SKY_SCALE), new ItemStack(SkyItems.SKY_PEACH))
                : List.of(new ItemStack(SkyItems.SKY_PEACH, 3), new ItemStack(SkyItems.SKY_SCALE), new ItemStack(Items.HONEY_BOTTLE),
                        new ItemStack(Items.GLOW_BERRIES, 4), new ItemStack(Items.AMETHYST_SHARD, 2), new ItemStack(Items.LILY_OF_THE_VALLEY),
                        new ItemStack(Items.FEATHER, 4), new ItemStack(Items.EMERALD));
        return kinds.get(RANDOM.nextInt(kinds.size())).copy();
    }

    /** The village a player is in now, by its home (tests). */
    public static @Nullable BlockPos visiting(ServerPlayer player) {
        return VISITING.get(player.getUUID());
    }
}
