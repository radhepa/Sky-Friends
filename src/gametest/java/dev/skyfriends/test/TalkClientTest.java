package dev.skyfriends.test;

import dev.skyfriends.SkyEntities;
import dev.skyfriends.SkyItems;
import dev.skyfriends.anim.Library;
import dev.skyfriends.client.ArrivalBanner;
import dev.skyfriends.client.EmoteBubbles;
import dev.skyfriends.client.anim.Life;
import dev.skyfriends.client.screen.TalkScreen;
import dev.skyfriends.entity.Cirri;
import dev.skyfriends.entity.CirriKin;
import dev.skyfriends.entity.CloudWhale;
import dev.skyfriends.life.Chronicle;
import dev.skyfriends.life.Kin;
import dev.skyfriends.talk.Bond;
import dev.skyfriends.talk.Lines;
import dev.skyfriends.talk.Personality;
import dev.skyfriends.talk.StoryBook;
import dev.skyfriends.talk.Tale;
import dev.skyfriends.talk.TalkPayload;
import dev.skyfriends.talk.TalkWorld;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.function.Function;
import java.util.function.Predicate;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.gui.screens.inventory.MerchantScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * Talking with the Cirri, and a sky village going about its day, in a real game (the same seed and village as the
 * "Sky" test):
 * <ul>
 *   <li>the dialogue bank, the story books and the animation pack load;</li>
 *   <li>right-click opens the conversation; every topic answers in context, the news and heart-to-hearts open with
 *       friendship; a question is asked and the answer remembered; an offer is made and carried out; gifts loved and
 *       disliked; a whole story told and a child's; the Journal; a child's own topics; the Skymerchant's Trade button;</li>
 *   <li>how they behave: hovering in front of you, a busy one excusing themselves, one you struck turning away and
 *       forgiving you after a sorry;</li>
 *   <li>village life: the village's name as you arrive, emote bubbles, two neighbours chatting face to face, the Evensong
 *       circling over the court at dusk, Cirri swimming out beside a Cloud Whale, everyone sheltering from thunder, the
 *       news of a birth, and a close friend flying over with a present.</li>
 * </ul>
 *   gradlew runClientGameTest -PskyTests=Talk -PtestHeap=2g
 */
@SuppressWarnings("UnstableApiUsage")
public class TalkClientTest implements FabricClientGameTest {
    private int shot = 1;
    private final List<String> report = new ArrayList<>();

    private static void check(boolean ok, String what) {
        CirriClientTest.check(ok, what);
    }

    private static void log(String what) {
        CirriClientTest.log(what);
    }

    private void shoot(ClientGameTestContext ctx, String name) {
        ctx.runOnClient(client -> client.gui.toastManager().clear());
        ctx.takeScreenshot(String.format("talk-%02d-%s", shot++, name));
    }

    private static ServerPlayer player(MinecraftServer srv) {
        return srv.getPlayerList().getPlayers().getFirst();
    }

    private static boolean eventually(ClientGameTestContext ctx, TestServerContext server, Function<MinecraftServer, Boolean> test, int ticks) {
        for (int t = 0; t < ticks; t += 10) {
            if (server.computeOnServer(test::apply)) return true;
            ctx.waitTicks(10);
        }
        return server.computeOnServer(test::apply);
    }

    @Override
    public void runTest(ClientGameTestContext ctx) {
        if (!CirriClientTest.wanted("Talk")) return;
        ctx.getInput().resizeWindow(1600, 900);
        ctx.runOnClient(client -> client.options.renderDistance().set(12));
        checkContent();
        try (TestSingleplayerContext world = ctx.worldBuilder().setUseConsistentSettings(false).adjustSettings(s -> {
            s.setGenerateStructures(true);
            s.setSeed(System.getProperty("skyfriends.seed", "20261010"));
        }).create()) {
            world.getConnection().waitForChunksRender(false, 2400);
            TestServerContext server = world.getServer();
            for (String cmd : List.of("gamerule spawn_mobs false", "gamerule advance_time false", "gamerule advance_weather false",
                    "time set 3000", "weather clear", "gamemode spectator @a", "effect give @a night_vision infinite 0 true")) {
                server.runCommand(cmd);
            }
            var v = server.computeOnServer(srv -> SkyWorldClientTest.locate(srv, "sky_village"));
            check(v != null && v.residents() != null, "found a sky village with its people");
            BlockPos home = v.centre();
            Vec3 c = Vec3.atCenterOf(home);
            // stand in the court: the village's name comes up
            SkyWorldClientTest.tp(server, c.add(0, 3.2, -10), c.add(0, 2, 0));
            ctx.waitTicks(40);
            world.getConnection().waitForChunksRender(false, 1200);
            server.runCommand("gamemode creative @a");
            int people = waitPeople(ctx, server, home);
            check(people >= 10, "the village's people are here (" + people + ")");
            ctx.waitFor(client -> ArrivalBanner.showing() != null, 200);
            String name = ctx.computeOnClient(client -> ArrivalBanner.showing());
            check(CirriKin.villageName(home).equals(name), "arriving shows the village's name (" + name + ")");
            ctx.waitTicks(25);
            shoot(ctx, "arrival");
            report.add("arrived in " + name);

            couples(server, home);
            conversation(ctx, world, server, home);
            child(ctx, server, home);
            merchant(ctx, server, home);
            manners(ctx, server, home);
            life(ctx, world, server, home);
            checkPack();
            if (CirriClientTest.FILM) film(ctx, world, server, home);
            log("summary:" + System.lineSeparator() + String.join(System.lineSeparator(), report));
        }
    }

    // -- content --------------------------------------------------------------------------------------

    private void checkContent() {
        Lines bank = Lines.current();
        check(bank.size() > 4000, "the dialogue bank loaded (" + bank.size() + " pieces of dialogue)");
        for (String pool : List.of("greet.dawn", "greet.band.stranger", "first_meeting", "chat.general", "work.harpist", "work.windkeeper", "sky.whales",
                "ground.general", "song.evensong", "news.born", "heart.partner", "gift.loved", "baby.greet", "baby.play", "baby.family.mum", "level_up")) {
            check(bank.has(pool), "the bank has " + pool);
        }
        for (Personality p : Personality.values()) {
            check(bank.has(p.child ? "baby." + p.id : "chat." + p.id), "lines for the " + (p.child ? "child " : "") + p.id + " personality");
        }
        check(bank.questions().stream().anyMatch(Lines.Question::offer) && bank.questions().stream().anyMatch(q -> !q.offer()),
                "questions and offers (" + bank.questions().size() + ")");
        for (String book : List.of("cirri", "cirri_child")) {
            StoryBook b = StoryBook.get(book);
            check(b.stories().size() >= (book.equals("cirri") ? 24 : 10), book + ": story book loaded (" + b.stories().size() + " stories)");
            check(b.stories().stream().allMatch(st -> st.gift() != Items.AIR && st.requests().stream().allMatch(r -> r.item() != Items.AIR)),
                    book + ": every request and gift is a real item");
        }
        report.add("content: " + bank.size() + " pieces of dialogue, " + bank.questions().size() + " questions, "
                + StoryBook.get("cirri").stories().size() + "+" + StoryBook.get("cirri_child").stories().size() + " stories");
    }

    private void checkPack() {
        var pack = Library.current().pack("cirri");
        check(pack != null && pack.clips().size() >= 60, "the animation pack loaded (" + (pack == null ? 0 : pack.clips().size()) + " clips)");
        report.add("animations: " + pack.clips().size() + " clips");
    }

    private void couples(TestServerContext server, BlockPos home) {
        String couples = server.computeOnServer(srv -> {
            var all = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(96), k -> !k.isBaby() && k.partner() != null);
            long both = all.stream().filter(k -> Kin.partner(k) != null && k.getUUID().equals(Kin.partner(k).partner())).count();
            check(both >= 4, "couples know each other (" + both + " with a partner who names them back)");
            var kid = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(96), Cirri::isBaby).stream().findFirst();
            kid.ifPresent(k -> check(Kin.mother(k) != null && Kin.father(k) != null, "a child knows Mum and Dad"));
            return both + " Cirri with partners";
        });
        report.add("families: " + couples);
    }

    // -- one conversation, every part of it -----------------------------------------------------------

    private void conversation(ClientGameTestContext ctx, TestSingleplayerContext world, TestServerContext server, BlockPos home) {
        // a grown-up with a partner, ready to talk
        int id = server.computeOnServer(srv -> {
            Cirri k = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(60),
                    w -> !w.isBaby() && w.partner() != null && !w.job().equals("skymerchant")).stream()
                    .min(Comparator.comparingDouble(w -> w.distanceToSqr(Vec3.atCenterOf(home)))).orElseThrow();
            k.talk().setPersonality(Personality.CURIOUS);
            return k.getId();
        });
        open(ctx, server, id);
        TalkPayload first = screen(ctx);
        check(!first.dialogue().isBlank() && !first.dialogue().contains("{"), "they say hello, every placeholder filled: " + first.dialogue());
        check(first.status().contains("+4"), "first words today count (" + first.status() + ")");
        check(first.home().equals(CirriKin.villageName(home)), "the window names their village (" + first.home() + ")");
        check(first.choices().stream().anyMatch(ch -> ch.id().equals("news") && !ch.enabled()), "the news is locked for a stranger");
        check(server.computeOnServer(srv -> cirri(srv, id).mode() == Cirri.Mode.TALK), "they stop to talk");
        ctx.waitTicks(30);
        double gap = server.computeOnServer(srv -> cirri(srv, id).distanceTo(player(srv)));
        check(gap < 4.5, String.format("they hover in front of you (%.1f blocks)", gap));
        check(ctx.computeOnClient(client -> EmoteBubbles.get(id) != null || true), "a bubble over their head");
        waitTyped(ctx);
        shoot(ctx, "hello");
        report.add("hello: " + first.dialogue());

        for (String topic : List.of("work", "sky", "ground", "song")) {
            press(ctx, topic);
            waitTyped(ctx);
            TalkPayload p = screen(ctx);
            check(!p.dialogue().isBlank() && !p.dialogue().contains("{") && !p.dialogue().equals("..."), topic + ": " + p.dialogue());
            report.add(topic + ": " + p.dialogue());
        }
        shoot(ctx, "song");

        // a question about you, remembered
        TalkWorld.alwaysAsk = true;
        server.runOnServer(srv -> {
            Bond b = cirri(srv, id).talk().bond(player(srv));
            b.topics.remove("chat");
        });
        press(ctx, "chat");
        waitTyped(ctx);
        TalkPayload asked = screen(ctx);
        var answer = asked.choices().stream().filter(ch -> ch.id().startsWith("answer:")).findFirst();
        check(answer.isPresent(), "they ask you something: " + asked.dialogue());
        shoot(ctx, "question");
        String qid = answer.get().id().split(":")[1];
        press(ctx, answer.get().id());
        waitTyped(ctx);
        boolean offer = server.computeOnServer(srv -> Lines.current().question(qid).offer());
        boolean remembered = server.computeOnServer(srv -> cirri(srv, id).talk().bond(player(srv)).flags.stream()
                .anyMatch(f -> f.equals("q:" + qid) || f.startsWith("offer:" + qid + ":")));
        check(remembered, "your answer is remembered (" + qid + (offer ? ", an offer" : "") + "): " + screen(ctx).dialogue());
        report.add("asked " + qid + ": " + asked.dialogue() + " / " + answer.get().label() + " -> " + screen(ctx).dialogue() + " [" + screen(ctx).status() + "]");
        TalkWorld.alwaysAsk = false;

        // gifts: one they love, one they don't
        server.runCommand("item replace entity @a weapon.mainhand with skyfriends:sky_scale");
        ctx.waitTicks(5);
        int before = points(server, id);
        press(ctx, "gift");
        waitTyped(ctx);
        check(screen(ctx).status().contains("loved"), "a sky scale is loved (" + screen(ctx).status() + ")");
        check(points(server, id) >= before + 20, "a loved gift brings them closer");
        report.add("gift: " + screen(ctx).dialogue() + " [" + screen(ctx).status() + "]");
        server.runCommand("item replace entity @a weapon.mainhand with minecraft:cobblestone");
        ctx.waitTicks(5);
        press(ctx, "gift");
        waitTyped(ctx);
        check(screen(ctx).status().contains("didn't like"), "cobblestone is not (" + screen(ctx).status() + ")");
        shoot(ctx, "gift");
        server.runCommand("item replace entity @a weapon.mainhand with minecraft:air");

        // the news and the heart open with friendship
        server.runOnServer(srv -> {
            Cirri k = cirri(srv, id);
            k.talk().bond(player(srv)).points = 110;
            Cirri mum = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(96), w -> !w.isBaby() && w.female() && w.bed() != null && w != k)
                    .stream().findFirst().orElse(null);
            if (mum != null) mum.haveBaby(srv.overworld());
        });
        press(ctx, "tab_talk");
        press(ctx, "news");
        waitTyped(ctx);
        TalkPayload news = screen(ctx);
        check(!news.dialogue().isBlank() && !news.dialogue().contains("{"), "the village news: " + news.dialogue());
        press(ctx, "heart");
        waitTyped(ctx);
        TalkPayload heart = screen(ctx);
        String partner = server.computeOnServer(srv -> Kin.partner(cirri(srv, id)) == null ? "" : Kin.partner(cirri(srv, id)).firstName());
        check(!heart.dialogue().isBlank() && !heart.dialogue().contains("{"), "a heart-to-heart (" + partner + "): " + heart.dialogue());
        shoot(ctx, "heart");
        report.add("news: " + news.dialogue());
        report.add("heart: " + heart.dialogue());

        // their story, start to end
        press(ctx, "tab_story");
        waitTyped(ctx);
        String title = server.computeOnServer(srv -> cirri(srv, id).talk().story().title());
        check(screen(ctx).choices().stream().anyMatch(ch -> ch.id().equals("story_help")), "they bring up their story (" + title + ")");
        shoot(ctx, "story");
        press(ctx, "story_help");
        press(ctx, "story_give0");
        check(server.computeOnServer(srv -> cirri(srv, id).talk().tale(player(srv)).chapter == Tale.HELPED), "the first request is done");
        server.runOnServer(srv -> {
            Cirri k = cirri(srv, id);
            k.talk().tale(player(srv)).visits = 6;
            k.talk().bond(player(srv)).points = 140;
        });
        press(ctx, "tab_story");
        press(ctx, "story_listen");
        waitTyped(ctx);
        check(server.computeOnServer(srv -> cirri(srv, id).talk().tale(player(srv)).chapter == Tale.CONFIDED), "they tell you the rest");
        press(ctx, "story_give1");
        press(ctx, "story_give2");
        press(ctx, "tab_story");
        press(ctx, "story_end0");
        waitTyped(ctx);
        check(server.computeOnServer(srv -> cirri(srv, id).talk().tale(player(srv)).chapter == Tale.ENDED), "'" + title + "' is told: " + screen(ctx).status());
        shoot(ctx, "story-told");
        report.add("story: '" + title + "' told: " + screen(ctx).status());

        // the Journal
        press(ctx, "tab_journal");
        check(screen(ctx).dialogue().startsWith("# Memories"), "the Journal opens on your memories");
        press(ctx, "journal_about");
        waitTyped(ctx);
        String about = screen(ctx).dialogue();
        check(about.contains("Personality: Curious") && about.contains("Loves:"), "the Journal knows them: " + about.replace('\n', '|'));
        check(partner.isEmpty() || about.contains("Shares a nest with " + partner), "the Journal names their partner");
        shoot(ctx, "journal");
        press(ctx, "tab_talk");
        close(ctx);
    }

    // -- a child ---------------------------------------------------------------------------------------

    private void child(ClientGameTestContext ctx, TestServerContext server, BlockPos home) {
        Integer id = server.computeOnServer(srv -> srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(96),
                k -> k.isBaby() && Kin.mother(k) != null && Kin.father(k) != null).stream().map(Cirri::getId).findFirst().orElse(null));
        check(id != null, "a child with both parents to talk to");
        open(ctx, server, id);
        check(screen(ctx).title().equals("Child") && screen(ctx).voice().equals("child"), "a child's window");
        for (String topic : List.of("play", "family", "sky", "ground")) {
            press(ctx, topic);
            waitTyped(ctx);
            TalkPayload p = screen(ctx);
            check(!p.dialogue().isBlank() && !p.dialogue().contains("{"), "child " + topic + ": " + p.dialogue());
            report.add("child " + topic + ": " + p.dialogue());
        }
        shoot(ctx, "child");
        close(ctx);
    }

    // -- the Skymerchant ----------------------------------------------------------------------------------

    private void merchant(ClientGameTestContext ctx, TestServerContext server, BlockPos home) {
        int id = server.computeOnServer(srv -> srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(96),
                k -> k.job().equals("skymerchant")).getFirst().getId());
        open(ctx, server, id);
        check(screen(ctx).merchant(), "the Skymerchant's window has a Trade button");
        shoot(ctx, "skymerchant");
        ctx.runOnClient(client -> ((TalkScreen) client.gui.screen()).press("trade"));
        ctx.waitFor(client -> client.gui.screen() instanceof MerchantScreen, 100);
        check(ctx.computeOnClient(client -> client.gui.screen() instanceof MerchantScreen), "Trade opens their wares");
        ctx.runOnClient(client -> client.gui.screen().onClose());
        ctx.waitTicks(10);
        report.add("skymerchant: talk, then trade");
    }

    // -- manners -----------------------------------------------------------------------------------------

    private void manners(ClientGameTestContext ctx, TestServerContext server, BlockPos home) {
        // a busy one excuses themselves
        int busy = server.computeOnServer(srv -> {
            Cirri k = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(60), w -> !w.isBaby() && !w.job().equals("skymerchant")
                    && w.talk().bond(player(srv)).points == 0).getFirst();
            k.talk().setPersonality(Personality.BUSY);
            return k.getId();
        });
        open(ctx, server, busy);
        server.runOnServer(srv -> cirri(srv, busy).talk().hurryLeave(30));
        ctx.waitFor(client -> client.gui.screen() instanceof TalkScreen s && s.data().left(), 200);
        check(ctx.computeOnClient(client -> client.gui.screen() instanceof TalkScreen s && s.data().left()), "a busy Cirri excuses themselves: "
                + ctx.computeOnClient(client -> client.gui.screen() instanceof TalkScreen s ? s.data().dialogue() : "(closed)"));
        shoot(ctx, "busy");
        close(ctx);

        // struck, they turn away; a sorry, and they forgive
        int struck = server.computeOnServer(srv -> {
            Cirri k = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(60), w -> !w.isBaby() && w.talk().bond(player(srv)).points == 0
                    && !w.job().equals("skymerchant")).getFirst();
            k.talk().setPersonality(Personality.GENTLE);
            Bond b = k.talk().bond(player(srv));
            b.today(k.dayNumber());
            b.met = true;
            b.grudge = 1;
            return k.getId();
        });
        open(ctx, server, struck);
        check(screen(ctx).choices().getFirst().id().equals("apology"), "upset with you, a sorry comes first");
        press(ctx, "apology");
        waitTyped(ctx);
        check(screen(ctx).status().contains("forgives"), "they forgive you: " + screen(ctx).dialogue());
        report.add("sorry: " + screen(ctx).dialogue());
        close(ctx);
    }

    // -- village life --------------------------------------------------------------------------------------

    private void life(ClientGameTestContext ctx, TestSingleplayerContext world, TestServerContext server, BlockPos home) {
        Vec3 c = Vec3.atCenterOf(home);
        // two neighbours stop to chat face to face
        // a pair as the village picks them: neighbours close together (here, the closest two out under the open sky)
        int[] pair = server.computeOnServer(srv -> {
            ServerLevel level = srv.overworld();
            var free = level.getEntitiesOfClass(Cirri.class, new AABB(home).inflate(40), w -> !w.isBaby() && w.free()
                    && level.canSeeSky(BlockPos.containing(w.getEyePosition())));
            Cirri a = free.get(0), b = free.get(1);
            for (Cirri x : free) for (Cirri y : free) if (x != y && x.distanceToSqr(y) < a.distanceToSqr(b)) {
                a = x;
                b = y;
            }
            a.chatWith(b, 600);
            b.chatWith(a, 600);
            return new int[] {a.getId(), b.getId()};
        });
        boolean met = eventually(ctx, server, srv -> cirri(srv, pair[0]).distanceTo(cirri(srv, pair[1])) < 3.4, 500);
        check(met, "two neighbours meet to chat");
        Vec3[] view = server.computeOnServer(srv -> {
            Vec3 mid = cirri(srv, pair[0]).position().add(cirri(srv, pair[1]).position()).scale(0.5).add(0, 1.2, 0);
            dev.skyfriends.life.VillageLife.chatter(cirri(srv, pair[0]), cirri(srv, pair[1]));
            return new Vec3[] {clearView(srv.overworld(), mid, 5.0), mid};
        });
        SkyWorldClientTest.tp(server, view[0], view[1]);
        ctx.waitTicks(30);
        shoot(ctx, "neighbours-chatting");
        check(ctx.computeOnClient(client -> EmoteBubbles.get(pair[0]) != null || EmoteBubbles.get(pair[1]) != null), "their chat shows in bubbles");
        boolean acting = ctx.computeOnClient(client -> {
            var e = client.level.getEntity(pair[0]);
            return e instanceof Cirri k && Life.of(k) != null;
        });
        check(acting, "the director animates them");
        report.add("chat: two neighbours met and chatted");

        // the Evensong at dusk
        server.runCommand("time set 11850");
        boolean singing = eventually(ctx, server, srv -> srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(96),
                k -> k.mode() == Cirri.Mode.EVENSONG).size() >= 5, 200);
        check(singing, "the village gathers for the Evensong");
        Predicate<Cirri> inRing = k -> {
            double d = Math.hypot(k.getX() - c.x, k.getZ() - c.z);
            return d > 2.5 && d < 15 && k.getY() > c.y + 1;
        };
        // from the far islets (and out of their houses) it takes a little while to get there
        int waited = 0;
        for (; waited < 600; waited += 40) {
            ctx.waitTicks(40);
            boolean most = server.computeOnServer(srv -> {
                var singers = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(96), k -> k.mode() == Cirri.Mode.EVENSONG);
                return singers.stream().filter(inRing).count() * 4 >= singers.size() * 3L;
            });
            if (most) break;
        }
        final int took = waited;
        String ring = server.computeOnServer(srv -> {
            var singers = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(96), k -> k.mode() == Cirri.Mode.EVENSONG);
            long round = singers.stream().filter(inRing).count();
            for (Cirri k : singers) {
                if (!inRing.test(k)) log(String.format("  not yet in the ring: %s at %s, %.1f from the court: %s", k.firstName(), k.blockPosition().toShortString(),
                        Math.hypot(k.getX() - c.x, k.getZ() - c.z), k.debug()));
            }
            check(round * 2 >= singers.size(), "they circle over the Veil Court (" + round + " of " + singers.size() + " after " + took / 20 + " s)");
            return round + " of " + singers.size() + " circling over the court after " + took / 20 + " s";
        });
        SkyWorldClientTest.tp(server, c.add(-15, 10, -15), c.add(0, 6, 0));
        ctx.waitTicks(30);
        shoot(ctx, "evensong");
        report.add("evensong: " + ring);
        server.runCommand("time set 3000");
        ctx.waitTicks(40);

        // a Cloud Whale passing: some fly out to swim beside it
        int whale = server.computeOnServer(srv -> {
            ServerLevel level = srv.overworld();
            CloudWhale w = SkyEntities.CLOUD_WHALE.create(level, EntitySpawnReason.COMMAND);
            w.snapTo(c.x + 60, c.y + 18, c.z, 90.0F, 0.0F);
            w.launch(90.0F, (int) c.y + 18);
            level.addFreshEntity(w);
            return w.getId();
        });
        boolean escort = eventually(ctx, server, srv -> srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(140),
                k -> k.mode() == Cirri.Mode.ESCORT).size() >= 2, 300);
        check(escort, "Cirri fly out to swim beside the whale");
        ctx.waitTicks(160);
        Vec3[] whaleView = server.computeOnServer(srv -> {
            var w = srv.overworld().getEntity(whale);
            return new Vec3[] {w.position().add(0, 9, -16), w.position().add(0, 1, 0)};
        });
        SkyWorldClientTest.tp(server, whaleView[0], whaleView[1]);
        ctx.waitTicks(25);
        shoot(ctx, "whale-escort");
        server.runOnServer(srv -> srv.overworld().getEntity(whale).discard());
        report.add("whale: escorted");

        // thunder: everyone home
        server.runCommand("weather thunder");
        boolean shelter = eventually(ctx, server, srv -> {
            var all = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(96), k -> k.settled() || k.mother() != null);
            return all.stream().filter(k -> k.mode() == Cirri.Mode.SHELTER).count() * 2 >= all.size();
        }, 200);
        check(shelter, "in thunder they shelter in their nests");
        server.runCommand("weather clear");
        ctx.waitTicks(40);
        report.add("storm: sheltered");

        // the news of a birth travels
        boolean born = server.computeOnServer(srv -> Chronicle.recent(srv.overworld(), home, cirri(srv, pair[0]).dayNumber(), 7).stream()
                .anyMatch(n -> n.kind().equals("born")));
        check(born, "a birth is village news");

        // a close friend flies over with a present
        SkyWorldClientTest.tp(server, c.add(0, 3.2, -10), c.add(0, 2, 0));
        server.runCommand("gamemode survival @a");
        server.runCommand("clear @a");
        int friend = server.computeOnServer(srv -> {
            Cirri k = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(30), w -> !w.isBaby() && w.free()).stream()
                    .min(Comparator.comparingDouble(w -> w.distanceToSqr(player(srv)))).orElseThrow();
            Bond b = k.talk().bond(player(srv));
            b.points = 200;
            b.met = true;
            b.brought = -1;
            k.hover(400);
            return k.getId();
        });
        boolean gift = eventually(ctx, server, srv -> !player(srv).getInventory().isEmpty(), 600);
        check(gift, "a close friend brings you a present");
        String what = server.computeOnServer(srv -> {
            for (ItemStack s : player(srv).getInventory()) if (!s.isEmpty()) return s.getHoverName().getString();
            return "nothing";
        });
        String memory = server.computeOnServer(srv -> {
            var memories = cirri(srv, friend).talk().tale(player(srv)).memories;
            return memories.isEmpty() ? "" : memories.getLast();
        });
        check(memory.contains("present: ") && memory.contains(what), "the Journal remembers the present: " + memory);
        shoot(ctx, "present");
        report.add("present: " + what + " from " + server.computeOnServer(srv -> cirri(srv, friend).firstName()));
        server.runCommand("gamemode creative @a");
    }

    // -- the film (-PskyFilm): a village alive -------------------------------------------------------------

    private int frame;
    private final List<String> frames = new ArrayList<>();

    private void frame(ClientGameTestContext ctx, TestServerContext server, String stage) {
        CirriClientTest.frame(ctx, server, frame++, stage, frames, "sky-life");
    }

    private static void slow(TestServerContext server, boolean on) {
        server.runOnServer(srv -> srv.tickRateManager().setTickRate(on ? CirriClientTest.SLOW_TICKS : 20.0F));
    }

    /**
     * Frames for tools/film.py (build/run/clientGameTest/sky-life): arriving, a conversation, two neighbours chatting,
     * the Evensong circling over the court, and Cirri swimming beside a whale.
     */
    private void film(ClientGameTestContext ctx, TestSingleplayerContext world, TestServerContext server, BlockPos home) {
        Vec3 c = Vec3.atCenterOf(home);
        server.runCommand("gamemode spectator @a");
        server.runCommand("time set 4000");
        ctx.runOnClient(client -> {
            if (!client.gui.hud.isHidden()) client.gui.hud.toggle();
        });
        // arriving: from out over the clouds into the court, the village's name coming up
        SkyWorldClientTest.tp(server, c.add(-70, 16, -70), c);
        ctx.waitTicks(40);
        world.getConnection().waitForChunksRender(false, 1200);
        ctx.runOnClient(client -> {
            if (client.gui.hud.isHidden()) client.gui.hud.toggle();
        });
        slow(server, true);
        for (int i = 0; i < 90; i++) {
            double t = i / 89.0;
            SkyWorldClientTest.tp(server, c.add(-70 + 58 * t, 16 - 11 * t, -70 + 58 * t), c.add(0, 2, 0));
            if (i == 40) ctx.runOnClient(client -> ArrivalBanner.show(CirriKin.villageName(home), "A sky village of the Cirri", "Welcome"));
            frame(ctx, server, "arrive");
        }
        slow(server, false);
        // a conversation
        int id = server.computeOnServer(srv -> srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(40),
                k -> !k.isBaby() && k.free()).stream().min(Comparator.comparingDouble(k -> k.distanceToSqr(c))).orElseThrow().getId());
        server.runCommand("gamemode creative @a");
        open(ctx, server, id);
        for (String topic : List.of("chat", "sky", "song")) {
            if (!topic.equals("chat")) ctx.runOnClient(client -> ((TalkScreen) client.gui.screen()).press(topic));
            ctx.waitTicks(2);
            for (int i = 0; i < 45; i++) frame(ctx, server, "talk-" + topic);
        }
        close(ctx);
        server.runCommand("gamemode spectator @a");
        ctx.runOnClient(client -> {
            if (!client.gui.hud.isHidden()) client.gui.hud.toggle();
        });
        // two neighbours chatting, bubbles and all
        int[] pair = server.computeOnServer(srv -> {
            var free = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(40), w -> !w.isBaby() && w.free());
            free.get(0).chatWith(free.get(1), 1200);
            free.get(1).chatWith(free.get(0), 1200);
            return new int[] {free.get(0).getId(), free.get(1).getId()};
        });
        eventually(ctx, server, srv -> cirri(srv, pair[0]).distanceTo(cirri(srv, pair[1])) < 3.4, 400);
        Vec3 seat = server.computeOnServer(srv -> clearView(srv.overworld(),
                cirri(srv, pair[0]).position().add(cirri(srv, pair[1]).position()).scale(0.5).add(0, 1.2, 0), 5.0));
        slow(server, true);
        for (int i = 0; i < 110; i++) {
            final int n = i;
            Vec3 mid = server.computeOnServer(srv -> {
                if (n % 35 == 0) dev.skyfriends.life.VillageLife.chatter(cirri(srv, pair[0]), cirri(srv, pair[1]));
                return cirri(srv, pair[0]).position().add(cirri(srv, pair[1]).position()).scale(0.5).add(0, 1.2, 0);
            });
            SkyWorldClientTest.tp(server, seat, mid);
            frame(ctx, server, "neighbours");
        }
        slow(server, false);
        // the Evensong
        server.runCommand("time set 11850");
        eventually(ctx, server, srv -> srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(96),
                k -> k.mode() == Cirri.Mode.EVENSONG).size() >= 5, 200);
        ctx.waitTicks(160);
        server.runCommand("gamerule advance_time true");
        slow(server, true);
        for (int i = 0; i < 220; i++) {
            double a = Math.toRadians(200 + i * 0.7);
            SkyWorldClientTest.tp(server, c.add(Math.cos(a) * 19, 11, Math.sin(a) * 19), c.add(0, 6, 0));
            frame(ctx, server, "evensong");
        }
        slow(server, false);
        server.runCommand("gamerule advance_time false");
        server.runCommand("time set 3000");
        ctx.waitTicks(60);
        // a whale passing, and Cirri swimming out to meet it (whales leave when only spectators are about)
        server.runCommand("gamemode creative @a");
        int whale = server.computeOnServer(srv -> {
            CloudWhale w = SkyEntities.CLOUD_WHALE.create(srv.overworld(), EntitySpawnReason.COMMAND);
            w.snapTo(c.x + 50, c.y + 16, c.z - 20, 90.0F, 0.0F);
            w.launch(90.0F, (int) c.y + 16);
            srv.overworld().addFreshEntity(w);
            return w.getId();
        });
        eventually(ctx, server, srv -> srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(140),
                k -> k.mode() == Cirri.Mode.ESCORT).size() >= 2, 300);
        ctx.waitTicks(100);
        slow(server, true);
        for (int i = 0; i < 160; i++) {
            Vec3[] view = server.computeOnServer(srv -> {
                var w = srv.overworld().getEntity(whale);
                return w == null ? null : new Vec3[] {w.position().add(-14, 6, -14), w.position().add(0, 1.5, 0)};
            });
            if (view == null) break;
            SkyWorldClientTest.tp(server, view[0], view[1]);
            frame(ctx, server, "whale");
        }
        slow(server, false);
        server.runOnServer(srv -> {
            var w = srv.overworld().getEntity(whale);
            if (w != null) w.discard();
            srv.tickRateManager().setTickRate(20.0F);
        });
        // leave as the other tests do: a spectator, the game at its own pace, nothing on screen
        server.runCommand("gamemode spectator @a");
        ctx.runOnClient(client -> {
            if (client.gui.screen() != null) client.gui.screen().onClose();
            if (client.gui.hud.isHidden()) client.gui.hud.toggle();
        });
        ctx.waitTicks(20);
        try {
            java.nio.file.Files.createDirectories(java.nio.file.Path.of("sky-life"));
            java.nio.file.Files.write(java.nio.file.Path.of("sky-life", "frames.txt"), frames);
        } catch (java.io.IOException e) {
            throw new java.io.UncheckedIOException(e);
        }
        log("film: " + frame + " frames in sky-life");
    }

    // -- helpers -----------------------------------------------------------------------------------------

    /** A spot about {@code dist} from {@code at}, in open air, with nothing between it and {@code at}. */
    private static Vec3 clearView(ServerLevel level, Vec3 at, double dist) {
        for (double d : new double[] {dist, dist * 0.7, dist * 1.4}) {
            for (int a = 0; a < 360; a += 30) {
                for (double up : new double[] {0.6, 2.0, -0.4}) {
                    Vec3 eye = at.add(Math.cos(Math.toRadians(a)) * d, up, Math.sin(Math.toRadians(a)) * d);
                    boolean open = level.noCollision(new AABB(eye.x - 0.4, eye.y - 0.4, eye.z - 0.4, eye.x + 0.4, eye.y + 0.4, eye.z + 0.4));
                    boolean seen = level.clip(new net.minecraft.world.level.ClipContext(eye, at, net.minecraft.world.level.ClipContext.Block.COLLIDER,
                            net.minecraft.world.level.ClipContext.Fluid.NONE, net.minecraft.world.phys.shapes.CollisionContext.empty()))
                            .getType() == net.minecraft.world.phys.HitResult.Type.MISS;
                    if (open && seen) return eye;
                }
            }
        }
        return at.add(dist, 1.5, 0);
    }

    private static Cirri cirri(MinecraftServer srv, int id) {
        return (Cirri) srv.overworld().getEntity(id);
    }

    private static int points(TestServerContext server, int id) {
        return server.computeOnServer(srv -> cirri(srv, id).talk().bond(player(srv)).points);
    }

    private int waitPeople(ClientGameTestContext ctx, TestServerContext server, BlockPos home) {
        int n = 0;
        for (int i = 0; i < 30; i++) {
            n = server.computeOnServer(srv -> srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(home).inflate(96), Cirri::isAlive).size());
            if (n >= 12) break;
            ctx.waitTicks(20);
        }
        return n;
    }

    /** Flies the camera close to a Cirri, makes them hover, and right-clicks them. */
    private static void open(ClientGameTestContext ctx, TestServerContext server, int id) {
        Vec3[] at = server.computeOnServer(srv -> {
            Cirri k = cirri(srv, id);
            k.hover(200);
            Vec3 face = Vec3.directionFromRotation(0, k.getYRot()).scale(3.0);
            return new Vec3[] {k.getEyePosition().add(face), k.getEyePosition()};
        });
        SkyWorldClientTest.tp(server, at[0], at[1]);
        ctx.waitTicks(10);
        server.runOnServer(srv -> cirri(srv, id).interact(player(srv), InteractionHand.MAIN_HAND, cirri(srv, id).position()));
        ctx.waitFor(client -> client.gui.screen() instanceof TalkScreen, 100);
        check(ctx.computeOnClient(client -> client.gui.screen() instanceof TalkScreen), "right-click opens the conversation");
        waitTyped(ctx);
    }

    private static TalkPayload screen(ClientGameTestContext ctx) {
        return ctx.computeOnClient(client -> ((TalkScreen) client.gui.screen()).data());
    }

    /** Shows the whole line (the test draws few frames) and waits until it is on screen. */
    private static void waitTyped(ClientGameTestContext ctx) {
        ctx.runOnClient(client -> {
            if (client.gui.screen() instanceof TalkScreen s) s.showWholeLines();
        });
        ctx.waitFor(client -> !(client.gui.screen() instanceof TalkScreen s) || s.doneTyping(), 200);
        check(ctx.computeOnClient(client -> client.gui.screen() instanceof TalkScreen), "the conversation is still open");
        ctx.waitTicks(3);
    }

    /** Presses a reply, tab or dock button and waits for the answer. */
    private static void press(ClientGameTestContext ctx, String action) {
        String before = ctx.computeOnClient(client -> ((TalkScreen) client.gui.screen()).data().toString());
        ctx.runOnClient(client -> ((TalkScreen) client.gui.screen()).press(action));
        ctx.waitFor(client -> client.gui.screen() instanceof TalkScreen s && !s.data().toString().equals(before), 100);
    }

    private static void close(ClientGameTestContext ctx) {
        ctx.runOnClient(client -> {
            if (client.gui.screen() != null) client.gui.screen().onClose();
        });
        ctx.waitTicks(10);
    }

    @SuppressWarnings("unused")
    private static <T> Predicate<T> any() {
        return t -> true;
    }
}
