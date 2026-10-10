package dev.skyfriends.anim;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * One people's animations: {@code assets/skyfriends/animations/<people>.json}, compiled from
 * {@code tools/animations/<people>/*.py} (docs/ANIMATIONS.md has the format). The pack names the {@code waist}: the
 * height of the hips and the parts that bend with the upper body.
 */
public record Pack(String species, String name, float hip, Set<String> upper, List<Clip> clips) {
    public static final int FORMAT = 1;
    /** The moments the director plays clips for. Unknown triggers are rejected to catch typos. */
    public static final Set<String> TRIGGERS = Set.of("idle", "greet", "farewell", "talk", "listen", "chat_speak", "chat_listen",
            "happy", "thanks", "decline", "pleased", "annoyed", "hurt");
    private static final float MAX_ROTATION = 400, MAX_OFFSET = 16, MAX_LENGTH = 30;

    public static Pack parse(String json) {
        try {
            return parse(JsonParser.parseString(json).getAsJsonObject());
        } catch (IllegalArgumentException e) {
            throw e;
        } catch (RuntimeException e) {
            throw new IllegalArgumentException("Animation pack is not valid JSON: " + e.getMessage(), e);
        }
    }

    public static Pack parse(JsonObject root) {
        if (!root.has("format") || root.get("format").getAsInt() != FORMAT) {
            throw new IllegalArgumentException("Animation pack needs \"format\": " + FORMAT);
        }
        String species = text(root, "species", null);
        if (species == null || !species.matches("[a-z_]+")) throw new IllegalArgumentException("Animation pack needs a species");
        JsonObject waist = root.has("waist") ? root.getAsJsonObject("waist") : new JsonObject();
        float hip = number(waist, "hip", 12);
        Set<String> upper = new LinkedHashSet<>();
        if (waist.has("upper")) for (JsonElement e : waist.getAsJsonArray("upper")) upper.add(e.getAsString());
        List<Clip> clips = new ArrayList<>();
        Set<String> ids = new HashSet<>();
        if (!root.has("clips") || !root.get("clips").isJsonArray()) throw new IllegalArgumentException("Animation pack " + species + " has no clips");
        for (JsonElement e : root.getAsJsonArray("clips")) {
            Clip clip = clip(species, e.getAsJsonObject());
            if (!ids.add(clip.id())) throw new IllegalArgumentException("Duplicate clip " + clip.id());
            clips.add(clip);
        }
        return new Pack(species, text(root, "name", species), hip, Collections.unmodifiableSet(upper), List.copyOf(clips));
    }

    private static Clip clip(String species, JsonObject o) {
        String local = text(o, "id", null);
        if (local == null || !local.matches("[a-z0-9_]+")) throw new IllegalArgumentException("Clip ids in " + species + " must be lowercase words: " + local);
        String id = species + ":" + local, where = "Clip " + id;
        String trigger = text(o, "trigger", "idle");
        if (!TRIGGERS.contains(trigger)) throw new IllegalArgumentException(where + " has unknown trigger " + trigger);
        float length = number(o, "length", -1);
        if (!(length > 0 && length <= MAX_LENGTH)) throw new IllegalArgumentException(where + " needs a length between 0 and " + MAX_LENGTH + " seconds");
        float weight = number(o, "weight", 1);
        if (!(weight > 0)) throw new IllegalArgumentException(where + " needs a positive weight");
        List<Set<String>> require = new ArrayList<>();
        if (o.has("require")) for (JsonElement e : o.getAsJsonArray("require")) require.add(Set.of(e.getAsString().split("\\|")));
        Set<String> avoid = new HashSet<>();
        if (o.has("avoid")) for (JsonElement e : o.getAsJsonArray("avoid")) avoid.add(e.getAsString());
        Map<String, Float> boost = new LinkedHashMap<>();
        if (o.has("boost")) {
            for (Map.Entry<String, JsonElement> e : o.getAsJsonObject("boost").entrySet()) {
                float b = e.getValue().getAsFloat();
                if (!(b >= 0)) throw new IllegalArgumentException(where + " has a negative boost");
                boost.put(e.getKey(), b);
            }
        }
        float blendIn = .25F, blendOut = .35F;
        if (o.has("blend")) {
            JsonArray b = o.getAsJsonArray("blend");
            blendIn = b.get(0).getAsFloat();
            blendOut = b.get(1).getAsFloat();
        }
        if (blendIn < 0 || blendOut < 0 || blendIn + blendOut > length + 1e-4F) throw new IllegalArgumentException(where + " blends longer than the clip");
        Clip.Mirror mirror = switch (text(o, "mirror", "hand")) {
            case "hand" -> Clip.Mirror.HAND;
            case "free" -> Clip.Mirror.FREE;
            case "never" -> Clip.Mirror.NEVER;
            default -> throw new IllegalArgumentException(where + " mirror must be hand, free or never");
        };
        if (!o.has("tracks")) throw new IllegalArgumentException(where + " has no tracks");
        Map<String, Track[]> byBone = new LinkedHashMap<>();
        for (Map.Entry<String, JsonElement> e : o.getAsJsonObject("tracks").entrySet()) {
            String key = e.getKey();
            int dot = key.lastIndexOf('.');
            if (dot <= 0) throw new IllegalArgumentException(where + " track " + key + " must be <part>.rot or <part>.pos");
            String bone = key.substring(0, dot), channel = key.substring(dot + 1);
            if (!bone.matches("[a-z0-9_]+")) throw new IllegalArgumentException(where + " has a bad part name " + bone);
            Track[] pair = byBone.computeIfAbsent(bone, b -> new Track[2]);
            switch (channel) {
                case "rot" -> pair[0] = track(where, key, e.getValue(), MAX_ROTATION);
                case "pos" -> {
                    if (bone.equals(Clip.WAIST)) throw new IllegalArgumentException(where + ": the waist only rotates");
                    pair[1] = track(where, key, e.getValue(), MAX_OFFSET);
                }
                default -> throw new IllegalArgumentException(where + " track " + key + " must end in .rot or .pos");
            }
            Track t = pair[channel.equals("rot") ? 0 : 1];
            if (t.end() > length + 1e-4F) throw new IllegalArgumentException(where + " has keys after its length");
        }
        int n = byBone.size();
        String[] bones = new String[n], mirrored = new String[n];
        Track[] rotations = new Track[n], positions = new Track[n];
        int i = 0;
        for (Map.Entry<String, Track[]> e : byBone.entrySet()) {
            bones[i] = e.getKey();
            mirrored[i] = Clip.mirror(e.getKey());
            rotations[i] = e.getValue()[0];
            positions[i] = e.getValue()[1];
            i++;
        }
        return new Clip(id, text(o, "name", local), trigger, length, weight, List.copyOf(require), Set.copyOf(avoid),
                Collections.unmodifiableMap(boost), blendIn, blendOut, mirror, bones, mirrored, rotations, positions);
    }

    /** Keys are {@code [time, x, y, z]}. */
    private static Track track(String where, String key, JsonElement element, float limit) {
        JsonArray keys = element.getAsJsonArray();
        if (keys.isEmpty()) throw new IllegalArgumentException(where + " track " + key + " is empty");
        float[] times = new float[keys.size()], values = new float[keys.size() * 3];
        for (int i = 0; i < keys.size(); i++) {
            JsonArray k = keys.get(i).getAsJsonArray();
            if (k.size() != 4) throw new IllegalArgumentException(where + " track " + key + " needs [time, x, y, z] keys");
            times[i] = k.get(0).getAsFloat();
            if (times[i] < 0 || i > 0 && times[i] <= times[i - 1]) throw new IllegalArgumentException(where + " track " + key + " times must increase from 0");
            for (int c = 0; c < 3; c++) {
                float v = k.get(c + 1).getAsFloat();
                if (!Float.isFinite(v) || Math.abs(v) > limit) throw new IllegalArgumentException(where + " track " + key + " value out of range: " + v);
                values[i * 3 + c] = v;
            }
        }
        return new Track(times, values);
    }

    private static String text(JsonObject o, String key, String fallback) {
        return o.has(key) ? o.get(key).getAsString() : fallback;
    }

    private static float number(JsonObject o, String key, float fallback) {
        return o.has(key) ? o.get(key).getAsFloat() : fallback;
    }
}
