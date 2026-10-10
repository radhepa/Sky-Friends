package dev.skyfriends.test;

import dev.skyfriends.SkyBlocks;
import dev.skyfriends.SkyFriends;
import dev.skyfriends.SkyItems;
import dev.skyfriends.block.WindStoneBlockEntity;
import dev.skyfriends.entity.Cirri;
import dev.skyfriends.entity.CloudKoi;
import dev.skyfriends.entity.CloudWhale;
import dev.skyfriends.entity.SkySpawner;
import dev.skyfriends.world.SkyPieces;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.gui.screens.inventory.MerchantScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The sky world in a real game (a fixed seed, structures on):
 * <ul>
 *   <li>a sky village is found and built: islands, buildings, its people spawned with homes and jobs, Cloud Koi at its pools;</li>
 *   <li>its wind lift: the Wind Stone on the ground under the dock carries a player up to the dock, and down again while they sneak, with no harm;</li>
 *   <li>the Cirri sleep floating in their nests at night and go to work by day; the Skymerchant trades; a couple has a baby who keeps by its mother;</li>
 *   <li>a wild sky islet, a wind shrine and a ruined belltower are found and built;</li>
 *   <li>a Cloud Whale is sent across the sky and swims on; a Cirrus Veil saves a fall.</li>
 * </ul>
 * Photographs each. With -PskyFilm it also films a tour (frames for tools/film.py).
 *   gradlew runClientGameTest -PskyTests=Sky -PtestHeap=2g [-PskyFilm] [-PcompatMods=...]
 */
@SuppressWarnings("UnstableApiUsage")
public class SkyWorldClientTest implements FabricClientGameTest {
    private int shot = 1;
    private int frame = 0;
    private final List<String> frames = new ArrayList<>();

    record Found(String kind, StructureStart start, BoundingBox box, SkyPieces.ResidentPiece residents, SkyPieces.LiftPiece lift, BlockPos centre) {}

    private void shoot(ClientGameTestContext ctx, String name) {
        ctx.runOnClient(client -> client.gui.toastManager().clear());
        ctx.takeScreenshot(String.format("sky-%02d-%s", shot++, name));
    }

    private static void check(boolean ok, String what) {
        CirriClientTest.check(ok, what);
    }

    private static void log(String what) {
        CirriClientTest.log(what);
    }

    private static ServerPlayer player(MinecraftServer srv) {
        return srv.getPlayerList().getPlayers().getFirst();
    }

    static Found locate(MinecraftServer srv, String kind) {
        ServerLevel level = srv.overworld();
        var registry = srv.registryAccess().lookupOrThrow(Registries.STRUCTURE);
        var holder = registry.getOrThrow(ResourceKey.create(Registries.STRUCTURE, SkyFriends.id(kind)));
        BlockPos near = level.findNearestMapStructure(HolderSet.direct(holder), BlockPos.ZERO, 160, false);
        if (near == null) return null;
        Structure structure = holder.value();
        StructureStart start = level.getChunk(near.getX() >> 4, near.getZ() >> 4).getStartForStructure(structure);
        check(start != null && start.isValid(), kind + ": structure start at " + near);
        BoundingBox box = start.getBoundingBox();
        for (int cx = box.minX() >> 4; cx <= box.maxX() >> 4; cx++)
            for (int cz = box.minZ() >> 4; cz <= box.maxZ() >> 4; cz++) level.getChunk(cx, cz);
        SkyPieces.ResidentPiece residents = null;
        SkyPieces.LiftPiece lift = null;
        for (var p : start.getPieces()) {
            if (p instanceof SkyPieces.ResidentPiece r) residents = r;
            if (p instanceof SkyPieces.LiftPiece l) lift = l;
        }
        BlockPos centre = residents != null ? residents.centre() : box.getCenter();
        // sample what was built
        int built = 0, skystone = 0, cloud = 0, lanterns = 0;
        var pos = new BlockPos.MutableBlockPos();
        for (int x = box.minX(); x <= box.maxX(); x += 2)
            for (int z = box.minZ(); z <= box.maxZ(); z += 2)
                for (int y = box.minY(); y <= box.maxY(); y++) {
                    var s = level.getBlockState(pos.set(x, y, z));
                    if (s.isAir()) continue;
                    if (s.is(SkyBlocks.SKYSTONE)) skystone++;
                    else if (s.is(SkyBlocks.CLOUD)) cloud++;
                    else if (s.is(SkyBlocks.SKY_LANTERN)) lanterns++;
                    built++;
                }
        log(String.format("%s at %s: %d pieces, box %s, sampled %d blocks (%d skystone, %d cloud, %d sky lanterns)", kind, near,
                start.getPieces().size(), box, built, skystone, cloud, lanterns));
        check(built > 200 && skystone > 30, kind + ": its islands were built");
        int bottom = start.getPieces().stream().filter(p -> p instanceof SkyPieces.TilePiece).mapToInt(p -> p.getBoundingBox().minY()).min().orElse(0);
        check(bottom > 150, kind + ": its islands float high in the sky (their bottom at y " + bottom + ")");
        return new Found(kind, start, box, residents, lift, centre);
    }

    /** Puts the camera's eye at {@code eye}, looking at {@code look}. */
    static void tp(TestServerContext server, Vec3 eye, Vec3 look) {
        CirriClientTest.tp(server, eye, look);
    }

    private void settle(ClientGameTestContext ctx, TestSingleplayerContext world, int ticks) {
        ctx.waitTicks(ticks);
        world.getConnection().waitForChunksRender(false, 1200);
    }

    @Override
    public void runTest(ClientGameTestContext ctx) {
        if (!CirriClientTest.wanted("Sky")) return;
        ctx.getInput().resizeWindow(CirriClientTest.FILM ? 960 : 1600, CirriClientTest.FILM ? 540 : 900);
        ctx.runOnClient(client -> client.options.renderDistance().set(12));
        // a normal world: superflat worlds only build the structures their preset lists
        try (TestSingleplayerContext world = ctx.worldBuilder().setUseConsistentSettings(false).adjustSettings(s -> {
            s.setGenerateStructures(true);
            s.setSeed(System.getProperty("skyfriends.seed", "20261010"));
        }).create()) {
            world.getConnection().waitForChunksRender(false, 2400);
            TestServerContext server = world.getServer();
            for (String cmd : List.of("gamerule spawn_mobs false", "gamerule advance_time false", "gamerule advance_weather false",
                    "time set 2000", "weather clear", "gamemode spectator @a")) {
                server.runCommand(cmd);
            }
            ctx.runOnClient(client -> {
                if (!client.gui.hud.isHidden()) client.gui.hud.toggle();
            });
            List<String> report = new ArrayList<>();
            village(ctx, world, server, report);
            for (String kind : List.of("sky_islet", "wind_shrine", "ruined_belltower")) wild(ctx, world, server, kind, report);
            whale(ctx, world, server, report);
            veil(ctx, world, server, report);
            log("summary:" + System.lineSeparator() + String.join(System.lineSeparator(), report));
            if (CirriClientTest.FILM) {
                try {
                    java.nio.file.Files.createDirectories(java.nio.file.Path.of("sky-tour"));
                    java.nio.file.Files.write(java.nio.file.Path.of("sky-tour", "frames.txt"), frames);
                } catch (java.io.IOException e) {
                    throw new java.io.UncheckedIOException(e);
                }
            }
        }
    }

    // -- the village ----------------------------------------------------------------------------------

    private void village(ClientGameTestContext ctx, TestSingleplayerContext world, TestServerContext server, List<String> report) {
        Found v = server.computeOnServer(srv -> locate(srv, "sky_village"));
        check(v != null, "found a sky village");
        check(v.residents() != null && v.lift() != null, "the village has its people and its lift");
        Vec3 c = Vec3.atCenterOf(v.centre());
        int expected = (int) v.residents().residents().stream().filter(r -> r.type().equals("cirri")).count();
        int koiExpected = (int) v.residents().residents().stream().filter(r -> r.type().equals("cloud_koi")).count();

        // from afar: floating over the land
        tp(server, c.add(-72, 10, -72), c.add(0, -8, 0));
        settle(ctx, world, 60);
        int cirri = waitCount(ctx, server, c, expected);
        check(cirri >= expected - 1, "its people were spawned (" + cirri + " of " + expected + ")");
        shoot(ctx, "village-from-afar");
        if (CirriClientTest.FILM) {
            orbit(ctx, server, c, 72, 12, 225, 200, "village-orbit");
            follow(ctx, server, v.centre(), 200);
        }

        // in the court
        tp(server, c.add(0, 4, -13), c.add(0, 0, 0));
        settle(ctx, world, 30);
        shoot(ctx, "village-court");
        tp(server, c.add(18, 14, 18), c.add(0, 0, 0));
        settle(ctx, world, 20);
        shoot(ctx, "village-rooftops");

        // the people: homes, jobs, families
        String people = server.computeOnServer(srv -> {
            List<Cirri> all = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(v.centre()).inflate(96), Cirri::isAlive);
            long women = all.stream().filter(k -> !k.isBaby() && k.female()).count(), men = all.stream().filter(k -> !k.isBaby() && !k.female()).count();
            long kids = all.stream().filter(Cirri::isBaby).count(), working = all.stream().filter(k -> !k.job().isEmpty()).count();
            check(women > 0 && men > 0, "women and men live there (" + women + " and " + men + ")");
            check(all.stream().filter(k -> !k.isBaby()).allMatch(k -> k.settled() && v.centre().equals(k.home())), "every grown-up belongs to the village");
            check(all.stream().filter(Cirri::isBaby).allMatch(k -> k.mother() != null), "every child has a mother");
            check(all.stream().anyMatch(k -> k.job().equals("skymerchant")), "the village has a Skymerchant");
            check(all.stream().allMatch(Cirri::hasCustomName), "everyone has a name");
            return women + " women, " + men + " men, " + kids + " children, " + working + " with jobs";
        });
        report.add("village at " + v.centre().toShortString() + ": " + people);

        // the lift
        liftRide(ctx, world, server, v, report);

        // night: asleep in their nests
        server.runCommand("time set 18000");
        int[] sleep = {0, 1};
        int waited = 0;
        for (; waited < 1200 && sleep[0] * 4 < sleep[1] * 3; waited += 40) {
            ctx.waitTicks(40);
            sleep = server.computeOnServer(srv -> {
                List<Cirri> grown = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(v.centre()).inflate(96), k -> !k.isBaby() && k.bed() != null);
                return new int[] {(int) grown.stream().filter(Cirri::asleep).count(), grown.size()};
            });
        }
        check(sleep[0] * 4 >= sleep[1] * 3, "at night they fly home and sleep in their nests (" + sleep[0] + " of " + sleep[1] + ")");
        report.add("night: " + sleep[0] + " of " + sleep[1] + " asleep after " + waited / 20 + " s");
        Vec3[] sleeper = server.computeOnServer(srv -> {
            var k = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(v.centre()).inflate(96), Cirri::asleep).stream().findFirst().orElse(null);
            if (k == null) return null;
            Vec3 face = Vec3.directionFromRotation(0, k.getYRot()).scale(2.6);
            return new Vec3[] {k.position().add(face).add(0, 1.4, 0), k.position().add(0, 0.9, 0)};
        });
        if (sleeper != null) {
            tp(server, sleeper[0], sleeper[1]);
            settle(ctx, world, 20);
            shoot(ctx, "asleep-in-the-nest");
        }

        // morning: to work
        server.runCommand("time set 1000");
        int working = 0;
        for (int i = 0; i < 60 && working < 3; i++) {
            ctx.waitTicks(30);
            working = server.computeOnServer(srv -> (int) srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(v.centre()).inflate(96),
                    k -> k.state() == Cirri.WORKING).size());
        }
        String jobs = server.computeOnServer(srv -> {
            StringBuilder b = new StringBuilder();
            for (Cirri k : srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(v.centre()).inflate(96), w -> w.work() != null)) {
                b.append(String.format("%n  %s %s state %d, %.1f blocks from work %s (at %s) %s", k.getName().getString(), k.job(),
                        k.state(), Math.sqrt(k.distanceToSqr(Vec3.atBottomCenterOf(k.work()))), k.work().toShortString(), k.blockPosition().toShortString(),
                        k.debug()));
            }
            return b.toString();
        });
        log("workers after the morning:" + jobs);
        if (working == 0) {
            Vec3[] stuck = server.computeOnServer(srv -> {
                var k = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(v.centre()).inflate(96), w -> w.work() != null).getFirst();
                return new Vec3[] {k.position().add(2.5, 1.6, 2.5), k.position().add(0, 1, 0)};
            });
            tp(server, stuck[0], stuck[1]);
            settle(ctx, world, 20);
            shoot(ctx, "why-not-at-work");
        }
        check(working >= 3, "by day they go to work (" + working + " at work)");
        report.add("day: " + working + " at work within a minute and a half");
        Vec3[] worker = server.computeOnServer(srv -> {
            var k = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(v.centre()).inflate(96), w -> w.state() == Cirri.WORKING).getFirst();
            Vec3 face = Vec3.directionFromRotation(0, k.getYRot()).scale(3.0);
            return new Vec3[] {k.position().add(face).add(0, 1.5, 0), k.position().add(0, 1.0, 0)};
        });
        tp(server, worker[0], worker[1]);
        settle(ctx, world, 20);
        shoot(ctx, "at-work");

        // the Skymerchant
        server.runCommand("gamemode creative @a");
        Vec3[] shop = server.computeOnServer(srv -> {
            var m = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(v.centre()).inflate(96), k -> k.job().equals("skymerchant")).getFirst();
            m.hover(400);
            Vec3 face = Vec3.directionFromRotation(0, m.getYRot()).scale(2.5);
            return new Vec3[] {m.position().add(face).add(0, 1.6, 0), m.position().add(0, 1.6, 0)};
        });
        tp(server, shop[0], shop[1]);
        ctx.waitTicks(10);
        server.runOnServer(srv -> {
            var m = srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(v.centre()).inflate(96), k -> k.job().equals("skymerchant")).getFirst();
            m.interact(player(srv), InteractionHand.MAIN_HAND, m.position());
        });
        ctx.waitFor(client -> client.gui.screen() instanceof MerchantScreen, 100);
        check(ctx.computeOnClient(client -> client.gui.screen() instanceof MerchantScreen), "the Skymerchant opens their trades");
        shoot(ctx, "skymerchant");
        ctx.runOnClient(client -> client.gui.screen().onClose());
        ctx.waitTicks(10);

        // a baby
        String baby = server.computeOnServer(srv -> {
            ServerLevel level = srv.overworld();
            for (Cirri mum : level.getEntitiesOfClass(Cirri.class, new AABB(v.centre()).inflate(96), k -> !k.isBaby() && k.female() && k.bed() != null)) {
                Cirri b = mum.haveBaby(level);
                if (b != null) {
                    check(b.isBaby() && mum.getUUID().equals(b.mother()), "a baby is born to her (" + mum.getName().getString() + ")");
                    return b.getName().getString() + " born to " + mum.getName().getString();
                }
            }
            return null;
        });
        check(baby != null, "a couple can have a baby");
        report.add("baby: " + baby);

        // the koi
        ctx.waitTicks(200);
        int[] koi = server.computeOnServer(srv -> {
            List<CloudKoi> all = srv.overworld().getEntitiesOfClass(CloudKoi.class, new AABB(v.centre()).inflate(96), CloudKoi::isAlive);
            int near = (int) all.stream().filter(k -> k.distanceToSqr(Vec3.atCenterOf(k.home())) < 14 * 14).count();
            return new int[] {all.size(), near};
        });
        check(koi[0] >= koiExpected - 1, "Cloud Koi swim at the village's pools (" + koi[0] + " of " + koiExpected + ")");
        check(koi[1] >= koi[0] - 1, "the koi keep near their pools (" + koi[1] + " of " + koi[0] + ")");
        report.add("koi: " + koi[0] + ", " + koi[1] + " near their pools after 10 s");
        Vec3[] pool = server.computeOnServer(srv -> {
            var k = srv.overworld().getEntitiesOfClass(CloudKoi.class, new AABB(v.centre()).inflate(96), CloudKoi::isAlive).stream().findFirst().orElse(null);
            if (k == null) return null;
            return new Vec3[] {k.position().add(3, 1.5, 3), k.position()};
        });
        if (pool != null) {
            tp(server, pool[0], pool[1]);
            settle(ctx, world, 15);
            shoot(ctx, "cloud-koi");
        }
        server.runCommand("gamemode spectator @a");
    }

    private int waitCount(ClientGameTestContext ctx, TestServerContext server, Vec3 c, int expected) {
        int n = 0;
        for (int i = 0; i < 30; i++) {
            n = server.computeOnServer(srv -> srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(BlockPos.containing(c)).inflate(96),
                    Cirri::isAlive).size());
            if (n >= expected) break;
            ctx.waitTicks(20);
        }
        return n;
    }

    private void liftRide(ClientGameTestContext ctx, TestSingleplayerContext world, TestServerContext server, Found v, List<String> report) {
        BlockPos stone = v.lift().stone();
        int[] lift = server.computeOnServer(srv -> {
            ServerLevel level = srv.overworld();
            check(level.getBlockState(stone).is(SkyBlocks.WIND_STONE), "the Wind Stone stands on the ground below the dock (" + stone.toShortString() + ")");
            var be = (WindStoneBlockEntity) level.getBlockEntity(stone);
            check(be != null && be.connected(), "the Wind Stone is connected to the dock");
            BlockPos land = be.landing();
            check(!level.getBlockState(land.below()).isAir(), "the landing on the dock is solid (" + land.below().toShortString() + ")");
            for (int y = stone.getY() + 2; y < be.top() - 1; y += 3) {
                check(level.getBlockState(stone.atY(y)).getCollisionShape(level, stone.atY(y)).isEmpty(), "the shaft is open at y " + y);
            }
            return new int[] {be.top(), land.getX(), land.getZ()};
        });
        int top = lift[0];
        // look up the column from the ground
        tp(server, Vec3.atCenterOf(stone).add(-7, 2.5, -7), Vec3.atCenterOf(stone).add(0, 30, 0));
        settle(ctx, world, 30);
        shoot(ctx, "wind-stone");
        // ride up as a player (survival: the lift must keep them from falling)
        server.runCommand("gamemode survival @a");
        server.runCommand("effect give @a resistance 60 4 true");
        server.runOnServer(srv -> player(srv).teleportTo(stone.getX() + 0.5, stone.getY() + 1.0, stone.getZ() + 0.5));
        if (CirriClientTest.FILM) {
            slow(server, true);
            ctx.runOnClient(client -> client.player.setXRot(-25.0F));
        }
        double y = 0;
        boolean photographed = false;
        int ticks = 0;
        for (; ticks < 900; ticks += 2) {
            if (CirriClientTest.FILM) frame(ctx, server, "lift");
            else ctx.waitTicks(2);
            y = ctx.computeOnClient(client -> client.player.getY());
            if (!photographed && y > (stone.getY() + top) / 2.0) {
                ctx.runOnClient(client -> client.player.setXRot(35.0F));
                shoot(ctx, "riding-the-wind");
                photographed = true;
            }
            if (y > top - 0.6) break;
        }
        if (CirriClientTest.FILM) {
            for (int i = 0; i < 40; i++) {
                float pitch = -25.0F + i * 0.9F;
                ctx.runOnClient(client -> client.player.setXRot(pitch));
                frame(ctx, server, "landing");
            }
            slow(server, false);
        }
        check(y > top - 0.6, String.format("the wind carried the player up to the dock (y %.1f, dock %d) in %d ticks", y, top, ticks));
        ctx.waitTicks(60);
        double[] at = ctx.computeOnClient(client -> new double[] {client.player.getX(), client.player.getY(), client.player.getZ(),
                client.player.onGround() ? 1 : 0});
        double off = Math.hypot(at[0] - (lift[1] + 0.5), at[2] - (lift[2] + 0.5));
        check(at[3] == 1 && off < 2.0, String.format("and set them down on the dock (%.1f blocks from the landing, on ground %s)", off, at[3] == 1));
        ctx.runOnClient(client -> client.player.setXRot(10.0F));
        shoot(ctx, "on-the-dock");
        report.add(String.format("lift: up %d blocks in %.1f s", top - stone.getY(), ticks / 20.0));
        // and down: step back into the shaft and hold sneak
        float health = server.computeOnServer(srv -> player(srv).getHealth());
        server.runOnServer(srv -> player(srv).teleportTo(stone.getX() + 0.5, top + 0.2, stone.getZ() + 0.5));
        ctx.getInput().holdKey(o -> o.keyShift);
        for (ticks = 0; ticks < 1600; ticks += 10) {
            ctx.waitTicks(10);
            y = ctx.computeOnClient(client -> client.player.getY());
            if (y < stone.getY() + 2.5) break;
        }
        ctx.waitTicks(30);
        ctx.getInput().releaseKey(o -> o.keyShift);
        float after = server.computeOnServer(srv -> player(srv).getHealth());
        check(y < stone.getY() + 2.5, String.format("sneaking, the player sank back to the ground (y %.1f) in %.0f s", y, ticks / 20.0));
        check(after >= health, "with no harm (" + health + " -> " + after + ")");
        report.add(String.format("lift: down in %.0f s, health %.0f -> %.0f", ticks / 20.0, health, after));
        server.runCommand("effect clear @a");
        server.runCommand("gamemode spectator @a");
    }

    // -- the wild sky -----------------------------------------------------------------------------------

    private void wild(ClientGameTestContext ctx, TestSingleplayerContext world, TestServerContext server, String kind, List<String> report) {
        Found f = server.computeOnServer(srv -> locate(srv, kind));
        check(f != null, "found a " + kind);
        BoundingBox b = f.box();
        Vec3 c = new Vec3((b.minX() + b.maxX()) / 2.0, (b.minY() + b.maxY()) / 2.0 + 4, (b.minZ() + b.maxZ()) / 2.0);
        double r = Math.max(b.getXSpan(), b.getZSpan()) * 0.75 + 12;
        tp(server, c.add(-r * 0.7, r * 0.35, -r * 0.7), c);
        settle(ctx, world, 60);
        shoot(ctx, kind);
        report.add(kind + " at " + BlockPos.containing(c).toShortString());
    }

    private void whale(ClientGameTestContext ctx, TestSingleplayerContext world, TestServerContext server, List<String> report) {
        server.runCommand("gamemode creative @a");
        int id = server.computeOnServer(srv -> {
            CloudWhale w = SkySpawner.spawnNear(srv.overworld(), player(srv));
            check(w != null, "a Cloud Whale was sent across the sky");
            return w.getId();
        });
        Vec3 from = server.computeOnServer(srv -> srv.overworld().getEntity(id).position());
        ctx.waitTicks(120);
        Vec3 to = server.computeOnServer(srv -> srv.overworld().getEntity(id).position());
        check(to.distanceTo(from) > 5, String.format("the whale swims on (%.1f blocks in 6 s)", to.distanceTo(from)));
        check(to.y > 150, "high in the sky (y " + (int) to.y + ")");
        Vec3[] view = server.computeOnServer(srv -> {
            var w = srv.overworld().getEntity(id);
            Vec3 side = Vec3.directionFromRotation(0, w.getYRot() + 90).scale(22);
            return new Vec3[] {w.position().add(side).add(0, 4, 0), w.position().add(0, 3, 0)};
        });
        tp(server, view[0], view[1]);
        settle(ctx, world, 30);
        shoot(ctx, "cloud-whale");
        if (CirriClientTest.FILM) {
            slow(server, true);
            for (int i = 0; i < 160; i++) {
                Vec3[] v = server.computeOnServer(srv -> {
                    var w = srv.overworld().getEntity(id);
                    Vec3 side = Vec3.directionFromRotation(0, w.getYRot() + 70).scale(24);
                    return new Vec3[] {w.position().add(side).add(0, 5, 0), w.position().add(0, 3, 0)};
                });
                tp(server, v[0], v[1]);
                frame(ctx, server, "whale");
            }
            slow(server, false);
        }
        report.add(String.format("whale: swam %.1f blocks in 6 s at y %d", to.distanceTo(from), (int) to.y));
        server.runCommand("gamemode spectator @a");
    }

    private void veil(ClientGameTestContext ctx, TestSingleplayerContext world, TestServerContext server, List<String> report) {
        server.runCommand("gamemode survival @a");
        float before = server.computeOnServer(srv -> {
            ServerPlayer p = player(srv);
            p.setItemSlot(EquipmentSlot.CHEST, new ItemStack(SkyItems.CIRRUS_VEIL));
            // over dry land (not the sea, where there's nothing to land on)
            ServerLevel level = srv.overworld();
            BlockPos dry = null;
            for (int r = 0; r < 200 && dry == null; r += 8) {
                for (int a = 0; a < 8 && dry == null; a++) {
                    int x = p.getBlockX() + (int) (Math.cos(a * Math.PI / 4) * r), z = p.getBlockZ() + (int) (Math.sin(a * Math.PI / 4) * r);
                    int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING, x, z);
                    BlockPos top = new BlockPos(x, y - 1, z);
                    if (level.getFluidState(top).isEmpty() && y < 150) dry = top.above();
                }
            }
            check(dry != null, "found dry land to fall onto");
            p.teleportTo(dry.getX() + 0.5, dry.getY() + 40, dry.getZ() + 0.5);
            p.setHealth(p.getMaxHealth());
            return p.getHealth();
        });
        boolean slowFalling = false;
        for (int i = 0; i < 60 && !slowFalling; i++) {
            ctx.waitTicks(5);
            slowFalling = server.computeOnServer(srv -> player(srv).hasEffect(net.minecraft.world.effect.MobEffects.SLOW_FALLING));
        }
        check(slowFalling, "falling in a Cirrus Veil, the player glides (Slow Falling)");
        for (int i = 0; i < 80; i++) {
            ctx.waitTicks(10);
            if (ctx.computeOnClient(client -> client.player.onGround())) break;
        }
        float after = server.computeOnServer(srv -> player(srv).getHealth());
        check(after >= before, "and lands from 40 blocks unhurt (" + before + " -> " + after + ")");
        report.add("veil: fell 40 blocks, health " + before + " -> " + after);
        server.runCommand("gamemode spectator @a");
    }

    // -- film (-PskyFilm) -----------------------------------------------------------------------------------

    private static void slow(TestServerContext server, boolean on) {
        server.runOnServer(srv -> srv.tickRateManager().setTickRate(on ? CirriClientTest.SLOW_TICKS : 20.0F));
    }

    private void orbit(ClientGameTestContext ctx, TestServerContext server, Vec3 centre, double radius, double up, float from, int count, String stage) {
        slow(server, true);
        for (int i = 0; i < count; i++) {
            double a = Math.toRadians(from + i * 0.45);
            tp(server, centre.add(Math.cos(a) * radius, up, Math.sin(a) * radius), centre.add(0, -6, 0));
            frame(ctx, server, stage);
        }
        slow(server, false);
    }

    /** Film a Cirri of the village flying about, the camera alongside it. */
    private void follow(ClientGameTestContext ctx, TestServerContext server, BlockPos centre, int count) {
        Integer id = server.computeOnServer(srv -> srv.overworld().getEntitiesOfClass(Cirri.class, new AABB(centre).inflate(96),
                k -> !k.isBaby() && k.mode() == Cirri.Mode.SOAR).stream().map(Cirri::getId).findFirst().orElse(null));
        if (id == null) return;
        slow(server, true);
        for (int i = 0; i < count; i++) {
            Vec3[] v = server.computeOnServer(srv -> {
                var k = srv.overworld().getEntity(id);
                Vec3 aim = k.position().add(0, 0.9, 0);
                return new Vec3[] {aim.add(Vec3.directionFromRotation(0, k.getYRot() - 110).scale(4.8)).add(0, 0.8, 0), aim};
            });
            tp(server, v[0], v[1]);
            frame(ctx, server, "follow");
        }
        slow(server, false);
    }

    private void frame(ClientGameTestContext ctx, TestServerContext server, String stage) {
        CirriClientTest.frame(ctx, server, frame++, stage, frames, "sky-tour");
    }
}
