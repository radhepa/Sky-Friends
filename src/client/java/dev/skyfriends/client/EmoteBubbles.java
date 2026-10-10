package dev.skyfriends.client;

import dev.skyfriends.SkyFriends;
import dev.skyfriends.entity.Cirri;
import dev.skyfriends.life.Emote;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.Identifier;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;

/**
 * Cloud bubbles that pop above the Cirri, Tomodachi Life style (Village Friends' residents have the same): a "!"
 * when they spot you, a heart for a sweetheart, notes while they sing, "..." while they chat, "Zz" while they
 * sleep. Each bubble pops in with a little overshoot, bobs while it lasts, animates its symbol and pops out.
 * The sheet ({@code textures/gui/emotes.png}, made by {@code tools/gui/emotes.py}): three 32px bubble shapes on
 * the top row, then 16px symbols.
 */
public final class EmoteBubbles {
    public static final Identifier SHEET = SkyFriends.id("textures/gui/emotes.png");
    private static final int POP_IN = 5, POP_OUT = 4;

    /** A bubble on screen: what it says, when it started (client ticks) and how long it lasts. */
    public record Bubble(Emote emote, int start, int length) {
        public float age(float partial) {
            return clock - start + partial;
        }

        public boolean over() {
            return clock - start >= length;
        }
    }

    private record Pending(int entity, Emote emote, int at, int queued) {}

    private static final Map<Integer, Bubble> ACTIVE = new HashMap<>();
    private static final List<Pending> PENDING = new ArrayList<>();
    private static final Map<Integer, Integer> NEXT_SNORE = new HashMap<>();
    private static int clock;

    private EmoteBubbles() {}

    public static void clear() {
        ACTIVE.clear();
        PENDING.clear();
        NEXT_SNORE.clear();
    }

    public static Bubble get(int entityId) {
        return ACTIVE.get(entityId);
    }

    /** Pops a bubble above a Cirri after {@code delay} ticks, replacing whatever they were showing. */
    public static void show(int entityId, Emote emote, int delay) {
        if (emote == null) return;
        if (delay > 0) {
            PENDING.add(new Pending(entityId, emote, clock + delay, clock));
            return;
        }
        ACTIVE.put(entityId, new Bubble(emote, clock, length(emote)));
        var level = Minecraft.getInstance().level;
        var camera = Minecraft.getInstance().getCameraEntity();
        if (level != null && camera != null && level.getEntity(entityId) instanceof Cirri c && c.distanceToSqr(camera) < 24 * 24) {
            level.playLocalSound(c.getX(), c.getEyeY() + .6, c.getZ(), SoundEvents.BUBBLE_COLUMN_BUBBLE_POP, SoundSource.NEUTRAL, .35F, pitch(emote), false);
        }
    }

    /** An ambient bubble that only shows when the Cirri isn't already saying something. */
    public static void ambient(Cirri c, Emote emote) {
        var current = ACTIVE.get(c.getId());
        if (current == null || current.over()) show(c.getId(), emote, 0);
    }

    public static void tick(Minecraft client) {
        if (client.level == null) {
            clear();
            return;
        }
        if (client.isPaused()) return;
        clock++;
        for (var it = PENDING.iterator(); it.hasNext(); ) {
            var p = it.next();
            if (p.at > clock) continue;
            it.remove();
            // a delayed reply never talks over something the Cirri started saying since
            var current = ACTIVE.get(p.entity);
            if (current == null || current.start() <= p.queued || current.over()) show(p.entity, p.emote, 0);
        }
        ACTIVE.values().removeIf(Bubble::over);
        // sleepers drift off with a "Zz" every so often
        if (clock % 20 == 0) {
            var camera = client.getCameraEntity();
            for (var entity : client.level.entitiesForRendering()) {
                if (!(entity instanceof Cirri c) || !c.asleep() || camera == null || c.distanceToSqr(camera) > 20 * 20) continue;
                int next = NEXT_SNORE.getOrDefault(c.getId(), 0);
                if (clock >= next) {
                    ambient(c, Emote.SLEEP);
                    NEXT_SNORE.put(c.getId(), clock + 120 + c.getRandom().nextInt(100));
                }
            }
        }
    }

    public static int length(Emote emote) {
        return switch (emote) {
            case EXCLAIM -> 32;
            case QUESTION, ANGER, SPARKLE -> 42;
            case HEART, BLUSH, IDEA -> 52;
            case NOTE, SWEAT -> 46;
            case DOTS -> 60;
            case SLEEP, GLOOM -> 70;
        };
    }

    private static float pitch(Emote emote) {
        return switch (emote) {
            case EXCLAIM -> 1.35F;
            case QUESTION -> 1.2F;
            case HEART, BLUSH -> 1.45F;
            case NOTE, SPARKLE -> 1.55F;
            case ANGER -> .75F;
            case SWEAT, GLOOM -> .85F;
            case DOTS, SLEEP -> 1.0F;
            case IDEA -> 1.65F;
        };
    }

    /** Which bubble: 0 a round cloud (speech), 1 a thought cloud with little puffs, 2 a spiky storm cloud (a shout). */
    public static int shape(Emote emote) {
        return switch (emote) {
            case EXCLAIM, ANGER -> 2;
            case DOTS, IDEA, SLEEP, GLOOM -> 1;
            default -> 0;
        };
    }

    /** The symbol's cell in the sheet (16px cells from y=32), animated for the dots. */
    public static int symbol(Emote emote, float age) {
        return switch (emote) {
            case EXCLAIM -> 0;
            case QUESTION -> 1;
            case HEART -> 2;
            case NOTE -> 3;
            case ANGER -> 4;
            case SWEAT -> 5;
            case DOTS -> 6 + Math.min(2, (int) (age / 7) % 4);
            case SLEEP -> 9;
            case SPARKLE -> 10;
            case IDEA -> 11;
            case GLOOM -> 12;
            case BLUSH -> 13;
        };
    }

    /** Overall bubble scale: pops in with an overshoot, holds, then pops out. */
    public static float scale(Bubble b, float age) {
        if (age < POP_IN) {
            float t = age / POP_IN, c = 2.2F;
            return 1 + (c + 1) * (float) Math.pow(t - 1, 3) + c * (float) Math.pow(t - 1, 2);
        }
        float left = b.length() - age;
        if (left < POP_OUT) return Math.max(0, left / POP_OUT) * (1 + .15F * (1 - left / POP_OUT));
        return 1;
    }

    /** Gentle bob of the whole bubble, in pixels. */
    public static float bob(float age) {
        return Mth.sin(age * .18F) * .9F;
    }

    /** The symbol's own little performance: offset x/y in pixels, scale and rotation in degrees. */
    public static float[] symbolMotion(Emote emote, float age) {
        float x = 0, y = 0, s = 1, r = 0;
        switch (emote) {
            case EXCLAIM -> {
                if (age < 12) x = Mth.sin(age * 2.6F) * 1.2F * (1 - age / 12);
                s = 1 + .25F * Math.max(0, 1 - age / 6);
            }
            case QUESTION -> r = Mth.sin(age * .22F) * 14;
            case HEART -> s = 1 + .14F * Math.max(0, Mth.sin(age * .55F));
            case NOTE -> {
                x = Mth.sin(age * .25F) * 1.6F;
                r = Mth.sin(age * .25F) * 10;
            }
            case ANGER -> s = 1 + .2F * Math.abs(Mth.sin(age * .6F));
            case SWEAT -> y = Math.min(2.5F, age * .07F);
            case SLEEP -> {
                y = -(age % 35) * .08F;
                x = Mth.sin(age * .15F) * .8F;
            }
            case SPARKLE -> {
                s = .9F + .25F * Math.abs(Mth.sin(age * .35F));
                r = age * 3;
            }
            case IDEA -> s = 1 + .12F * Math.max(0, 1 - age / 8) + .04F * Mth.sin(age * .8F);
            case GLOOM -> y = Mth.sin(age * .12F) * .7F;
            case BLUSH -> {
                y = Mth.sin(age * .2F) * 1.1F;
                s = 1 + .06F * Mth.sin(age * .4F);
            }
            default -> { }
        }
        return new float[] {x, y, s, r};
    }
}
