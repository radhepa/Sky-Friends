package dev.skyfriends.talk;

import dev.skyfriends.SkyBlocks;
import dev.skyfriends.SkyItems;
import dev.skyfriends.SkySounds;
import dev.skyfriends.block.WindHarpBlock;
import dev.skyfriends.entity.Cirri;
import dev.skyfriends.entity.CloudKoi;
import dev.skyfriends.entity.CloudWhale;
import dev.skyfriends.life.Emote;
import dev.skyfriends.life.Kin;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.biome.Biome;
import org.jspecify.annotations.Nullable;

/**
 * Reads the world into a {@link Talk.Context} for a Cirri and a player, says the chosen line, asks questions,
 * and carries out what the Cirri offer: patching you up, a sky peach, a breath of wind to fall gently, a lantern
 * in the dark, mending what you hold, the way down to the Wind Stone, a song.
 *
 * <p>Bond flags: {@code asking:<id>} is the question on the table, {@code q:<id>} one you've answered, {@code
 * offer:<id>:<day>} an offer made today, {@code a:<flag>} something they remember about you.
 */
public final class TalkWorld {
    static final Random RANDOM = new Random();
    /** Tests: every "How's your day?" asks a question or makes an offer, if one fits. */
    public static boolean alwaysAsk;
    public static final List<String> WINDS = List.of("aure", "sefa", "vell", "borre");

    private TalkWorld() {}

    // -- reading the moment -----------------------------------------------------------------------

    public static Talk.Context context(Cirri c, ServerPlayer p, String topic) {
        ServerLevel level = (ServerLevel) c.level();
        Bond b = c.talk().bond(p);
        long time = c.dayTime(), today = c.dayNumber();
        String moon = Talk.MOONS[(int) Math.floorMod(today, 8L)];
        ItemStack hand = p.getMainHandItem();
        var states = states(p, level, time);
        var extra = new HashSet<String>();
        if (!level.getEntitiesOfClass(CloudWhale.class, c.getBoundingBox().inflate(128, 64, 128), CloudWhale::isAlive).isEmpty()) extra.add("whale");
        if (!level.getEntitiesOfClass(CloudKoi.class, c.getBoundingBox().inflate(14), CloudKoi::isAlive).isEmpty()) extra.add("koi");
        if (!level.getEntitiesOfClass(Cirri.class, c.getBoundingBox().inflate(14), o -> o != c && o.isBaby()).isEmpty()) extra.add("children");
        if (harpNear(level, c.blockPosition())) extra.add("harp");
        if (c.routineTag().equals("evensong")) extra.add("evensong");
        // a couple of things they remember about you, for callbacks
        var remembered = new ArrayList<String>();
        for (String flag : b.flags) if (flag.startsWith("a:")) remembered.add(flag);
        java.util.Collections.shuffle(remembered, RANDOM);
        extra.addAll(remembered.subList(0, Math.min(2, remembered.size())));
        if (hand.isDamaged()) extra.add("damaged");
        var fill = fill(c, p);
        if (fill.containsKey("partner")) extra.add("partnered");
        if (fill.containsKey("child")) extra.add("parent");
        return new Talk.Context(topic, c.isBaby(), c.talk().personality().id, c.job(), b.level(), Talk.period(time), weather(level, c.blockPosition()),
                wind(level, today), moon, c.routineTag(), held(hand), states, extra, fill);
    }

    /** The placeholders for this Cirri and player (docs/DIALOGUE.md); ones that don't apply are left out. */
    public static Map<String, String> fill(Cirri c, ServerPlayer p) {
        ServerLevel level = (ServerLevel) c.level();
        long today = c.dayNumber();
        var fill = new HashMap<String, String>();
        fill.put("name", c.firstName());
        fill.put("player", p.getName().getString());
        fill.put("village", c.villageName());
        fill.put("job", c.title().toLowerCase(Locale.ROOT));
        String wind = wind(level, today);
        fill.put("wind", Character.toUpperCase(wind.charAt(0)) + wind.substring(1));
        fill.put("moon", Talk.moonName(Talk.MOONS[(int) Math.floorMod(today, 8L)]));
        fill.put("day", Long.toString(today + 1));
        if (!p.getMainHandItem().isEmpty()) fill.put("item", p.getMainHandItem().getHoverName().getString().toLowerCase(Locale.ROOT));
        var village = Kin.village(c);
        Cirri partner = Kin.partner(c);
        if (partner != null) {
            fill.put("partner", partner.firstName());
            fill.put("spouse", Kin.spouseWord(c));
        }
        var kids = Kin.children(c, village);
        if (!kids.isEmpty()) fill.put("child", kids.get(RANDOM.nextInt(kids.size())).firstName());
        Cirri mum = Kin.mother(c), dad = Kin.father(c);
        if (mum != null) fill.put("mother", mum.firstName());
        if (dad != null) fill.put("father", dad.firstName());
        Cirri friend = Kin.friend(c, village), coworker = Kin.coworker(c, village), crush = Kin.crush(c, village);
        if (friend != null) fill.put("friend", friend.firstName());
        if (coworker != null) fill.put("coworker", coworker.firstName());
        if (crush != null) fill.put("crush", crush.firstName());
        var others = village.stream().filter(o -> o != c).toList();
        if (!others.isEmpty()) fill.put("neighbour", others.get(RANDOM.nextInt(others.size())).firstName());
        return fill;
    }

    /** clear, rain, thunder or snow, where the Cirri is (their villages are high: cold lands get snow up there). */
    public static String weather(ServerLevel level, BlockPos pos) {
        if (!level.isRaining()) return "clear";
        Biome.Precipitation fall = level.precipitationAt(pos);
        if (fall == Biome.Precipitation.NONE) return "clear";
        if (level.isThundering()) return "thunder";
        return fall == Biome.Precipitation.SNOW ? "snow" : "rain";
    }

    /** The wind that has the sky today: Borre brings the storms; otherwise one of the four, by the day. */
    public static String wind(ServerLevel level, long day) {
        if (level.isThundering()) return "borre";
        long x = day * 0x9E3779B97F4A7C15L ^ level.getSeed();
        x ^= x >>> 31;
        x *= 0xBF58476D1CE4E5B9L;
        x ^= x >>> 29;
        return WINDS.get((int) Math.floorMod(x, 4L));
    }

    private static boolean harpNear(ServerLevel level, BlockPos at) {
        for (BlockPos p : BlockPos.betweenClosed(at.offset(-5, -3, -5), at.offset(5, 3, 5))) {
            if (level.getBlockState(p).getBlock() instanceof WindHarpBlock) return true;
        }
        return false;
    }

    /** What kind of thing the player is holding, as the Cirri see it ({@code held.<kind>}). */
    static String held(ItemStack s) {
        if (s.isEmpty()) return "";
        Item i = s.getItem();
        String id = BuiltInRegistries.ITEM.getKey(i).toString();
        if (i == SkyItems.SKY_PEACH) return "peach";
        if (i == SkyItems.SKY_SCALE) return "scale";
        if (i == SkyItems.WINDSONG_FLUTE) return "flute";
        if (i == SkyItems.CIRRUS_VEIL) return "veil";
        if (i == SkyBlocks.WIND_HARP.asItem()) return "harp";
        if (i == SkyBlocks.CLOUD.asItem()) return "cloud";
        if (i == SkyBlocks.SKY_LANTERN.asItem() || s.is(Items.LANTERN) || s.is(Items.SOUL_LANTERN) || s.is(Items.TORCH)) return "lantern";
        if (s.is(Items.ELYTRA)) return "elytra";
        if (s.is(Items.FIREWORK_ROCKET) || s.is(Items.FIREWORK_STAR) || s.is(Items.GUNPOWDER) || s.is(Items.TNT)) return "firework";
        if (s.is(Items.WIND_CHARGE) || s.is(Items.BREEZE_ROD)) return "breeze";
        if (s.is(Items.FLINT_AND_STEEL) || s.is(Items.FIRE_CHARGE) || s.is(Items.LAVA_BUCKET) || s.is(Items.CAMPFIRE)) return "fire";
        if (s.is(ItemTags.SWORDS) || s.is(Items.BOW) || s.is(Items.CROSSBOW) || s.is(Items.TRIDENT) || s.is(Items.MACE)) return "weapon";
        if (s.is(ItemTags.PICKAXES)) return "pickaxe";
        if (s.is(ItemTags.AXES) || s.is(ItemTags.SHOVELS) || s.is(ItemTags.HOES) || s.is(Items.SHEARS)) return "tool";
        if (s.is(Items.FISHING_ROD)) return "fishing_rod";
        if (s.is(Items.SPYGLASS)) return "spyglass";
        if (s.is(Items.MAP) || s.is(Items.FILLED_MAP) || s.is(Items.COMPASS) || s.is(Items.RECOVERY_COMPASS) || s.is(Items.CLOCK)) return "map";
        if (s.is(Items.BOOK) || s.is(Items.WRITABLE_BOOK) || s.is(Items.WRITTEN_BOOK) || s.is(Items.ENCHANTED_BOOK)) return "book";
        if (s.is(Items.EMERALD) || s.is(Items.EMERALD_BLOCK)) return "emerald";
        if (s.is(Items.DIAMOND) || s.is(Items.DIAMOND_BLOCK) || s.is(Items.NETHERITE_INGOT)) return "diamond";
        if (s.is(Items.GOLD_INGOT) || s.is(Items.GOLD_NUGGET) || s.is(Items.GOLD_BLOCK) || s.is(Items.RAW_GOLD)) return "gold";
        if (s.is(Items.FEATHER)) return "feather";
        if (s.is(Items.PHANTOM_MEMBRANE)) return "membrane";
        if (s.is(Items.STRING) || s.is(ItemTags.WOOL) || s.is(ItemTags.WOOL_CARPETS)) return "string";
        if (s.is(Items.AMETHYST_SHARD) || s.is(Items.AMETHYST_BLOCK) || s.is(Items.AMETHYST_CLUSTER)) return "amethyst";
        if (s.is(ItemTags.SAPLINGS)) return "sapling";
        if (s.is(Items.NOTE_BLOCK) || s.is(Items.JUKEBOX) || s.is(Items.GOAT_HORN) || id.startsWith("minecraft:music_disc_")) return "music";
        if (s.is(Items.TOTEM_OF_UNDYING)) return "totem";
        if (s.is(Items.POTION) || s.is(Items.SPLASH_POTION) || s.is(Items.LINGERING_POTION)) return "potion";
        if (s.is(Items.LEAD) || s.is(Items.NAME_TAG) || s.is(Items.SADDLE)) return "pet";
        if (s.is(Items.BUCKET) || s.is(Items.WATER_BUCKET) || s.is(Items.MILK_BUCKET) || s.is(Items.POWDER_SNOW_BUCKET)) return "bucket";
        if (s.is(Items.CAKE) || s.is(Items.COOKIE) || s.is(Items.PUMPKIN_PIE) || s.is(Items.HONEY_BOTTLE) || s.is(Items.SWEET_BERRIES)
                || s.is(Items.GLOW_BERRIES)) return "treat";
        if (s.is(net.minecraft.tags.BlockItemTags.FLOWERS.item())) return "flower";
        if (s.has(DataComponents.FOOD)) return "food";
        return "";
    }

    /** How the player looks right now. */
    static Set<String> states(ServerPlayer p, ServerLevel level, long time) {
        var states = new HashSet<String>();
        if (p.getHealth() < p.getMaxHealth() * 0.5F) states.add("hurt");
        if (p.getFoodData().getFoodLevel() <= 8) states.add("hungry");
        if (p.isInWaterOrRain() && !p.isInWater()) states.add("wet");
        if (p.isOnFire()) states.add("fire");
        if (p.isFallFlying() || p.getAbilities().flying) states.add("flying");
        var head = p.getItemBySlot(EquipmentSlot.HEAD);
        var chest = p.getItemBySlot(EquipmentSlot.CHEST);
        if (head.is(Items.CARVED_PUMPKIN)) states.add("pumpkin");
        if (chest.is(Items.ELYTRA)) states.add("elytra");
        else if (chest.is(SkyItems.CIRRUS_VEIL)) states.add("veil");
        else if (chest.is(Items.DIAMOND_CHESTPLATE) || chest.is(Items.NETHERITE_CHESTPLATE)) states.add("diamond");
        else if (chest.is(Items.GOLDEN_CHESTPLATE)) states.add("golden");
        else if (chest.isEmpty() && head.isEmpty() && p.getItemBySlot(EquipmentSlot.LEGS).isEmpty()) states.add("unarmored");
        String period = Talk.period(time);
        if ((period.equals("night") || period.equals("late")) && level.canSeeSky(p.blockPosition())) states.add("dark");
        if (atEdge(p, level)) states.add("edge");
        return states;
    }

    /** Standing on solid ground with a long drop (24 blocks or more) a couple of steps away. */
    static boolean atEdge(ServerPlayer p, ServerLevel level) {
        if (!p.onGround()) return false;
        BlockPos feet = p.blockPosition();
        var cell = new BlockPos.MutableBlockPos();
        for (int dx = -2; dx <= 2; dx += 2) {
            for (int dz = -2; dz <= 2; dz += 2) {
                if (dx == 0 && dz == 0) continue;
                boolean open = true;
                for (int dy = -1; dy >= -24 && open; dy--) {
                    cell.set(feet.getX() + dx, feet.getY() + dy, feet.getZ() + dz);
                    if (!level.getBlockState(cell).getCollisionShape(level, cell).isEmpty()) open = false;
                }
                if (open) return true;
            }
        }
        return false;
    }

    // -- saying things ----------------------------------------------------------------------------

    /** A line for a topic (greet, chat, work, sky, ground, song; children: play, secret, family), remembered so it isn't repeated soon. */
    public static @Nullable String line(Cirri c, ServerPlayer p, String topic) {
        Bond b = c.talk().bond(p);
        var line = Talk.pick(Lines.current(), context(c, p, topic), RANDOM, b.recent);
        if (line == null) return null;
        b.said(line.id());
        return line.text();
    }

    /**
     * A line from one pool ({@code first_meeting}, {@code gift.loved}, {@code news.born}...; children use {@code
     * baby.<pool>} when it exists) with this moment's placeholders and any {@code extra} ones filled; null if
     * the pool has nothing that fits.
     */
    public static @Nullable String say(Cirri c, ServerPlayer p, String pool, Map<String, String> extra) {
        Lines bank = Lines.current();
        String key = c.isBaby() && bank.has("baby." + pool) ? "baby." + pool : pool;
        var fill = fill(c, p);
        fill.putAll(extra);
        Bond b = c.talk().bond(p);
        var line = Talk.from(bank, key, fill, RANDOM, b.recent);
        if (line == null) line = Talk.from(bank, key, fill, RANDOM, List.of());
        if (line == null) return null;
        b.said(line.id());
        return line.text();
    }

    public static @Nullable String say(Cirri c, ServerPlayer p, String pool) {
        return say(c, p, pool, Map.of());
    }

    // -- questions and offers ---------------------------------------------------------------------

    /** Sometimes, on "How's your day?", a Cirri asks you something, or offers to help, instead. */
    public static Lines.@Nullable Question ask(Cirri c, ServerPlayer p, Tale tale) {
        Lines bank = Lines.current();
        Bond b = c.talk().bond(p);
        var ctx = context(c, p, "chat");
        long today = c.dayNumber();
        var done = new HashSet<String>();
        for (String flag : b.flags) {
            if (flag.startsWith("q:")) done.add(flag.substring(2));
            if (flag.startsWith("offer:") && flag.endsWith(":" + today)) done.add(flag.substring(6, flag.lastIndexOf(':')));
        }
        Lines.Question q = null;
        // children ask questions, but only grown-ups make offers
        if (!c.isBaby() && (alwaysAsk || RANDOM.nextFloat() < 0.7F)) q = Talk.question(bank, ctx, done, true, RANDOM);
        // they'll help a stranger, but they warm up before quizzing you: not on the day you first meet
        float curious = c.talk().personality().id.equals("curious") ? 0.4F : 0.26F;
        if (q == null && (alwaysAsk || tale.visits >= 2 && RANDOM.nextFloat() < curious)) q = Talk.question(bank, ctx, done, false, RANDOM);
        if (q == null) return null;
        b.stopAsking();
        b.flag("asking:" + q.id());
        return q;
    }

    public static String askText(Cirri c, ServerPlayer p, Lines.Question q) {
        var fill = fill(c, p);
        var options = new ArrayList<String>();
        for (String a : q.ask()) {
            String t = Talk.fill(a, fill);
            if (t != null) options.add(t);
        }
        return options.isEmpty() ? q.ask().getFirst() : options.get(RANDOM.nextInt(options.size()));
    }

    static Lines.@Nullable Question asking(Cirri c, ServerPlayer p) {
        String id = c.talk().bond(p).asking();
        return id.isEmpty() ? null : Lines.current().question(id);
    }

    /** Your possible answers to the question on the table. */
    static List<TalkPayload.Choice> answers(Lines.Question q) {
        var out = new ArrayList<TalkPayload.Choice>();
        for (int i = 0; i < q.answers().size() && i < TalkPayload.MAX_CHOICES - 1; i++) {
            out.add(new TalkPayload.Choice("answer:" + q.id() + ":" + i, q.answers().get(i).label(), true, ""));
        }
        out.add(new TalkPayload.Choice("skip_question", q.offer() ? "No, thank you" : "Let's talk about something else", true, ""));
        return out;
    }

    /** What a Cirri does for you when you accept an offer; the status line. */
    static String effect(String effect, ServerPlayer p, Cirri c) {
        String who = c.firstName();
        ServerLevel level = (ServerLevel) c.level();
        switch (effect) {
            case "heal" -> {
                p.heal(6);
                p.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 100, 0));
                return who + " patched you up. (+3 hearts)";
            }
            case "peach" -> {
                give(p, new ItemStack(SkyItems.SKY_PEACH, 2));
                return who + " gave you two sky peaches.";
            }
            case "slowfall" -> {
                p.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 1200, 0));
                level.sendParticles(ParticleTypes.CLOUD, p.getX(), p.getY() + 0.8, p.getZ(), 12, 0.5, 0.6, 0.5, 0.02);
                return who + " wrapped a breath of wind round you. (Slow Falling for a minute)";
            }
            case "lantern" -> {
                give(p, new ItemStack(SkyBlocks.SKY_LANTERN));
                return who + " gave you a sky lantern.";
            }
            case "scale" -> {
                give(p, new ItemStack(SkyItems.SKY_SCALE));
                return who + " gave you a sky scale. For luck.";
            }
            case "feather" -> {
                give(p, new ItemStack(Items.FEATHER, 3));
                return who + " gave you three feathers.";
            }
            case "flower" -> {
                var flowers = List.of(Items.CORNFLOWER, Items.ALLIUM, Items.AZURE_BLUET, Items.LILY_OF_THE_VALLEY, Items.OXEYE_DAISY, Items.PINK_PETALS);
                give(p, new ItemStack(flowers.get(RANDOM.nextInt(flowers.size()))));
                return who + " gave you a flower.";
            }
            case "emerald_tip" -> {
                give(p, new ItemStack(Items.EMERALD));
                return who + " pressed an emerald into your hand.";
            }
            case "mend_held" -> {
                ItemStack held = p.getMainHandItem();
                if (!held.isDamaged()) return "It didn't need mending after all.";
                held.setDamageValue(Math.max(0, held.getDamageValue() - Math.max(1, held.getMaxDamage() * 3 / 10)));
                return who + " mended your " + held.getHoverName().getString().toLowerCase(Locale.ROOT) + ".";
            }
            case "lift" -> {
                var keeper = Kin.village(c).stream().filter(o -> o.job().equals("windkeeper") && o.work() != null).findFirst();
                if (keeper.isEmpty()) return who + " points down, past the clouds.";
                BlockPos dock = keeper.get().work();
                p.sendSystemMessage(Component.literal("The Lift Dock of " + c.villageName() + " is at " + dock.getX() + ", " + dock.getZ()
                        + ". The Wind Stone stands on the ground straight below it: step into its wind to rise, and hold sneak in the shaft to sink.")
                        .withStyle(ChatFormatting.AQUA));
                return "The way up and down is in your chat.";
            }
            case "song" -> {
                sing(c);
                p.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 80, 0));
                return who + " sang for you.";
            }
            case "dry" -> {
                Conversation.gain(c.talk().bond(p), 3);
                c.talk().tale(p).remember(c.dayNumber(), "We waited out the rain together.");
                return "+3. You waited out the rain together.";
            }
            default -> {
                return "";
            }
        }
    }

    /** A little song: their voice, and notes in the air round them. */
    public static void sing(Cirri c) {
        if (!(c.level() instanceof ServerLevel level)) return;
        c.playSound(c.isBaby() ? SkySounds.CIRRI_CHILD_HUM : c.female() ? SkySounds.CIRRI_FEMALE_HUM : SkySounds.CIRRI_MALE_HUM, 1.0F, c.getVoicePitch());
        level.sendParticles(ParticleTypes.NOTE, c.getX(), c.getEyeY() + 0.6, c.getZ(), 5, 0.6, 0.3, 0.6, 1.0);
        Emote.NOTE.show(c, 0);
    }

    public static void give(ServerPlayer p, ItemStack stack) {
        p.getInventory().placeItemBackInInventory(stack, net.minecraft.util.Prediction.SERVER_ONLY);
    }

    /** Plays a sound for the player only (a soft confirmation). */
    static void chime(ServerPlayer p) {
        p.level().playSound(null, p.blockPosition(), net.minecraft.sounds.SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.NEUTRAL, 0.5F, 1.4F);
    }
}
