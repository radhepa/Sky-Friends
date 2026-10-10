package dev.skyfriends.life;

import dev.skyfriends.entity.Cirri;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.phys.AABB;
import org.jspecify.annotations.Nullable;

/**
 * Who a Cirri's people are, read from the village as it is: the one they share a nest with (set when the
 * village was made), their children, a child's mum and dad, their closest friend, someone with the same job,
 * someone they're sweet on. Friends and sweethearts are fixed for a pair (the same two always), so a village
 * keeps its own friendships.
 */
public final class Kin {
    private Kin() {}

    /** Everyone loaded who lives in this Cirri's village (the same home), including themselves. */
    public static List<Cirri> village(Cirri c) {
        if (!(c.level() instanceof ServerLevel level)) return List.of();
        var home = c.home();
        return level.getEntitiesOfClass(Cirri.class, new AABB(home).inflate(96), o -> o.isAlive() && home.equals(o.home()));
    }

    private static @Nullable Cirri find(Cirri c, @Nullable UUID id) {
        if (id == null || !(c.level() instanceof ServerLevel level)) return null;
        return level.getEntity(id) instanceof Cirri o && o.isAlive() ? o : null;
    }

    public static @Nullable Cirri partner(Cirri c) {
        return find(c, c.partner());
    }

    /** "husband" or "wife": what their partner is to them. */
    public static String spouseWord(Cirri c) {
        return c.female() ? "husband" : "wife";
    }

    public static List<Cirri> children(Cirri c, List<Cirri> village) {
        UUID me = c.getUUID(), partner = c.partner();
        return village.stream().filter(o -> o.isBaby() && o.mother() != null && (o.mother().equals(me) || o.mother().equals(partner))).toList();
    }

    public static @Nullable Cirri mother(Cirri c) {
        return find(c, c.mother());
    }

    public static @Nullable Cirri father(Cirri c) {
        Cirri mum = mother(c);
        return mum == null ? null : find(c, mum.partner());
    }

    /** Their closest friend in the village: of their own age, not family. */
    public static @Nullable Cirri friend(Cirri c, List<Cirri> village) {
        return village.stream().filter(o -> o != c && o.isBaby() == c.isBaby() && !family(c, o))
                .max(Comparator.comparingLong(o -> pair(c, o))).orElse(null);
    }

    public static @Nullable Cirri coworker(Cirri c, List<Cirri> village) {
        if (c.job().isEmpty()) return null;
        return village.stream().filter(o -> o != c && o.job().equals(c.job())).findFirst().orElse(null);
    }

    /** Someone a grown-up with no partner is sweet on, if anyone: another grown-up with no partner. */
    public static @Nullable Cirri crush(Cirri c, List<Cirri> village) {
        if (c.isBaby() || c.partner() != null) return null;
        return village.stream().filter(o -> o != c && !o.isBaby() && o.partner() == null && o.female() != c.female()
                && Math.floorMod(pair(c, o), 3) == 0).max(Comparator.comparingLong(o -> pair(c, o))).orElse(null);
    }

    /** Partners, parents and children. */
    public static boolean family(Cirri a, Cirri b) {
        UUID ia = a.getUUID(), ib = b.getUUID();
        return ib.equals(a.partner()) || ia.equals(b.partner()) || ib.equals(a.mother()) || ia.equals(b.mother())
                || (a.mother() != null && a.mother().equals(b.partner())) || (b.mother() != null && b.mother().equals(a.partner()))
                || (a.mother() != null && a.mother().equals(b.mother()));
    }

    /** A number fixed for a pair, the same whichever way round: how well these two get on. */
    public static long pair(Cirri a, Cirri b) {
        long x = a.getUUID().getMostSignificantBits() ^ b.getUUID().getMostSignificantBits()
                ^ a.getUUID().getLeastSignificantBits() ^ b.getUUID().getLeastSignificantBits();
        x ^= x >>> 33;
        x *= 0xFF51AFD7ED558CCDL;
        x ^= x >>> 33;
        return x & Long.MAX_VALUE;
    }
}
