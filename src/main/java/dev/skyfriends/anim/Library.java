package dev.skyfriends.anim;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;

/** Every people's animation pack, by people, with each pack's clips indexed by trigger. */
public final class Library {
    /** The packs that ship with the mod, one per people. */
    public static final List<String> SPECIES = List.of("cirri");
    private static final String PATH = "/assets/skyfriends/animations/";
    private static volatile Library current;

    private final Map<String, Pack> packs = new HashMap<>();
    private final Map<String, Map<String, List<Clip>>> byTrigger = new HashMap<>();

    public Library(List<Pack> packs) {
        for (Pack pack : packs) {
            this.packs.put(pack.species(), pack);
            Map<String, List<Clip>> index = new HashMap<>();
            for (Clip clip : pack.clips()) index.computeIfAbsent(clip.trigger(), t -> new ArrayList<>()).add(clip);
            index.replaceAll((t, list) -> List.copyOf(list));
            this.byTrigger.put(pack.species(), index);
        }
    }

    public static Library current() {
        Library l = current;
        if (l == null) current = l = bundled();
        return l;
    }

    public static void install(Library library) {
        current = library;
    }

    public Pack pack(String species) {
        return packs.get(species);
    }

    public List<Clip> clips(String species, String trigger) {
        return byTrigger.getOrDefault(species, Map.of()).getOrDefault(trigger, List.of());
    }

    /**
     * Weighted choice among the eligible clips for a trigger. Recently played clips are strongly discouraged, so
     * nobody repeats themselves while anything else fits.
     */
    public Clip pick(String species, String trigger, Set<String> tags, Random random, String... recent) {
        List<Clip> options = clips(species, trigger);
        float total = 0;
        for (Clip clip : options) total += chance(clip, tags, recent);
        if (total <= 0) return null;
        float roll = random.nextFloat() * total;
        for (Clip clip : options) {
            float w = chance(clip, tags, recent);
            if (w <= 0) continue;
            if ((roll -= w) <= 0) return clip;
        }
        for (int i = options.size() - 1; i >= 0; i--) {
            if (chance(options.get(i), tags, recent) > 0) return options.get(i);
        }
        return null;
    }

    private static float chance(Clip clip, Set<String> tags, String[] recent) {
        if (!clip.eligible(tags)) return 0;
        float w = clip.weightFor(tags);
        for (String id : recent) {
            if (clip.id().equals(id)) w *= .06F;
        }
        return w;
    }

    /** The packs bundled in the jar (a missing pack is simply a people with no clips). */
    public static Library bundled() {
        List<Pack> packs = new ArrayList<>();
        for (String species : SPECIES) {
            try (InputStream in = Library.class.getResourceAsStream(PATH + species + ".json")) {
                if (in == null) continue;
                packs.add(Pack.parse(new String(in.readAllBytes(), StandardCharsets.UTF_8)));
            } catch (IOException e) {
                throw new IllegalStateException("Cannot read the animation pack " + species, e);
            }
        }
        return new Library(packs);
    }
}
