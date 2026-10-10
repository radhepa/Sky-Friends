package dev.skyfriends.test;

import dev.skyfriends.SkyEntities;
import dev.skyfriends.client.model.CirriModel;
import dev.skyfriends.client.model.Geometry;
import dev.skyfriends.client.render.CirriRenderer;
import dev.skyfriends.entity.Cirri;
import dev.skyfriends.face.LivingFace;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Random;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.fabricmc.fabric.api.client.gametest.v1.screenshot.TestScreenshotOptions;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The Cirri in a real game, over real terrain:
 * <ul>
 *   <li>four of them frozen in a row, one of each face (Starlit and Soft Glint eyes, feminine and not),
 *       photographed close up; the living-eye planes are on the baked model;</li>
 *   <li>one soaring free for 30 seconds: it never lands, keeps clear of the ground, covers distance,
 *       stays near home, and the client poses it stretched out at cruise; photographed beside it;</li>
 *   <li>told to hover: it stops and the client poses it upright;</li>
 *   <li>right-clicked by a player: it hovers a few blocks off, facing them;</li>
 *   <li>hit: it flees up and away;</li>
 *   <li>a flock of six soaring together, photographed from afar.</li>
 * </ul>
 * With -PskyFilm it also films one in flight and hovering, frame by frame (tools/film.py makes the film).
 *   gradlew runClientGameTest -PskyTests=Cirri -PtestHeap=2g [-PskyFilm] [-PcompatMods=<the modpack's mods folder>]
 */
@SuppressWarnings("UnstableApiUsage")
public class CirriClientTest implements FabricClientGameTest {
    static final boolean FILM = Boolean.getBoolean("skyfriends.film");
    /** The game's speed while filming (normal is 20), so the frames come about a tick apart. */
    static final float SLOW_TICKS = 4.0F;

    private int shot = 1;

    static void check(boolean ok, String what) {
        if (!ok) throw new AssertionError(what);
        System.out.println("[skyfriends test] ok: " + what);
    }

    static void log(String what) {
        System.out.println("[skyfriends test] " + what);
    }

    static boolean wanted(String name) {
        String only = System.getProperty("skyfriends.tests");
        return only == null || only.isBlank() || List.of(only.split(",")).contains(name);
    }

    private void shoot(ClientGameTestContext ctx, String name) {
        ctx.runOnClient(client -> client.gui.toastManager().clear());
        ctx.takeScreenshot(String.format("cirri-%02d-%s", shot++, name));
    }

    /** Puts the camera's eye at {@code eye}, looking at {@code look} (tp places the feet, and its facing aims from the feet). */
    static void tp(TestServerContext server, Vec3 eye, Vec3 look) {
        double e = 1.62;
        server.runCommand(String.format("tp @a %.2f %.2f %.2f facing %.2f %.2f %.2f", eye.x, eye.y - e, eye.z, look.x, look.y - e, look.z));
    }

    private static ServerPlayer player(MinecraftServer srv) {
        return srv.getPlayerList().getPlayers().getFirst();
    }

    private static Cirri cirri(MinecraftServer srv, int id) {
        return (Cirri) srv.overworld().getEntity(id);
    }

    private static Cirri spawn(ServerLevel level, Vec3 at, float yaw, boolean noAi, UUID id) {
        Cirri c = SkyEntities.CIRRI.create(level, EntitySpawnReason.COMMAND);
        if (id != null) c.setUUID(id);
        c.snapTo(at.x, at.y, at.z, yaw, 0.0F);
        c.setYHeadRot(yaw);
        c.setYBodyRot(yaw);
        c.setNoAi(noAi);
        level.addFreshEntity(c);
        return c;
    }

    @Override
    public void runTest(ClientGameTestContext ctx) {
        if (!wanted("Cirri")) return;
        ctx.getInput().resizeWindow(1600, 900);
        try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
            world.getConnection().waitForChunksRender(false, 2400);
            TestServerContext server = world.getServer();
            for (String cmd : List.of("gamerule spawn_mobs false", "gamerule advance_time false", "gamerule advance_weather false",
                    "time set 5000", "weather clear", "gamemode spectator @a")) {
                server.runCommand(cmd);
            }
            ctx.runOnClient(client -> {
                if (!client.gui.hud.isHidden()) client.gui.hud.toggle();
            });
            BlockPos centre = server.computeOnServer(srv -> {
                BlockPos p = player(srv).blockPosition();
                return new BlockPos(p.getX(), srv.overworld().getHeight(Heightmap.Types.MOTION_BLOCKING, p.getX(), p.getZ()), p.getZ());
            });
            log("test spot " + centre.toShortString());
            Vec3 c = Vec3.atBottomCenterOf(centre);

            portraits(ctx, world, server, c);
            List<String> report = new ArrayList<>();
            soaring(ctx, world, server, c, report);
            flock(ctx, world, server, c, report);
            log("summary:" + System.lineSeparator() + String.join(System.lineSeparator(), report));
        }
    }

    // -- the faces ----------------------------------------------------------------------------------

    /** Four UUIDs: Starlit feminine, Starlit, Soft Glint feminine, Soft Glint. */
    static List<UUID> faces() {
        Random r = new Random(20261010);
        UUID[] picked = new UUID[4];
        while (picked[0] == null || picked[1] == null || picked[2] == null || picked[3] == null) {
            UUID id = new UUID(r.nextLong(), r.nextLong());
            int seed = LivingFace.seed(id);
            int slot = (LivingFace.eyeStyle(seed) == LivingFace.EyeStyle.STARLIT ? 0 : 2) + (LivingFace.feminine(seed) ? 0 : 1);
            if (picked[slot] == null) picked[slot] = id;
        }
        return List.of(picked);
    }

    private void portraits(ClientGameTestContext ctx, TestSingleplayerContext world, TestServerContext server, Vec3 c) {
        Vec3 row = c.add(0, 8, 0);
        List<UUID> ids = faces();
        List<Integer> spawned = server.computeOnServer(srv -> {
            List<Integer> out = new ArrayList<>();
            for (int i = 0; i < 4; i++) out.add(spawn(srv.overworld(), row.add((i - 1.5) * 1.3, 0, 0), 180.0F, true, ids.get(i)).getId());
            return out;
        });
        // they face north (toward -z); the camera stands north of them
        tp(server, row.add(0, 1.6, -3.8), row.add(0, 1.25, 0));
        ctx.waitTicks(30);
        world.getConnection().waitForChunksRender(false, 600);
        ctx.waitFor(client -> spawned.stream().allMatch(id -> client.level.getEntity(id) instanceof Cirri), 200);
        ctx.runOnClient(client -> {
            Cirri one = (Cirri) client.level.getEntity(spawned.getFirst());
            var renderer = client.getEntityRenderDispatcher().getRenderer(one);
            check(renderer instanceof CirriRenderer, "the Cirri has its own renderer");
            CirriModel model = ((CirriRenderer) renderer).getModel();
            ModelPart head = Geometry.part(model.root(), "cirri", "head");
            for (String part : List.of("eye0", "eye1", "brow0", "brow1", "blush0", "mouth", "lips")) {
                check(head.hasChild(part), "the head has the living-eye plane " + part);
            }
            check(head.getChild("eye0").hasChild("iris") && head.getChild("eye0").hasChild("lash") && head.getChild("eye0").hasChild("lid"),
                    "each eye has an iris, a lash line and a lid");
            Set<String> seen = new java.util.TreeSet<>();
            for (int id : spawned) {
                int seed = LivingFace.seed(client.level.getEntity(id).getUUID());
                seen.add(LivingFace.eyeStyle(seed) + (LivingFace.feminine(seed) ? "/feminine" : "/plain"));
            }
            check(seen.size() == 4, "one of each face in the row: " + seen);
        });
        shoot(ctx, "faces");
        // close on the two Starlit faces, then the two Soft Glint faces
        tp(server, row.add(-1.3, 1.78, -1.7), row.add(-1.3, 1.72, 0));
        ctx.waitTicks(8);
        shoot(ctx, "starlit-eyes");
        tp(server, row.add(1.3, 1.78, -1.7), row.add(1.3, 1.72, 0));
        ctx.waitTicks(8);
        shoot(ctx, "soft-glint-eyes");
        // a blink: watch one face for a while and see its eyes shut at least once (the same timing as Village Friends)
        boolean blinked = false;
        int seed = LivingFace.seed(ids.getFirst());
        for (int t = 0; t < 200 && !blinked; t++) blinked = LivingFace.blink(t, seed) > 0.9F;
        check(blinked, "a Cirri blinks within ten seconds");
        // the hover pose from three-quarters
        tp(server, row.add(-3.6, 1.4, -2.6), row.add(-0.6, 1.1, 0));
        ctx.waitTicks(8);
        shoot(ctx, "hover-pose");
        server.runOnServer(srv -> spawned.forEach(id -> srv.overworld().getEntity(id).discard()));
    }

    // -- in flight ----------------------------------------------------------------------------------

    private void soaring(ClientGameTestContext ctx, TestSingleplayerContext world, TestServerContext server, Vec3 c, List<String> report) {
        Vec3 start = c.add(0, 10, 0);
        int id = server.computeOnServer(srv -> spawn(srv.overworld(), start, 0.0F, false, null).getId());
        tp(server, c.add(-18, 16, -18), start);
        ctx.waitFor(client -> client.level.getEntity(id) instanceof Cirri, 200);

        // thirty seconds of free flight, sampled every half second
        EnumSet<Cirri.Mode> modes = EnumSet.noneOf(Cirri.Mode.class);
        double travelled = 0, lowest = Double.MAX_VALUE, farthest = 0;
        float maxFlight = 0;
        Vec3 last = start;
        boolean cruiseShot = false;
        for (int i = 0; i < 60; i++) {
            ctx.waitTicks(10);
            double[] s = server.computeOnServer(srv -> {
                Cirri k = cirri(srv, id);
                ServerLevel level = srv.overworld();
                int ground = level.getHeight(Heightmap.Types.MOTION_BLOCKING, k.getBlockX(), k.getBlockZ());
                modes.add(k.mode());
                return new double[] {k.getX(), k.getY(), k.getZ(), k.getY() - ground, k.onGround() ? 1 : 0,
                        Math.hypot(k.getX() - k.home().getX(), k.getZ() - k.home().getZ())};
            });
            check(s[4] == 0, "still airborne after " + (i + 1) * 10 + " ticks");
            Vec3 now = new Vec3(s[0], s[1], s[2]);
            travelled += now.distanceTo(last);
            last = now;
            lowest = Math.min(lowest, s[3]);
            farthest = Math.max(farthest, s[5]);
            float flight = ctx.computeOnClient(client -> client.level.getEntity(id) instanceof Cirri k ? k.flight : 0.0F);
            maxFlight = Math.max(maxFlight, flight);
            // the follow camera: beside it, a little above, when it is going full tilt
            if (!cruiseShot && flight > 0.85F) {
                followShot(ctx, server, id, 4.2, "cruising");
                cruiseShot = true;
            }
        }
        check(lowest >= 1.5, String.format("kept clear of the ground (lowest %.1f blocks over it)", lowest));
        check(travelled > 40, String.format("soared about (%.0f blocks in 30 s)", travelled));
        check(farthest < 56, String.format("stayed near home (farthest %.0f blocks)", farthest));
        check(maxFlight > 0.8F, "the client posed it stretched out at cruise (flight " + maxFlight + ")");
        check(cruiseShot, "photographed at cruise");
        report.add(String.format("soaring: %.0f blocks in 30 s, lowest %.1f over the ground, farthest %.0f from home, modes %s",
                travelled, lowest, farthest, modes));

        // told to hover: it stops and stands upright on the air
        server.runOnServer(srv -> cirri(srv, id).hover(200));
        ctx.waitTicks(70);
        float hoverFlight = ctx.computeOnClient(client -> ((Cirri) client.level.getEntity(id)).flight);
        double hoverSpeed = server.computeOnServer(srv -> cirri(srv, id).getDeltaMovement().horizontalDistance());
        check(hoverSpeed < 0.05, "it stopped to hover (speed " + hoverSpeed + ")");
        check(hoverFlight < 0.3F, "the client posed it upright, hovering (flight " + hoverFlight + ")");
        followShot(ctx, server, id, 3.4, "hovering");

        // right-clicked by a player standing on the ground: it hovers a few blocks off, facing them
        server.runCommand("gamemode creative @a");
        Vec3 standing = server.computeOnServer(srv -> {
            Cirri k = cirri(srv, id);
            ServerLevel level = srv.overworld();
            int x = Mth.floor(k.getX()) + 4, z = Mth.floor(k.getZ()) + 4;
            return new Vec3(x + 0.5, level.getHeight(Heightmap.Types.MOTION_BLOCKING, x, z), z + 0.5);
        });
        tp(server, standing.add(0, 1.62, 0), server.computeOnServer(srv -> cirri(srv, id).position().add(0, 1.6, 0)));
        ctx.waitTicks(10);
        server.runOnServer(srv -> {
            Cirri k = cirri(srv, id);
            k.interact(player(srv), InteractionHand.MAIN_HAND, k.position());
        });
        ctx.waitTicks(100);
        double[] w = server.computeOnServer(srv -> {
            Cirri k = cirri(srv, id);
            ServerPlayer p = player(srv);
            Vec3 to = p.position().subtract(k.position());
            float face = (float) (Mth.atan2(to.z, to.x) * Mth.RAD_TO_DEG) - 90.0F;
            return new double[] {k.distanceTo(p), Math.abs(Mth.wrapDegrees(face - k.getYRot())), k.mode() == Cirri.Mode.TALK ? 1 : 0,
                    k.getY() - p.getY()};
        });
        check(w[2] == 1, "right-clicked, it comes to talk with the player");
        check(w[0] > 1.5 && w[0] < 5, String.format("it hovers in front of them (%.1f blocks)", w[0]));
        check(w[1] < 30, String.format("it faces the player (%.0f degrees off)", w[1]));
        check(w[3] > 0.2, String.format("its feet stay off the ground (%.1f above the player's)", w[3]));
        server.runCommand("execute as @a at @s run tp @s ~ ~ ~ facing entity @e[type=skyfriends:cirri,limit=1,sort=nearest] eyes");
        ctx.waitTicks(10);
        shoot(ctx, "talking-to-you");
        ctx.runOnClient(client -> {
            if (client.gui.screen() != null) client.gui.screen().onClose();
        });
        ctx.waitTicks(10);
        report.add(String.format("talking: %.1f blocks off, %.0f degrees from facing", w[0], w[1]));

        // hit: up and away
        double[] before = server.computeOnServer(srv -> {
            Cirri k = cirri(srv, id);
            ServerPlayer p = player(srv);
            double y = k.getY(), d = k.distanceTo(p);
            k.hurtServer(srv.overworld(), p.damageSources().playerAttack(p), 1.0F);
            return new double[] {y, d};
        });
        ctx.waitTicks(60);
        double[] after = server.computeOnServer(srv -> {
            Cirri k = cirri(srv, id);
            return new double[] {k.getY(), k.distanceTo(player(srv)), k.mode() == Cirri.Mode.FLEE ? 1 : 0};
        });
        check(after[2] == 1, "hurt, it flees");
        check(after[0] > before[0] + 3, String.format("it fled upward (%.1f -> %.1f)", before[0], after[0]));
        check(after[1] > before[1] + 6, String.format("and away (%.1f -> %.1f blocks)", before[1], after[1]));
        report.add(String.format("fleeing: rose %.1f blocks and got %.1f blocks farther in 3 s", after[0] - before[0], after[1] - before[1]));
        server.runCommand("gamemode spectator @a");

        if (FILM) film(ctx, server, id);
        server.runOnServer(srv -> cirri(srv, id).discard());
    }

    /** Puts the camera beside the Cirri (to its left, a little above), looking at it, and takes a photo. */
    private void followShot(ClientGameTestContext ctx, TestServerContext server, int id, double distance, String name) {
        for (int i = 0; i < 3; i++) {
            placeCamera(server, id, distance, 90.0F);
            ctx.waitTicks(1);
        }
        shoot(ctx, name);
    }

    private static void placeCamera(TestServerContext server, int id, double distance, float around) {
        Vec3[] spot = server.computeOnServer(srv -> {
            Cirri k = cirri(srv, id);
            Vec3 aim = k.position().add(0, 0.9, 0);
            Vec3 side = Vec3.directionFromRotation(0, k.getYRot() - around).scale(distance);
            return new Vec3[] {aim.add(side).add(0, 0.7, 0), aim};
        });
        tp(server, spot[0], spot[1]);
    }

    private void flock(ClientGameTestContext ctx, TestSingleplayerContext world, TestServerContext server, Vec3 c, List<String> report) {
        List<Integer> ids = server.computeOnServer(srv -> {
            List<Integer> out = new ArrayList<>();
            for (int i = 0; i < 6; i++) {
                double a = i * Math.PI / 3;
                out.add(spawn(srv.overworld(), c.add(Math.cos(a) * 6, 9 + i, Math.sin(a) * 6), i * 60.0F, false, null).getId());
            }
            return out;
        });
        tp(server, c.add(-26, 22, -26), c.add(0, 13, 0));
        ctx.waitTicks(240);
        world.getConnection().waitForChunksRender(false, 600);
        int airborne = server.computeOnServer(srv -> (int) ids.stream().map(i -> cirri(srv, i)).filter(k -> k != null && !k.onGround()).count());
        check(airborne == 6, "all six of the flock still in the air after 12 s");
        // aim the camera at the middle of the flock wherever it has got to
        Vec3 middle = server.computeOnServer(srv -> {
            Vec3 sum = Vec3.ZERO;
            for (int i : ids) sum = sum.add(cirri(srv, i).position());
            return sum.scale(1.0 / ids.size());
        });
        tp(server, middle.add(-22, 9, -22), middle.add(0, 1, 0));
        ctx.waitTicks(20);
        shoot(ctx, "flock");
        report.add("flock: 6 airborne after 12 s");
        server.runOnServer(srv -> ids.forEach(i -> cirri(srv, i).discard()));
    }

    // -- the film (-PskyFilm) -------------------------------------------------------------------------

    private void film(ClientGameTestContext ctx, TestServerContext server, int id) {
        ctx.getInput().resizeWindow(960, 540);
        server.runOnServer(srv -> {
            Cirri k = cirri(srv, id);
            k.setHealth(k.getMaxHealth());
            k.setLastHurtByMob(null);
            k.hover(1);
        });
        ctx.waitTicks(40);
        server.runOnServer(srv -> srv.tickRateManager().setTickRate(SLOW_TICKS));
        List<String> log = new ArrayList<>();
        int frame = 0;
        // 1: alongside it in flight, the camera swinging slowly from its side round toward its front
        for (int i = 0; i < 240; i++, frame++) {
            placeCamera(server, id, 4.6, 90.0F - Math.min(50.0F, i * 0.35F));
            frame(ctx, server, frame, "cruise", log);
        }
        // 2: it stops to hover; circle it close
        server.runOnServer(srv -> cirri(srv, id).hover(400));
        for (int i = 0; i < 220; i++, frame++) {
            placeCamera(server, id, 3.2, 40.0F + i * 1.4F);
            frame(ctx, server, frame, "hover", log);
        }
        // 3: off again
        server.runOnServer(srv -> cirri(srv, id).hover(1));
        for (int i = 0; i < 160; i++, frame++) {
            placeCamera(server, id, 5.0, 120.0F - i * 0.4F);
            frame(ctx, server, frame, "away", log);
        }
        server.runOnServer(srv -> srv.tickRateManager().setTickRate(20.0F));
        try {
            java.nio.file.Files.createDirectories(java.nio.file.Path.of("sky-frames"));
            java.nio.file.Files.write(java.nio.file.Path.of("sky-frames", "frames.txt"), log);
        } catch (java.io.IOException e) {
            throw new java.io.UncheckedIOException(e);
        }
        ctx.getInput().resizeWindow(1600, 900);
        log("filmed " + frame + " frames");
    }

    static void frame(ClientGameTestContext ctx, TestServerContext server, int frame, String stage, List<String> log) {
        frame(ctx, server, frame, stage, log, "sky-frames");
    }

    /** One frame of a film into {@code dir} (frame-NNNN.png), noting its stage and game tick. */
    static void frame(ClientGameTestContext ctx, TestServerContext server, int frame, String stage, List<String> log, String dir) {
        ctx.waitTicks(1);
        ctx.takeScreenshot(TestScreenshotOptions.of(String.format("frame-%04d", frame)).disableCounterPrefix()
                .withDestinationDir(java.nio.file.Path.of(dir)));
        long tick = server.computeOnServer(srv -> srv.overworld().getGameTime());
        log.add(frame + " " + stage + " " + tick);
    }
}
