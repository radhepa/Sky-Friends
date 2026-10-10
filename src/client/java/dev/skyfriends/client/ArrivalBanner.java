package dev.skyfriends.client;

import dev.skyfriends.SkyFriends;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.resources.sounds.SimpleSoundInstance;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Util;

/**
 * The title card shown when you come into a sky village (as Village Friends shows one for its villages): a small
 * spaced-out lead line, the village's name in large letters, a thin gold rule that draws outward from a centre
 * diamond, and who lives there. It fades in, holds, then fades out over a soft band of sky.
 */
public final class ArrivalBanner {
    private static final long FADE_IN = 700, HOLD = 3600, FADE_OUT = 1400, TOTAL = FADE_IN + HOLD + FADE_OUT;
    private static final int NAME = 0xF8FBFF, LEAD = 0xFFE6A8, RULE = 0xE9B548;
    private static String village, above, below;
    private static long start;

    private ArrivalBanner() {}

    public static void register() {
        HudElementRegistry.attachElementBefore(VanillaHudElements.TITLE_AND_SUBTITLE, SkyFriends.id("village_arrival"), ArrivalBanner::draw);
    }

    public static void show(String name, String lead, String sub) {
        village = name;
        above = lead;
        below = sub;
        start = Util.getMillis();
        var client = Minecraft.getInstance();
        client.getSoundManager().play(SimpleSoundInstance.forUI(SoundEvents.NOTE_BLOCK_CHIME.value(), 1.05F, .45F));
        client.getSoundManager().play(SimpleSoundInstance.forUI(SoundEvents.AMETHYST_BLOCK_CHIME, 1.4F, .6F));
    }

    public static void clear() {
        village = null;
    }

    /** The village whose card is on screen, or null. */
    public static String showing() {
        return village;
    }

    private static float ease(float t) {
        t = Math.clamp(t, 0F, 1F);
        return t * t * (3 - 2 * t);
    }

    private static void draw(GuiGraphicsExtractor g, DeltaTracker delta) {
        // a conversation has the screen: the card waits its turn (it carries on behind, fading on time)
        if (village == null || Minecraft.getInstance().gui.screen() instanceof dev.skyfriends.client.screen.TalkScreen) return;
        long age = Util.getMillis() - start;
        if (age >= TOTAL) {
            village = null;
            return;
        }
        float in = ease(age / (float) FADE_IN), out = 1 - ease((age - FADE_IN - HOLD) / (float) FADE_OUT);
        float alpha = Math.min(in, out);
        if (alpha <= .02F) return;
        var font = Minecraft.getInstance().font;
        int w = g.guiWidth(), h = g.guiHeight(), cx = w / 2;
        // the name is as large as fits: 4x on a roomy screen, never wider than 86% of it
        float scale = Math.clamp(w * .86F / Math.max(1, font.width(village)), 1.25F, 4F);
        float leadScale = Math.max(1F, scale * .38F);
        int nameH = Math.round(font.lineHeight * scale), leadH = Math.round(font.lineHeight * leadScale);
        boolean hasAbove = above != null && !above.isEmpty(), hasBelow = below != null && !below.isEmpty();
        int block = nameH + (hasAbove ? leadH + 6 : 0) + (hasBelow ? leadH + 6 : 0) + 12;
        int top = Math.round(h * .24F) - block / 2 + Math.round((1 - in) * 6);
        int bandTop = top - 14, bandBottom = top + block + 12, mid = (bandTop + bandBottom) / 2;
        int shade = Math.round(alpha * 0x66);
        g.fillGradient(0, bandTop, w, mid, 0, shade << 24 | 0x0B2440);
        g.fillGradient(0, mid, w, bandBottom, shade << 24 | 0x0B2440, 0);
        int y = top;
        if (hasAbove) {
            spaced(g, font, above.toUpperCase(), cx, y, leadScale, argb(alpha, LEAD));
            y += leadH + 6;
        }
        g.pose().pushMatrix();
        g.pose().translate(cx, y);
        g.pose().scale(scale, scale);
        g.centeredText(font, village, 0, 0, argb(alpha, NAME));
        g.pose().popMatrix();
        y += nameH + 6;
        rule(g, cx, y, Math.round(Math.min(w * .9F, font.width(village) * scale + 40) / 2 * ease((age - 150) / 900F)), alpha);
        y += 6;
        if (hasBelow) spaced(g, font, below.toUpperCase(), cx, y, leadScale, argb(alpha, LEAD));
    }

    /** Small capitals with extra letter spacing, centred on {@code cx}. */
    private static void spaced(GuiGraphicsExtractor g, Font font, String text, int cx, int y, float scale, int color) {
        int gap = 2, width = 0;
        for (int i = 0; i < text.length(); i++) width += font.width(String.valueOf(text.charAt(i))) + (i + 1 < text.length() ? gap : 0);
        g.pose().pushMatrix();
        g.pose().translate(cx, y);
        g.pose().scale(scale, scale);
        int x = -width / 2;
        for (int i = 0; i < text.length(); i++) {
            String c = String.valueOf(text.charAt(i));
            g.text(font, c, x, 0, color, true);
            x += font.width(c) + gap;
        }
        g.pose().popMatrix();
    }

    /** A thin gold rule each side of a small diamond, fading towards its ends. */
    private static void rule(GuiGraphicsExtractor g, int cx, int y, int half, float alpha) {
        int color = argb(alpha, RULE), clear = RULE & 0xFFFFFF;
        if (half > 6) {
            horizontal(g, cx - half, cx - 6, y, clear, color);
            horizontal(g, cx + 6, cx + half, y, color, clear);
        }
        for (int i = 0; i <= 3; i++) g.fill(cx - i, y - 3 + i, cx + i + 1, y - 2 + i, color);
        for (int i = 0; i < 3; i++) g.fill(cx - 2 + i, y + 1 + i, cx + 3 - i, y + 2 + i, color);
    }

    /** Left-to-right colour fade drawn as short segments (GUI gradients only run top to bottom). */
    private static void horizontal(GuiGraphicsExtractor g, int x0, int x1, int y, int from, int to) {
        int steps = Math.max(1, (x1 - x0) / 4);
        for (int i = 0; i < steps; i++) {
            float t = (i + .5F) / steps;
            int a = Math.round((from >>> 24) + ((to >>> 24) - (from >>> 24)) * t);
            int sx = x0 + (x1 - x0) * i / steps, ex = x0 + (x1 - x0) * (i + 1) / steps;
            g.fill(sx, y, ex, y + 1, a << 24 | (to | from) & 0xFFFFFF);
        }
    }

    private static int argb(float alpha, int rgb) {
        return Math.round(alpha * 255) << 24 | rgb;
    }
}
