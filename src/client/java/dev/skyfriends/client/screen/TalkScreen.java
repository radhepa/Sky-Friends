package dev.skyfriends.client.screen;

import dev.skyfriends.SkyBlocks;
import dev.skyfriends.SkyItems;
import dev.skyfriends.client.EmoteBubbles;
import dev.skyfriends.client.render.CirriRenderer;
import dev.skyfriends.life.Emote;
import dev.skyfriends.talk.TalkActionPayload;
import dev.skyfriends.talk.TalkPayload;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.client.resources.sounds.SimpleSoundInstance;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/**
 * The conversation window: the Village Friends layout in the colours of a clear sky. The Cirri stays in view in
 * the world; a dialogue box with their portrait, their mood bubble and a name ribbon sits at the bottom, the line
 * typing out in their voice (a flute's breath, higher for children); replies float as numbered bubbles on the
 * right; a dock offers a greeting, a gift, the Skymerchant's wares and farewell; and a card shows your friendship
 * as ten little clouds filling with gold. Tabs on the box switch between Talk, their Story (marked when there's
 * something to do there) and your Journal (shown whole, to scroll through; Tab cycles them). If they turn away,
 * the replies close and only the Journal still opens.
 */
public final class TalkScreen extends Screen {
    static final int PAPER = 0xFFF8FBFF, PAPER_SHADE = 0xFFDCE8F4, EDGE = 0xFF34587C, EDGE_LIGHT = 0xFF9DBCD9, INK = 0xFF223547,
            MUTED = 0xFF6D8298, STATUS = 0xFFA87522, STATUS_NEW = 0xFF8C5E10, GOLD = 0xFFE9B548, GOLD_LIGHT = 0xFFFFE7A8, EMPTY = 0xFFD3E1EE;
    /** Level badge colours by fifths of the way to 10: from pale sky to dawn gold. */
    static final int[] TIERS = {0xFF8EA4BA, 0xFF5E8DBA, 0xFF4F7FC8, 0xFFC9925A, 0xFFE0A93A};
    private static final float CHARS_PER_SECOND = 36F;
    private static final int SPACE_KEY = 32, KEY_1 = 49, TAB_KEY = 258, UP_KEY = 265, DOWN_KEY = 264, LINE = 10;
    private static final String[] TABS = {"talk", "story", "journal"}, TAB_LABELS = {"Talk", "Story", "Journal"};

    private TalkPayload data;
    private final List<Button> actions = new ArrayList<>();
    private final List<TabButton> tabs = new ArrayList<>();
    private boolean waiting, closing;
    private int waitTicks, ticks;
    private int boxX, boxY, boxW, boxH, textX, textW, portraitX, portraitY, portraitW, portraitH, cardX, cardY, cardW, cardH;
    private int dialogueScroll;
    private String lastDialogue;
    private List<String> typeLines = List.of();
    private int[] lineStarts = new int[0];
    private String typeKey = "", typeFlat = "";
    private int shown, sinceBlip;
    private float typeBudget, typePause;
    private long lastFrameNanos;
    private boolean popPending = true, wholeLines;
    private int levelUpAt = -1000, statusAt, emoteAt;
    private Emote emote;

    public TalkScreen(TalkPayload data) {
        super(Component.literal(data.name()));
        this.data = data;
        this.lastDialogue = data.dialogue();
        this.emote = Emote.parse(data.emote());
    }

    public boolean matches(TalkPayload next) {
        return data.id().equals(next.id());
    }

    public TalkPayload data() {
        return data;
    }

    /** Whether the current line has been laid out and has finished typing out. */
    public boolean doneTyping() {
        return typeKey.startsWith(data.dialogue() + '|') && !typing();
    }

    /** Show every line whole instead of typing it out (tests, where frames are few and far between). */
    public void showWholeLines() {
        wholeLines = true;
        finishLine();
    }

    public void update(TalkPayload next) {
        if (!lastDialogue.equals(next.dialogue())) {
            dialogueScroll = 0;
            lastDialogue = next.dialogue();
            restartTyping();
        }
        if (next.levelUp()) {
            levelUpAt = ticks;
            playUi(SoundEvents.AMETHYST_BLOCK_CHIME, 1.6F, 0.8F);
        }
        Emote mood = Emote.parse(next.emote());
        if (mood != null) {
            emote = mood;
            emoteAt = ticks;
        }
        if (!next.status().equals(data.status())) statusAt = ticks;
        data = next;
        waiting = false;
        waitTicks = 0;
        rebuildWidgets();
        triggerImmediateNarration(false);
    }

    /** The Journal is your own notes: shown whole, not spoken. */
    private boolean instant() {
        return data.tab().equals("journal");
    }

    // -- typing ------------------------------------------------------------------------------------

    private void restartTyping() {
        shown = 0;
        typeBudget = 0;
        typePause = 0;
        sinceBlip = 0;
        popPending = true;
    }

    /** True while their line is still typing out: they gesture as they speak. */
    public boolean speaking() {
        return typing();
    }

    private boolean typing() {
        return shown < typeFlat.length();
    }

    private void finishLine() {
        if (typing()) shown = typeFlat.length();
    }

    private void playUi(SoundEvent sound, float pitch, float volume) {
        if (minecraft != null) minecraft.getSoundManager().play(SimpleSoundInstance.forUI(sound, pitch, volume));
    }

    /** One typing blip in the speaker's voice: a breath of flute. */
    private void blip(char c) {
        float wobble = Character.toLowerCase(c) % 7 * 0.035F;
        switch (data.voice()) {
            case "man" -> playUi(SoundEvents.NOTE_BLOCK_FLUTE.value(), 0.85F + wobble, 0.22F);
            case "child" -> playUi(SoundEvents.NOTE_BLOCK_FLUTE.value(), 1.6F + wobble, 0.2F);
            default -> playUi(SoundEvents.NOTE_BLOCK_FLUTE.value(), 1.18F + wobble, 0.22F);
        }
    }

    private void layoutTyping(int wrapWidth) {
        String key = data.dialogue() + '|' + wrapWidth;
        if (key.equals(typeKey)) return;
        typeKey = key;
        typeLines = font.splitIgnoringLanguage(Component.literal(data.dialogue()), wrapWidth).stream().map(t -> t.getString()).toList();
        lineStarts = new int[typeLines.size()];
        int total = 0;
        for (int i = 0; i < lineStarts.length; i++) {
            lineStarts[i] = total;
            total += typeLines.get(i).length();
        }
        typeFlat = String.join("", typeLines);
        shown = wholeLines || instant() ? total : Math.min(shown, total);
    }

    private void advanceTyping() {
        long now = System.nanoTime();
        float dt = lastFrameNanos == 0 ? 0F : Math.min(0.25F, (now - lastFrameNanos) / 1.0E9F);
        lastFrameNanos = now;
        if (instant()) {
            popPending = false;
            finishLine();
            return;
        }
        if (popPending) {
            popPending = false;
            playUi(SoundEvents.NOTE_BLOCK_CHIME.value(), 1.5F, 0.18F);
        }
        if (!typing()) return;
        typeBudget += dt;
        float cost = 1F / CHARS_PER_SECOND;
        while (typeBudget > 0 && typing()) {
            if (typePause > 0) {
                float used = Math.min(typePause, typeBudget);
                typePause -= used;
                typeBudget -= used;
                continue;
            }
            if (typeBudget < cost) break;
            typeBudget -= cost;
            char c = typeFlat.charAt(shown++);
            if (!Character.isWhitespace(c) && c != '*' && ++sinceBlip >= 2) {
                sinceBlip = 0;
                blip(c);
            }
            if (".!?".indexOf(c) >= 0) typePause = 0.18F;
            else if (",;:".indexOf(c) >= 0) typePause = 0.08F;
        }
    }

    // -- layout ------------------------------------------------------------------------------------

    @Override
    protected void init() {
        actions.clear();
        tabs.clear();
        int dockH = 20, bottom = height - 8 - dockH - 5;
        boxW = Math.min(430, width - 16);
        boxX = (width - boxW) / 2;
        portraitW = 64;
        textX = boxX + portraitW + 18;
        textW = boxX + boxW - 12 - textX;
        int count = data.choices().size(), row = 18, baseH = 64;
        int columns = count * row > bottom - baseH - 30 ? 2 : 1;
        int rows = (count + columns - 1) / columns;
        int replyW = columns == 1 ? Math.clamp(width * 2 / 5, 130, 196) : Math.clamp((boxW - 12) / 2 - 2, 100, 176);
        // a story or a Journal page wants a taller box, as far as the replies above leave room
        int lines = font.splitIgnoringLanguage(Component.literal(data.dialogue()), textW).size();
        int wanted = Math.clamp(lines, 4, instant() ? 15 : 8) * LINE + 24;
        boxH = Math.max(baseH, Math.min(wanted, bottom - 30 - rows * row - 12));
        boxY = bottom - boxH;
        portraitH = Math.min(boxH + 30, 118);
        portraitX = boxX + 7;
        portraitY = boxY + boxH - 7 - portraitH;
        cardX = 8;
        cardY = 8;
        cardW = Math.min(170, width / 2 - 12);
        cardH = 50;
        int replyRight = Math.max(boxX + boxW, width - 10), replyBottom = boxY - 18;
        for (int i = 0; i < count; i++) {
            var choice = data.choices().get(i);
            int column = columns == 1 ? 0 : i % 2, r = columns == 1 ? i : i / 2;
            int x = replyRight - (columns - column) * (replyW + 4) + 4, y = replyBottom - (rows - r) * row;
            var button = new ReplyButton(x, y, replyW, row - 3, i + 1, choice.label(), pressed -> send(choice.id()));
            button.active = !waiting && choice.enabled() && (!data.left() || choice.id().startsWith("journal_"));
            if (!choice.hint().isEmpty()) button.setTooltip(Tooltip.create(Component.literal(choice.hint())));
            actions.add(button);
            addRenderableWidget(button);
        }
        // the tabs, on the top edge of the box at the right
        int tabH = 13, tabGap = 2, tabsW = -tabGap;
        int[] tabW = new int[TABS.length];
        for (int i = 0; i < TABS.length; i++) tabsW += (tabW[i] = font.width(TAB_LABELS[i]) + 14) + tabGap;
        boolean shortTabs = tabsW > boxW - portraitW - 120;
        if (shortTabs) {
            tabsW = -tabGap;
            for (int i = 0; i < TABS.length; i++) tabsW += (tabW[i] = font.width(TAB_LABELS[i].substring(0, 1)) + 12) + tabGap;
        }
        int tx = boxX + boxW - 6 - tabsW;
        for (int i = 0; i < TABS.length; i++) {
            String tab = TABS[i];
            String label = shortTabs ? TAB_LABELS[i].substring(0, 1) : TAB_LABELS[i];
            var button = new TabButton(tx, boxY - tabH + 1, tabW[i], tabH, label, tab.equals(data.tab()),
                    tab.equals("story") && data.storyAlert(), pressed -> send("tab_" + tab));
            button.setTooltip(Tooltip.create(Component.literal(switch (tab) {
                case "story" -> "Story: what's on their mind";
                case "journal" -> "Journal: your memories with them, what you know of them, their story so far";
                default -> "Talk: chat, ask about things, hear the news";
            } + " (Tab)")));
            button.active = !waiting && (!data.left() || tab.equals("journal"));
            tabs.add(button);
            addRenderableWidget(button);
            tx += tabW[i] + tabGap;
        }
        // the dock: a greeting, a gift, the Skymerchant's wares, farewell
        var player = Minecraft.getInstance().player;
        ItemStack held = player == null ? ItemStack.EMPTY : player.getMainHandItem();
        List<String> ids = new ArrayList<>(List.of("talk", "gift"));
        if (data.merchant()) ids.add("trade");
        ids.add("goodbye");
        boolean wide = width >= 360 + (data.merchant() ? 80 : 0);
        int each = wide ? 78 : 22, gap = 4;
        int n = ids.size(), total = n * each + (n - 1) * gap + 8, x = (width - total) / 2, y = height - 8 - dockH;
        for (int i = 0; i < n; i++) {
            String id = ids.get(i);
            if (id.equals("goodbye")) x += 8;
            String label = switch (id) {
                case "talk" -> "Greet";
                case "gift" -> "Gift";
                case "trade" -> "Trade";
                default -> "Farewell";
            };
            ItemStack icon = switch (id) {
                case "talk" -> new ItemStack(Items.FEATHER);
                case "gift" -> held.isEmpty() ? new ItemStack(SkyItems.SKY_PEACH) : held.copyWithCount(1);
                case "trade" -> new ItemStack(Items.EMERALD);
                default -> new ItemStack(SkyBlocks.CLOUD);
            };
            var button = new DockButton(x, y, each, dockH, label, icon, wide, id.equals("gift") ? data.giftsLeft() : -1,
                    pressed -> {
                        if (id.equals("goodbye")) onClose();
                        else send(id);
                    });
            button.setTooltip(Tooltip.create(Component.literal(tooltip(id, held))));
            if (id.equals("gift")) button.active = !waiting && !data.left() && data.giftsLeft() > 0;
            else if (!id.equals("goodbye")) button.active = !waiting && !data.left();
            if (!id.equals("goodbye")) actions.add(button);
            addRenderableWidget(button);
            x += each + gap;
        }
    }

    private String tooltip(String id, ItemStack held) {
        return switch (id) {
            case "talk" -> "Greet: say hello again";
            case "gift" -> "Gift: give " + (held.isEmpty() ? "what you hold in your main hand" : "one " + held.getHoverName().getString())
                    + ". " + data.giftsLeft() + " left today.";
            case "trade" -> "Trade: see the Skymerchant's wares";
            default -> "Farewell (Esc)";
        };
    }

    private void send(String action) {
        if (waiting || !ClientPlayNetworking.canSend(TalkActionPayload.TYPE)) return;
        ClientPlayNetworking.send(new TalkActionPayload(data.entityId(), data.id(), action));
        waiting = true;
        waitTicks = 0;
        actions.forEach(button -> button.active = false);
        tabs.forEach(button -> button.active = false);
    }

    /** Presses a reply or dock button by id, as a click would (for tests). */
    public void press(String action) {
        send(action);
    }

    // -- input -------------------------------------------------------------------------------------

    @Override
    public boolean keyPressed(KeyEvent event) {
        if (event.key() == SPACE_KEY && typing()) {
            finishLine();
            return true;
        }
        if (event.key() == TAB_KEY && !waiting) {
            int at = List.of(TABS).indexOf(data.tab());
            for (int step = 1; step < TABS.length; step++) {
                String next = TABS[Math.floorMod(at + (event.hasShiftDown() ? -step : step), TABS.length)];
                if (!data.left() || next.equals("journal")) {
                    send("tab_" + next);
                    break;
                }
            }
            return true;
        }
        if ((event.key() == UP_KEY || event.key() == DOWN_KEY) && typeLines.size() > visibleLines()) {
            dialogueScroll = Math.clamp(dialogueScroll + (event.key() == DOWN_KEY ? 1 : -1), 0, typeLines.size() - visibleLines());
            return true;
        }
        int index = event.key() - KEY_1;
        if (index >= 0 && index < data.choices().size() && !waiting) {
            var choice = data.choices().get(index);
            if (choice.enabled() && (!data.left() || choice.id().startsWith("journal_"))) {
                send(choice.id());
                return true;
            }
        }
        return super.keyPressed(event);
    }

    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        if (typing() && event.x() >= boxX && event.x() < boxX + boxW && event.y() >= boxY && event.y() < boxY + boxH) {
            finishLine();
            return true;
        }
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean mouseScrolled(double x, double y, double horizontal, double vertical) {
        if (x >= boxX && x < boxX + boxW && y >= boxY && y < boxY + boxH) {
            dialogueScroll = Math.clamp(dialogueScroll - (int) Math.signum(vertical), 0, Math.max(0, typeLines.size() - visibleLines()));
            return true;
        }
        return super.mouseScrolled(x, y, horizontal, vertical);
    }

    @Override
    public void tick() {
        ticks++;
        if (minecraft.player == null || minecraft.level == null) {
            onClose();
            return;
        }
        var who = minecraft.level.getEntity(data.entityId());
        // once they've cut it short the window stays, so you can read what they said (and your Journal)
        // a Cirri called from afar has a few seconds to fly over before distance ends the conversation
        double reach = data.left() || ticks < 100 ? 32 : 12;
        if (who == null || !who.isAlive() || !who.getUUID().equals(data.id()) || minecraft.player.distanceToSqr(who) > reach * reach || !minecraft.player.isAlive()) {
            onClose();
            return;
        }
        if (waiting && ++waitTicks > 100) {
            waiting = false;
            rebuildWidgets();
        }
    }

    /** Tell the Cirri the conversation is over, however the window closed. */
    @Override
    public void removed() {
        if (!closing && ClientPlayNetworking.canSend(TalkActionPayload.TYPE)) {
            closing = true;
            ClientPlayNetworking.send(new TalkActionPayload(data.entityId(), data.id(), "goodbye"));
        }
        super.removed();
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }

    @Override
    public boolean isInGameUi() {
        return true;
    }

    @Override
    public Component getNarrationMessage() {
        return Component.literal(data.name() + ", " + data.title() + ". Friendship " + data.level() + ", " + data.levelName() + ". "
                + TAB_LABELS[Math.max(0, List.of(TABS).indexOf(data.tab()))] + ". " + data.dialogue() + " " + data.status());
    }

    // -- drawing -----------------------------------------------------------------------------------

    /** No blur: the Cirri stays visible in the world; a soft blue shade under the box lifts the text. */
    @Override
    public void extractBackground(GuiGraphicsExtractor g, int mouseX, int mouseY, float delta) {
        g.fillGradient(0, height / 2, width, height, 0x00000000, 0x5A0B1E33);
    }

    private int visibleLines() {
        return Math.max(1, (boxH - 24) / LINE);
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float delta) {
        float now = ticks + delta;
        drawCard(g, mouseX, mouseY);
        panel(g, boxX, boxY, boxW, boxH, PAPER);
        frame(g, portraitX - 2, portraitY - 2, portraitW + 4, portraitH + 4);
        // a little sky behind them: blue at the top, cloud-white below
        g.fillGradient(portraitX, portraitY, portraitX + portraitW, portraitY + portraitH, 0xFF8FC1EA, 0xFFEAF4FC);
        if (minecraft.level != null && minecraft.level.getEntity(data.entityId()) instanceof LivingEntity who) {
            // frame the head and shoulders whatever their height
            // head and shoulders: a Cirri's model stands a little taller than its hitbox, its eyes at about 1.08 times the
            // hitbox's eye height; the portrait shows a block (less for a child), the eyes a third of the way down
            float h = who.getBbHeight(), eye = who.getEyeHeight() * 1.08F;
            float span = who.isBaby() ? 0.8F : 1.0F;
            int size = (int) (portraitH / span);
            float yOffset = eye - span * 0.12F - h / 2.0F;
            CirriRenderer.portrait = true;
            try {
                InventoryScreen.extractEntityInInventoryFollowsMouse(g, portraitX, portraitY, portraitX + portraitW, portraitY + portraitH,
                        size, yOffset, portraitX + portraitW / 2F - 10, portraitY + portraitH / 3F, who);
            } finally {
                CirriRenderer.portrait = false;
            }
        }
        drawEmote(g, portraitX + portraitW - 8, portraitY - 6, now);
        drawRibbon(g, mouseX, mouseY);
        layoutTyping(textW);
        advanceTyping();
        int visible = visibleLines();
        if (typing()) {
            int lastLine = 0;
            for (int i = 0; i < lineStarts.length; i++) if (lineStarts[i] < shown) lastLine = i;
            dialogueScroll = Math.max(dialogueScroll, lastLine - visible + 1);
        }
        dialogueScroll = Math.clamp(dialogueScroll, 0, Math.max(0, typeLines.size() - visible));
        int top = boxY + 9;
        g.enableScissor(textX, top - 1, textX + textW, top + visible * LINE);
        for (int line = dialogueScroll, y = top; line < Math.min(typeLines.size(), dialogueScroll + visible); line++, y += LINE) {
            int chars = Math.min(typeLines.get(line).length(), shown - lineStarts[line]);
            if (chars <= 0) break;
            drawLine(g, typeLines.get(line).substring(0, chars), textX, y);
        }
        g.disableScissor();
        if (typeLines.size() > visible) scrollbar(g, top, visible);
        int statusY = boxY + boxH - 13;
        g.fill(textX, statusY - 3, textX + textW, statusY - 2, PAPER_SHADE);
        String status = waiting ? "Listening..." : data.status();
        g.text(font, font.plainSubstrByWidth(status, textW - 12), textX, statusY, now - statusAt < 40 ? STATUS_NEW : STATUS, false);
        if (mouseX >= textX && mouseX < textX + textW && mouseY >= statusY - 2 && mouseY < statusY + 9 && font.width(status) > textW - 12)
            g.setTooltipForNextFrame(Component.literal(status), mouseX, mouseY);
        if (!typing() && !waiting) {
            int bounce = (int) (Math.abs(Mth.sin(now * .25F)) * 2);
            int ax = boxX + boxW - 14, ay = statusY + 1 + bounce;
            for (int i = 0; i < 4; i++) g.fill(ax + i, ay + i, ax + 7 - i, ay + i + 1, EDGE_LIGHT);
        }
        super.extractRenderState(g, mouseX, mouseY, delta);
        drawLevelUp(g, now);
    }

    /** Their mood bubble, popping in beside their portrait (the same bubbles as over their head in the world). */
    private void drawEmote(GuiGraphicsExtractor g, int x, int y, float now) {
        if (emote == null) return;
        float age = now - emoteAt;
        float life = EmoteBubbles.length(emote) + 40;
        if (age > life && !waiting) return;
        var bubble = new EmoteBubbles.Bubble(emote, 0, (int) life);
        float scale = waiting ? Math.min(1, age / 5F) : EmoteBubbles.scale(bubble, age);
        if (scale <= .01F) return;
        var pose = g.pose();
        pose.pushMatrix();
        pose.translate(x + 12, y + 22 + EmoteBubbles.bob(age));
        pose.scale(scale, scale);
        g.blit(RenderPipelines.GUI_TEXTURED, EmoteBubbles.SHEET, -12, -24, EmoteBubbles.shape(emote) * 32, 0, 24, 24, 32, 32, 128, 128);
        float[] motion = EmoteBubbles.symbolMotion(emote, age);
        int symbol = EmoteBubbles.symbol(emote, age);
        pose.translate(motion[0] * .75F, -14.5F + motion[1] * .75F);
        pose.rotate(motion[3] * Mth.DEG_TO_RAD);
        pose.scale(motion[2], motion[2]);
        g.blit(RenderPipelines.GUI_TEXTURED, EmoteBubbles.SHEET, -6, -6, symbol % 8 * 16, 32 + symbol / 8 * 16, 12, 12, 16, 16, 128, 128);
        pose.popMatrix();
    }

    /** A line of the box; Journal pages mark headings (# ), dates (Day N:) and steps done or not (✓, ○). */
    private void drawLine(GuiGraphicsExtractor g, String text, int x, int y) {
        if (!instant()) {
            g.text(font, text, x, y, INK, false);
            return;
        }
        if (text.startsWith("# ")) {
            g.text(font, text.substring(2), x, y, EDGE, false);
            g.fill(x, y + 9, x + Math.min(textW - 4, font.width(text.substring(2)) + 6), y + 10, GOLD);
            return;
        }
        int colon = text.indexOf(':');
        String lead = text.startsWith("✓ ") || text.startsWith("○ ") ? text.substring(0, 2)
                : text.startsWith("Day ") && colon > 4 && colon < 10 ? text.substring(0, colon + 1) : "";
        if (lead.isEmpty()) {
            g.text(font, text, x, y, INK, false);
            return;
        }
        g.text(font, lead, x, y, lead.startsWith("✓") ? STATUS : MUTED, false);
        g.text(font, text.substring(lead.length()), x + font.width(lead), y, INK, false);
    }

    private void drawCard(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        panel(g, cardX, cardY, cardW, cardH, PAPER);
        int tier = TIERS[Math.clamp(data.level() / 2 - (data.level() == 10 ? 1 : 0), 0, 4)];
        String badge = "Lv. " + data.level();
        int badgeW = font.width(badge) + 10;
        pill(g, cardX + 6, cardY + 6, badgeW, 12, tier);
        g.text(font, badge, cardX + 11, cardY + 8, 0xFFFFFFFF, true);
        g.text(font, font.plainSubstrByWidth(data.levelName(), cardW - badgeW - 18), cardX + badgeW + 11, cardY + 8, INK, false);
        int floor = data.levelFloor(), next = Math.max(floor + 1, data.nextThreshold());
        float progress = data.level() >= 10 ? 0 : Math.clamp((data.points() - floor) / (float) (next - floor), 0, 1);
        int hx = cardX + 6, hy = cardY + 23;
        for (int i = 0; i < 10; i++) {
            float fill = i < data.level() ? 1 : i == data.level() ? progress : 0;
            cloud(g, hx + i * 10, hy, fill);
        }
        String goal = data.level() >= 10 ? "One sky: as close as friends can be." : (next - data.points()) + " more to the next cloud";
        g.text(font, font.plainSubstrByWidth(goal, cardW - 12), cardX + 6, cardY + 35, MUTED, false);
        if (mouseX >= cardX && mouseX < cardX + cardW && mouseY >= cardY && mouseY < cardY + cardH) {
            var lines = new ArrayList<Component>();
            lines.add(Component.literal("Friendship " + data.level() + " of 10: " + data.levelName()));
            lines.add(Component.literal(data.points() + " friendship with " + data.name()));
            g.setComponentTooltipForNextFrame(font, lines, mouseX, mouseY);
        }
    }

    private int ribbonColour() {
        return switch (data.voice()) {
            case "man" -> 0xFF3E6E9A;
            case "child" -> 0xFF6FA6D2;
            default -> 0xFFB06A86;
        };
    }

    private void drawRibbon(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        int color = ribbonColour();
        String name = font.plainSubstrByWidth(data.name(), boxW - portraitW - 40);
        int w = font.width(name) + 14, x = textX - 4, y = boxY - 12;
        g.fill(x + 1, y + 1, x + w + 1, y + 14, 0x55000000);
        g.fill(x, y, x + w, y + 13, color);
        g.fill(x, y + 11, x + w, y + 13, darker(color));
        g.fill(x - 1, y + 1, x, y + 12, darker(color));
        g.fill(x + w, y + 1, x + w + 1, y + 12, darker(color));
        g.fill(x + 2, y + 1, x + w - 2, y + 2, GOLD_LIGHT);
        g.text(font, name, x + 7, y + 3, 0xFFFFFFFF, true);
        String subtitle = data.title() + " · " + data.home();
        int tabsLeft = tabs.isEmpty() ? boxX + boxW : tabs.getFirst().getX();
        int room = tabsLeft - (x + w + 6) - 6;
        // the job and home if they fit, else the job alone; never cut off mid-word
        String fits = font.width(subtitle) <= room ? subtitle : font.width(data.title()) <= room ? data.title() : "";
        if (!fits.isEmpty()) g.text(font, fits, x + w + 6, y + 3, 0xFFF8FBFF, true);
        if (mouseX >= x && mouseX < x + w && mouseY >= y && mouseY < y + 13) g.setTooltipForNextFrame(Component.literal(subtitle), mouseX, mouseY);
    }

    /** A banner that drops in when you grow closer, with clouds drifting round it. */
    private void drawLevelUp(GuiGraphicsExtractor g, float now) {
        float age = now - levelUpAt;
        if (age < 0 || age > 80) return;
        float drop = age < 8 ? 1 - (float) Math.pow(1 - age / 8, 3) : age > 70 ? 1 - (age - 70) / 10 : 1;
        String title = data.levelName() + "!";
        String sub = "Friendship " + data.level() + " of 10";
        int w = Math.max(font.width(title), font.width(sub)) + 40, h = 30, x = (width - w) / 2, y = (int) (-h + (h + 10) * drop);
        panel(g, x, y, w, h, 0xFFFFFDF4);
        g.centeredText(font, title, width / 2, y + 6, 0xFFC08A1E);
        g.centeredText(font, sub, width / 2, y + 17, INK);
        for (int i = 0; i < 6; i++) {
            float a = age * .12F + i * 1.047F;
            int sx = (int) (width / 2 + Mth.cos(a) * (w / 2F + 6)), sy = (int) (y + h / 2 + Mth.sin(a) * (h / 2F + 5));
            cloud(g, sx - 4, sy - 3, 1);
        }
    }

    private void scrollbar(GuiGraphicsExtractor g, int top, int visible) {
        int trackX = boxX + boxW - 6, trackH = visible * LINE;
        g.fill(trackX, top, trackX + 2, top + trackH, PAPER_SHADE);
        int thumb = Math.max(6, trackH * visible / typeLines.size());
        int offset = (trackH - thumb) * dialogueScroll / Math.max(1, typeLines.size() - visible);
        g.fill(trackX, top + offset, trackX + 2, top + offset + thumb, EDGE_LIGHT);
    }

    // -- drawing helpers ---------------------------------------------------------------------------

    /** A rounded cloud-white panel with a deep sky-blue edge, a thread of gold along the top and a soft drop shadow. */
    static void panel(GuiGraphicsExtractor g, int x, int y, int w, int h, int paper) {
        g.fill(x + 1, y + h, x + w - 1, y + h + 2, 0x55000000);
        g.fill(x + 1, y, x + w - 1, y + h, EDGE);
        g.fill(x, y + 1, x + w, y + h - 1, EDGE);
        g.fill(x + 2, y + 1, x + w - 2, y + h - 1, paper);
        g.fill(x + 1, y + 2, x + w - 1, y + h - 2, paper);
        g.fill(x + 2, y + h - 3, x + w - 2, y + h - 2, PAPER_SHADE);
        g.fill(x + 2, y + 2, x + w - 2, y + 3, GOLD_LIGHT);
    }

    static void frame(GuiGraphicsExtractor g, int x, int y, int w, int h) {
        g.fill(x + 1, y + h, x + w + 1, y + h + 2, 0x55000000);
        g.fill(x, y, x + w, y + h, EDGE);
        g.fill(x + 1, y + 1, x + w - 1, y + h - 1, GOLD);
    }

    static void pill(GuiGraphicsExtractor g, int x, int y, int w, int h, int color) {
        g.fill(x + 1, y, x + w - 1, y + h, color);
        g.fill(x, y + 1, x + w, y + h - 1, color);
        g.fill(x + 1, y + h - 2, x + w - 1, y + h - 1, darker(color));
    }

    static int darker(int color) {
        int r = (color >> 16 & 255) * 3 / 4, gr = (color >> 8 & 255) * 3 / 4, b = (color & 255) * 3 / 4;
        return 0xFF000000 | r << 16 | gr << 8 | b;
    }

    /** An 8x6 little cloud, filled with gold from the left by {@code fill} (0 to 1). */
    static void cloud(GuiGraphicsExtractor g, int x, int y, float fill) {
        int[] masks = {0b00111000, 0b01111100, 0b11111110, 0b11111111, 0b11111111, 0b01111110};
        for (int row = 0; row < masks.length; row++) for (int col = 0; col < 8; col++) {
            if ((masks[row] & (1 << (7 - col))) == 0) continue;
            boolean filled = col < Math.round(Math.clamp(fill, 0, 1) * 8);
            int c = filled ? row <= 2 ? GOLD_LIGHT : GOLD : row <= 1 ? 0xFFEAF2FA : EMPTY;
            if (row == masks.length - 1 && (masks[row] & (1 << (7 - col))) != 0) c = filled ? darker(GOLD) : 0xFFC2D3E3;
            g.fill(x + col, y + row, x + col + 1, y + row + 1, c);
        }
    }

    /** A numbered reply bubble. */
    static final class ReplyButton extends Button {
        private final int number;

        ReplyButton(int x, int y, int w, int h, int number, String label, OnPress action) {
            super(x, y, w, h, Component.literal(label), action, DEFAULT_NARRATION);
            this.number = number;
        }

        @Override
        protected void extractContents(GuiGraphicsExtractor g, int mouseX, int mouseY, float delta) {
            boolean hover = active && isHoveredOrFocused();
            int x = getX() + (hover ? -2 : 0), y = getY(), w = getWidth(), h = getHeight();
            int paper = !active ? 0xFFDDE5EE : hover ? 0xFFFFFFFF : 0xFFF4F8FD;
            int edge = active ? EDGE : 0xFF98A9BA;
            g.fill(x + 2, y + h, x + w - 2, y + h + 1, 0x44000000);
            g.fill(x + 2, y, x + w - 2, y + h, edge);
            g.fill(x + 1, y + 1, x + w - 1, y + h - 1, edge);
            g.fill(x + 2, y + 1, x + w - 2, y + h - 1, paper);
            g.fill(x + 1, y + 2, x + w - 1, y + h - 2, paper);
            int badge = active ? hover ? GOLD : EDGE_LIGHT : 0xFFB3C1CE;
            g.fill(x + 3, y + 2, x + 12, y + h - 2, badge);
            var font = Minecraft.getInstance().font;
            g.centeredText(font, String.valueOf(number), x + 8, y + (h - 8) / 2, 0xFFFFFFFF);
            String label = font.plainSubstrByWidth(getMessage().getString(), w - 20);
            g.text(font, label, x + 16, y + (h - 8) / 2, active ? INK : 0xFF8E9DAC, false);
        }
    }

    /** A paper tab on the top edge of the dialogue box; the open one joins the box. */
    static final class TabButton extends Button {
        private final boolean selected, alert;

        TabButton(int x, int y, int w, int h, String label, boolean selected, boolean alert, OnPress action) {
            super(x, y, w, h, Component.literal(label), action, DEFAULT_NARRATION);
            this.selected = selected;
            this.alert = alert;
        }

        @Override
        protected void extractContents(GuiGraphicsExtractor g, int mouseX, int mouseY, float delta) {
            boolean hover = active && isHoveredOrFocused();
            int x = getX(), y = getY() + (selected ? 0 : 2), w = getWidth(), h = getHeight() - (selected ? 0 : 2);
            int paper = selected ? PAPER : !active ? 0xFFD3DEE8 : hover ? 0xFFF7FBFF : PAPER_SHADE;
            int edge = active || selected ? EDGE : 0xFF98A9BA;
            g.fill(x + 1, y, x + w - 1, y + h, edge);
            g.fill(x, y + 1, x + w, y + h, edge);
            g.fill(x + 1, y + 1, x + w - 1, y + h + (selected ? 1 : 0), paper);
            var font = Minecraft.getInstance().font;
            int ink = !active && !selected ? 0xFF8E9DAC : selected ? INK : hover ? INK : MUTED;
            g.centeredText(font, getMessage().getString(), x + w / 2, y + (h - 7) / 2, ink);
            if (alert && !selected) {
                long t = System.currentTimeMillis() / 400 % 2;
                cloud(g, x + w - 7, y - 4, t == 0 ? 1 : 0.6F);
            }
        }
    }

    /** A round dock button with an item icon (and its name, on wide screens). */
    static final class DockButton extends Button {
        private final ItemStack icon;
        private final boolean labeled;
        private final int badge;

        DockButton(int x, int y, int w, int h, String label, ItemStack icon, boolean labeled, int badge, OnPress action) {
            super(x, y, w, h, Component.literal(label), action, DEFAULT_NARRATION);
            this.icon = icon;
            this.labeled = labeled;
            this.badge = badge;
        }

        @Override
        protected void extractContents(GuiGraphicsExtractor g, int mouseX, int mouseY, float delta) {
            boolean hover = active && isHoveredOrFocused();
            int x = getX(), y = getY() - (hover ? 1 : 0), w = getWidth(), h = getHeight();
            int fill = !active ? 0xFFD3DEE8 : hover ? 0xFFFFFFFF : 0xFFEEF4FA;
            int edge = !active ? 0xFF98A9BA : EDGE;
            g.fill(x + 2, y + h, x + w - 2, y + h + 2, 0x44000000);
            g.fill(x + 2, y, x + w - 2, y + h, edge);
            g.fill(x, y + 2, x + w, y + h - 2, edge);
            g.fill(x + 1, y + 1, x + w - 1, y + h - 1, edge);
            g.fill(x + 2, y + 1, x + w - 2, y + h - 1, fill);
            g.fill(x + 1, y + 2, x + w - 1, y + h - 2, fill);
            int iconX = labeled ? x + 3 : x + (w - 16) / 2, iconY = y + (h - 16) / 2;
            if (!icon.isEmpty()) g.item(icon, iconX, iconY);
            var font = Minecraft.getInstance().font;
            if (labeled) g.text(font, font.plainSubstrByWidth(getMessage().getString(), w - 22), x + 20, y + (h - 8) / 2, active ? INK : 0xFF8E9DAC, false);
            if (badge >= 0) {
                int bx = x + w - 7, by = y - 3;
                g.fill(bx - 1, by, bx + 7, by + 8, badge > 0 ? GOLD : 0xFF8EA4BA);
                g.centeredText(font, String.valueOf(badge), bx + 3, by, 0xFFFFFFFF);
            }
            if (!active) g.fill(x + 2, y + 2, x + w - 2, y + h - 2, 0x66DDE5EE);
        }
    }
}
