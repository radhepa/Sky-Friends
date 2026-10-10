package dev.skyfriends.talk;

import java.util.Set;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.ItemStack;

/**
 * What the Cirri love, like and don't like to be given. Light, bright, sweet and musical things please them;
 * heavy, loud, fiery and dead things don't. Children are the same, with a sweeter tooth.
 */
public final class Tastes {
    private static final Set<String> LOVED = Set.of("skyfriends:sky_scale", "minecraft:amethyst_shard", "minecraft:phantom_membrane",
            "minecraft:glow_berries", "minecraft:honey_bottle", "minecraft:wind_charge", "minecraft:breeze_rod", "minecraft:feather",
            "minecraft:spore_blossom", "minecraft:pink_petals", "minecraft:lily_of_the_valley", "minecraft:azure_bluet",
            "minecraft:echo_shard", "minecraft:nautilus_shell", "minecraft:firefly_bush");
    private static final Set<String> LIKED = Set.of("skyfriends:sky_peach", "minecraft:string", "minecraft:white_wool",
            "minecraft:light_blue_dye", "minecraft:cornflower", "minecraft:allium", "minecraft:blue_orchid", "minecraft:oxeye_daisy",
            "minecraft:dandelion", "minecraft:torchflower", "minecraft:sweet_berries", "minecraft:melon_slice", "minecraft:apple",
            "minecraft:golden_apple", "minecraft:glowstone_dust", "minecraft:candle", "minecraft:prismarine_crystals",
            "minecraft:cookie", "minecraft:cake", "skyfriends:white_veilcloth", "skyfriends:sky_veilcloth", "skyfriends:rose_veilcloth",
            "skyfriends:wind_chime", "skyfriends:sky_lantern", "minecraft:note_block", "minecraft:goat_horn", "minecraft:spyglass");
    private static final Set<String> DISLIKED = Set.of("minecraft:dirt", "minecraft:coarse_dirt", "minecraft:gravel",
            "minecraft:cobblestone", "minecraft:cobbled_deepslate", "minecraft:anvil", "minecraft:iron_block", "minecraft:rotten_flesh",
            "minecraft:spider_eye", "minecraft:poisonous_potato", "minecraft:pufferfish", "minecraft:gunpowder", "minecraft:firework_rocket",
            "minecraft:tnt", "minecraft:bone", "minecraft:lava_bucket", "minecraft:fire_charge", "minecraft:flint_and_steel",
            "minecraft:beef", "minecraft:porkchop", "minecraft:mutton", "minecraft:chicken", "minecraft:rabbit");
    /** Children love sweets more than amethyst. */
    private static final Set<String> CHILD_LOVED = Set.of("minecraft:cookie", "minecraft:cake", "minecraft:sweet_berries",
            "skyfriends:sky_peach", "minecraft:feather", "skyfriends:sky_scale", "minecraft:glow_berries", "minecraft:honey_bottle");

    private Tastes() {}

    /** "loved", "liked", "disliked" or "neutral". */
    public static String of(ItemStack stack, boolean child) {
        String id = BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
        if (child && CHILD_LOVED.contains(id)) return "loved";
        if (LOVED.contains(id) || id.startsWith("minecraft:music_disc_")) return "loved";
        if (LIKED.contains(id)) return "liked";
        if (DISLIKED.contains(id)) return "disliked";
        return "neutral";
    }

    /** Friendship for a gift of this taste. */
    public static int points(String taste) {
        return switch (taste) {
            case "loved" -> 20;
            case "liked" -> 10;
            case "disliked" -> -8;
            default -> 3;
        };
    }
}
