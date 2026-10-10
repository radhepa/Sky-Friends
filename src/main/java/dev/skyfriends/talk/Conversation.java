package dev.skyfriends.talk;

import dev.skyfriends.anim.Cue;
import dev.skyfriends.entity.Cirri;
import dev.skyfriends.life.Chronicle;
import dev.skyfriends.life.Emote;
import dev.skyfriends.life.Gossip;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/**
 * The server side of talking with a Cirri: what they say when you open it, and what happens for each reply,
 * question, gift and tab. Each step sends the whole screen ({@link TalkPayload}); the client sends back the
 * button pressed ({@link TalkActionPayload}).
 *
 * <p>Friendship grows a little the first time you talk each day, for each topic once a day, for answering their
 * questions, and with gifts they like (two a day). "How's your day?" sometimes turns into a question about you
 * (they remember the answer) or, if they see you need it, an offer to help. The news opens at Fair Wind (3) and
 * talk of the ones they love at Open Sky (5).
 *
 * <p>The screen has three tabs: Talk, Story (their personal story, see {@link Storyteller}) and Journal (your
 * memories with them and what you know of them). Someone upset with you, or busy, or woken at night, may cut the
 * conversation short ({@link #walkOff}).
 */
public final class Conversation {
    public static final int GIFTS_PER_DAY = 2;
    private static final double REACH = 8.0;

    private Conversation() {}

    public static void register() {
        PayloadTypeRegistry.clientboundPlay().register(TalkPayload.TYPE, TalkPayload.CODEC);
        PayloadTypeRegistry.serverboundPlay().register(TalkActionPayload.TYPE, TalkActionPayload.CODEC);
        ServerPlayNetworking.registerGlobalReceiver(TalkActionPayload.TYPE, (payload, context) -> act(context.player(), payload));
    }

    // -- opening ----------------------------------------------------------------------------------

    public static void open(ServerPlayer player, Cirri c) {
        TalkState talk = c.talk();
        String snub = talk.snubbedBy(player);
        if (snub != null) {
            String first = c.firstName();
            player.sendOverlayMessage(Component.literal(switch (snub) {
                case "dislike" -> first + " turns away from you.";
                case "sleep" -> first + " is asleep again.";
                default -> c.isBaby() ? first + " is off playing. Try again in a little while." : first + " is busy. Try again in a little while.";
            }));
            return;
        }
        Bond bond = talk.bond(player);
        long day = c.dayNumber();
        bond.today(day);
        Tale tale = talk.tale(player);
        tale.visit(day);
        int before = bond.level();
        if (!bond.met || tale.memories.isEmpty()) tale.remember(day, "Met " + c.firstName() + " in " + c.villageName() + ".");
        boolean upset = bond.grudge > 0;
        String routine = c.routineTag();
        long time = Math.floorMod(c.dayTime(), 24000L);
        String pool;
        if (!bond.met) {
            pool = "first_meeting";
            bond.met = true;
        } else if (bond.hurtUntil > player.level().getGameTime()) {
            pool = "hurt";
        } else if (c.asleep()) {
            pool = "night";
        } else if (routine.equals("escort") && c.getRandom().nextBoolean()) {
            pool = "whale.sighted";
        } else if (!c.isBaby() && time >= 11000 && time < 12600 && c.getRandom().nextInt(5) < 2) {
            pool = "evensong.invite";
        } else {
            pool = "";
        }
        String status = "";
        if (upset) {
            status = c.firstName() + " is still upset with you.";
        } else if (!bond.greeted) {
            bond.greeted = true;
            gain(bond, 4);
            status = "First words today: +4";
        }
        talk.start(player);
        c.beginTalk(player);
        String said = pool.isEmpty() ? greeting(c, player) : TalkWorld.say(c, player, pool);
        if (said == null) said = greeting(c, player);
        Emote mood = upset ? Emote.GLOOM : pool.equals("night") ? Emote.SLEEP : pool.equals("whale.sighted") ? Emote.SPARKLE
                : bond.level() >= Friendship.PRESENTS ? Emote.HEART : bond.level() >= 4 ? Emote.NOTE : Emote.EXCLAIM;
        send(player, c, bond, talkPage(c, player, bond, said, status), before, true, false, mood);
    }

    private static String greeting(Cirri c, ServerPlayer player) {
        String line = TalkWorld.line(c, player, "greet");
        return line != null ? line : "Fair wind, " + player.getName().getString() + ".";
    }

    /**
     * They cut the conversation short: they say so, and the screen shows it (the replies close). {@code reason}:
     * dislike (still upset with you), busy, or sleep (woken at night).
     */
    public static void walkOff(ServerPlayer player, Cirri c, String reason) {
        TalkState talk = c.talk();
        Bond bond = talk.bond(player);
        long day = c.dayNumber();
        bond.today(day);
        Tale tale = talk.tale(player);
        String pool = switch (reason) {
            case "dislike" -> "walk_off";
            case "sleep" -> "night";
            default -> "busy_off";
        };
        String first = c.firstName();
        String status = switch (reason) {
            case "dislike" -> first + " turned away. They're still upset with you.";
            case "sleep" -> first + " has gone back to sleep.";
            default -> c.isBaby() ? first + " flew off to play." : first + " had to go.";
        };
        if (reason.equals("dislike")) tale.remember(day, first + " turned away from you.");
        String said = TalkWorld.say(c, player, pool);
        if (said == null) said = "...";
        talk.lastLine = said;
        Cue.send(c, reason.equals("dislike") ? "annoyed" : "farewell", player);
        send(player, c, bond, talkPage(c, player, bond, said, status), bond.level(), false, true,
                reason.equals("dislike") ? Emote.ANGER : reason.equals("sleep") ? Emote.SLEEP : Emote.DOTS);
    }

    // -- replies ----------------------------------------------------------------------------------

    static void act(ServerPlayer player, TalkActionPayload action) {
        if (!(player.level().getEntity(action.entityId()) instanceof Cirri c) || !c.getUUID().equals(action.id()) || !c.isAlive()) return;
        TalkState talk = c.talk();
        String act = action.action();
        boolean talking = talk.isTalkingTo(player);
        if (act.equals("goodbye")) {
            if (talking) c.endTalk();
            return;
        }
        // the Journal is the player's own: it stays open after they've cut the conversation short
        boolean journal = act.equals("tab_journal") || act.startsWith("journal_");
        double reach = journal ? REACH * 4 : REACH;
        if (c.distanceToSqr(player) > reach * reach || (!talking && !journal)) return;
        if (talking) talk.keep();
        Bond bond = talk.bond(player);
        long day = c.dayNumber();
        bond.today(day);
        Tale tale = talk.tale(player);
        int before = bond.level();
        if (journal) {
            String page = act.startsWith("journal_") ? act.substring(8) : "memories";
            send(player, c, bond, Storyteller.journal(c, player, bond, tale, page), before, false, !talking, null);
            return;
        }
        if (act.equals("tab_story") || act.startsWith("story_")) {
            Storyteller.Page page = act.equals("tab_story") ? Storyteller.story(c, player, bond, tale) : Storyteller.act(c, player, bond, tale, act);
            if (page == null) return;
            talk.lastLine = page.text();
            talk.planLeave(player);
            send(player, c, bond, page, before, false, false, act.startsWith("story_end") || act.startsWith("story_give") ? Emote.HEART
                    : act.equals("tab_story") ? null : Emote.NOTE);
            return;
        }
        if (act.equals("trade")) {
            if (!c.isMerchant()) return;
            c.endTalk();
            c.openTrade(player);
            String line = TalkWorld.say(c, player, "trade.open");
            if (line != null) player.sendSystemMessage(Component.literal("<" + c.firstName() + "> " + line));
            return;
        }
        if (act.startsWith("answer:") || act.equals("skip_question")) {
            answer(player, c, bond, tale, act, before);
            return;
        }
        String said, status = "";
        Emote mood = Emote.DOTS;
        switch (act) {
            case "talk", "tab_talk" -> {
                said = greeting(c, player);
                mood = Emote.NOTE;
            }
            case "apology" -> {
                if (bond.grudge <= 0 || bond.apologized) return;
                bond.apologized = true;
                bond.grudge--;
                String first = c.firstName();
                Cue.send(c, bond.grudge == 0 ? "pleased" : "decline", player);
                if (bond.grudge == 0) {
                    said = TalkWorld.say(c, player, "apology_accepted");
                    status = first + " forgives you.";
                    mood = Emote.HEART;
                    tale.remember(day, "You said sorry to " + first + ". They forgave you.");
                } else {
                    said = TalkWorld.say(c, player, "apology_wary");
                    status = first + " is still wary of you. Give it time.";
                    mood = Emote.SWEAT;
                    tale.remember(day, "You said sorry to " + first + ". They're still wary.");
                }
            }
            case "gift" -> {
                Gift g = gift(player, c, bond);
                said = g.said;
                status = g.status;
                mood = g.mood;
            }
            default -> {
                var topics = topics(c);
                if (!topics.contains(act) || !unlocked(c, act, bond)) return;
                if (act.equals("chat")) {
                    // now and then "how's your day?" turns into a question about you, or an offer of help
                    Lines.Question q = TalkWorld.ask(c, player, tale);
                    if (q != null) {
                        String asked = TalkWorld.askText(c, player, q);
                        talk.lastLine = asked;
                        if (bond.topics.add(act)) {
                            gain(bond, 4);
                            status = "+4. ";
                        }
                        status += q.offer() ? c.firstName() + " offers to help." : c.firstName() + " asks you something.";
                        talk.planLeave(player);
                        Emote ask = q.offer() ? Emote.IDEA : Emote.QUESTION;
                        send(player, c, bond, new Storyteller.Page("talk", asked, status, TalkWorld.answers(q)), before, false, false, ask);
                        return;
                    }
                }
                said = switch (act) {
                    case "news" -> Gossip.news(c, player);
                    case "heart" -> Gossip.heart(c, player);
                    default -> TalkWorld.line(c, player, act);
                };
                if (said == null) said = greeting(c, player);
                if ((act.equals("chat") || act.equals("work")) && c.getRandom().nextInt(act.equals("chat") ? 3 : 4) == 0) {
                    String mention = Gossip.mention(c, player, act);
                    if (!mention.isEmpty()) said = said + " " + mention;
                }
                if (act.equals("song")) TalkWorld.sing(c);
                mood = switch (act) {
                    case "work" -> Emote.IDEA;
                    case "sky" -> Emote.SPARKLE;
                    case "ground" -> Emote.QUESTION;
                    case "song" -> Emote.NOTE;
                    case "news" -> Emote.IDEA;
                    case "heart", "secret" -> Emote.BLUSH;
                    case "play" -> Emote.EXCLAIM;
                    case "family" -> Emote.HEART;
                    default -> Emote.DOTS;
                };
                if (bond.topics.add(act)) {
                    int gain = act.equals("chat") ? 4 : 3;
                    gain(bond, gain);
                    status = "+" + gain;
                } else {
                    status = "You've talked about that today.";
                }
            }
        }
        if (said == null) said = "...";
        talk.lastLine = said;
        talk.planLeave(player);
        send(player, c, bond, talkPage(c, player, bond, said, status), before, false, false, mood);
    }

    /** You answered their question (or turned down their offer): they reply, remember it, and do what they offered. */
    private static void answer(ServerPlayer player, Cirri c, Bond bond, Tale tale, String act, int before) {
        Lines.Question q = TalkWorld.asking(c, player);
        if (act.equals("skip_question")) {
            bond.stopAsking();
            String said = TalkWorld.line(c, player, "chat");
            send(player, c, bond, talkPage(c, player, bond, said != null ? said : "Another time, then.", "No pressure."), before, false, false, Emote.DOTS);
            return;
        }
        if (q == null) return;
        int index = Talk.answerIndex(act, q.id());
        if (index < 0 || index >= q.answers().size()) return;
        Lines.Answer a = q.answers().get(index);
        long today = c.dayNumber();
        bond.stopAsking();
        bond.flag(q.offer() ? "offer:" + q.id() + ":" + today : "q:" + q.id());
        if (a.flag() != null && !a.flag().isEmpty()) bond.flag("a:" + a.flag());
        String status = q.offer() ? "" : "They'll remember that.";
        if (a.points() > 0) {
            gain(bond, a.points());
            status = "+" + a.points() + "." + (q.offer() ? "" : " They'll remember that.");
        }
        if (a.effect() != null && !a.effect().isEmpty()) status = TalkWorld.effect(a.effect(), player, c);
        if (!q.offer() && a.flag() != null && !a.flag().isEmpty()) tale.remember(today, "You told " + c.firstName() + ": " + a.label() + ".");
        String reply = Talk.fill(a.reply(), TalkWorld.fill(c, player));
        Emote mood = Emote.parse(a.mood());
        c.talk().lastLine = reply == null ? a.reply() : reply;
        send(player, c, bond, talkPage(c, player, bond, c.talk().lastLine, status.isEmpty() ? "Thank you." : status), before, false, false,
                mood == null ? Emote.NOTE : mood);
    }

    private record Gift(String said, String status, Emote mood) {}

    private static Gift gift(ServerPlayer player, Cirri c, Bond bond) {
        ItemStack held = player.getMainHandItem();
        TalkState talk = c.talk();
        if (held.isEmpty()) return new Gift(talk.lastLine, "Hold something in your hand to give it.", Emote.QUESTION);
        if (bond.gifts >= GIFTS_PER_DAY) {
            String said = TalkWorld.say(c, player, "gift.limit");
            return new Gift(said != null ? said : talk.lastLine, "No more gifts today.", Emote.DOTS);
        }
        String taste = Tastes.of(held, c.isBaby());
        int points = Tastes.points(taste);
        String name = held.getHoverName().getString();
        String id = BuiltInRegistries.ITEM.getKey(held.getItem()).toString();
        if (!player.hasInfiniteMaterials()) held.shrink(1);
        bond.gifts++;
        gain(bond, points);
        Cue.send(c, switch (taste) {
            case "loved" -> "happy";
            case "disliked" -> "decline";
            default -> "thanks";
        }, player);
        Tale tale = talk.tale(player);
        long day = c.dayNumber();
        String first = c.firstName();
        if (!taste.equals("neutral")) tale.tastes.put(id, taste);
        String gave = "Gave " + first + " " + name + ". ";
        switch (taste) {
            case "loved" -> tale.remember(day, gave + "They loved it.");
            case "liked" -> tale.remember(day, gave + "They liked it.");
            case "disliked" -> tale.remember(day, gave + "They didn't like it.");
            default -> { }
        }
        if (taste.equals("loved")) {
            if (bond.grudge > 0) bond.grudge--;
            if (c.level() instanceof ServerLevel level) Chronicle.report(level, c.home(), day, "gift", first, player.getName().getString());
        }
        player.level().playSound(null, c.blockPosition(), SoundEvents.ITEM_PICKUP, SoundSource.NEUTRAL, 0.6F, 1.1F);
        String verdict = switch (taste) {
            case "loved" -> "They loved the " + name + "!";
            case "liked" -> "They liked the " + name + ".";
            case "disliked" -> "They didn't like the " + name + ".";
            default -> "They took the " + name + ".";
        };
        String said = TalkWorld.say(c, player, "gift." + taste, Map.of("gift", name.toLowerCase(java.util.Locale.ROOT)));
        Emote mood = switch (taste) {
            case "loved" -> Emote.HEART;
            case "liked" -> Emote.NOTE;
            case "disliked" -> Emote.SWEAT;
            default -> Emote.DOTS;
        };
        return new Gift(said != null ? said : "Thank you.", verdict + " " + (points >= 0 ? "+" : "") + points, mood);
    }

    // -- helpers ----------------------------------------------------------------------------------

    /** The replies a Cirri offers. */
    public static List<String> topics(Cirri c) {
        return c.isBaby() ? List.of("chat", "play", "sky", "ground", "song", "secret", "family")
                : List.of("chat", "work", "sky", "ground", "song", "news", "heart");
    }

    private static int unlock(String topic) {
        return switch (topic) {
            case "news", "secret" -> Friendship.NEWS;
            case "heart" -> Friendship.HEART;
            default -> 0;
        };
    }

    private static boolean unlocked(Cirri c, String topic, Bond bond) {
        return bond.level() >= unlock(topic);
    }

    private static String label(Cirri c, String topic) {
        boolean kid = c.isBaby();
        return switch (topic) {
            case "chat" -> kid ? "What are you up to?" : "How's your day?";
            case "work" -> "Tell me about your work";
            case "sky" -> "Tell me about the sky";
            case "ground" -> kid ? "Ever touched the ground?" : "What do you make of the ground?";
            case "song" -> "Sing me something";
            case "news" -> "Any news in the village?";
            case "heart" -> "Anyone special?";
            case "play" -> "Let's play!";
            case "secret" -> "Tell me a secret";
            case "family" -> "Tell me about your family";
            case "apology" -> "I'm sorry I hurt you";
            default -> topic;
        };
    }

    static int count(ServerPlayer player, Item item) {
        int n = 0;
        for (ItemStack s : player.getInventory()) if (s.is(item)) n += s.getCount();
        return n;
    }

    static void take(ServerPlayer player, Item item, int count) {
        for (ItemStack s : player.getInventory()) {
            if (count <= 0) return;
            if (!s.is(item)) continue;
            int used = Math.min(count, s.getCount());
            s.shrink(used);
            count -= used;
        }
    }

    static void gain(Bond bond, int points) {
        bond.points = Math.clamp(bond.points + points, 0, Friendship.cap());
    }

    /** The Talk tab: what they said, and the replies (a sorry first while they're upset with you). */
    private static Storyteller.Page talkPage(Cirri c, ServerPlayer player, Bond bond, String said, String status) {
        List<String> topics = new ArrayList<>(topics(c));
        if (bond.grudge > 0 && !bond.apologized) {
            topics.addFirst("apology");
            while (topics.size() > TalkPayload.MAX_CHOICES) topics.removeLast();
        }
        List<TalkPayload.Choice> choices = new ArrayList<>();
        for (String topic : topics) {
            boolean open = unlocked(c, topic, bond);
            String hint = open ? "" : "Opens at " + Friendship.name(unlock(topic)) + " (" + unlock(topic) + ").";
            if (topic.equals("apology")) hint = "They're upset with you for striking them.";
            choices.add(new TalkPayload.Choice(topic, label(c, topic), open, hint));
        }
        return new Storyteller.Page("talk", said, status, choices);
    }

    /** Sends the screen: {@code left} when they have cut it short (the replies close; only the Journal still answers). */
    private static void send(ServerPlayer player, Cirri c, Bond bond, Storyteller.Page page, int levelBefore, boolean opening, boolean left,
                             Emote mood) {
        int level = bond.level();
        boolean levelUp = level > levelBefore;
        Tale tale = c.talk().tale(player);
        String dialogue = page.text();
        if (levelUp) {
            Cue.send(c, "happy", player);
            mood = Emote.SPARKLE;
            String up = TalkWorld.say(c, player, "level_up");
            // in their story and your Journal the banner says it; the quip is for small talk
            if (up != null && page.tab().equals("talk")) dialogue = dialogue + " " + up;
            tale.remember(c.dayNumber(), "You and " + c.firstName() + " grew closer: " + Friendship.name(level) + ".");
        }
        if (mood != null) mood.show(c, opening ? 4 : 0);
        List<TalkPayload.Choice> choices = page.choices();
        if (left) {
            choices = choices.stream().map(ch -> ch.id().startsWith("journal_")
                    ? ch : new TalkPayload.Choice(ch.id(), ch.label(), false, "They've gone.")).toList();
        }
        String voice = c.isBaby() ? "child" : c.female() ? "woman" : "man";
        ServerPlayNetworking.send(player, new TalkPayload(c.getId(), c.getUUID(), c.firstName(), c.title(), c.villageName(), voice,
                level, Friendship.name(level), bond.points, Friendship.floor(level), Friendship.next(level), dialogue, page.status(), choices,
                Math.max(0, GIFTS_PER_DAY - bond.gifts), levelUp, opening, page.tab(), left,
                !left && Storyteller.alert(c, player, bond, tale), mood == null ? "" : mood.name(), c.isMerchant() && !left));
    }
}
