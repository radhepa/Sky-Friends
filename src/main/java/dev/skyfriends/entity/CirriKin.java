package dev.skyfriends.entity;

import dev.skyfriends.SkyBlocks;
import dev.skyfriends.SkyItems;
import java.util.List;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.trading.ItemCost;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.ItemLike;

/** Names, looks and the Skymerchant's wares: the parts of a Cirri's life that are plain lists. */
public final class CirriKin {
    private CirriKin() {}

    public static final List<String> WOMEN = List.of("Ilvara", "Seraine", "Nalia", "Vesa", "Aurelie", "Sirena", "Mirael", "Celune",
            "Ayla", "Iriel", "Zephyra", "Liora", "Selanth", "Vaela", "Neris", "Amara", "Sefi", "Talin", "Ysolde", "Elira", "Noa", "Kaeli",
            "Oriane", "Thessaly", "Wren", "Isembre", "Calla", "Lumi");
    public static final List<String> MEN = List.of("Aurel", "Caelan", "Tavi", "Sorin", "Eren", "Ilyan", "Varo", "Kestrel", "Lior",
            "Silvan", "Arin", "Corin", "Davian", "Halcyon", "Oren", "Rowe", "Taren", "Faelan", "Ilian", "Mirro", "Navi", "Soren", "Elias",
            "Tamsin", "Avel", "Cyrus", "Jaro", "Pell");

    /** Jobs in a sky village (the buildings' {@code job} flags). */
    public static final List<String> JOBS = List.of("harpist", "weaver", "gardener", "bellkeeper", "lamplighter", "skymerchant", "windkeeper");

    public static final int COMPLEXIONS = 3, PALETTES = 4;
    public static final List<String> PALETTE_NAMES = List.of("dawn", "dusk", "noon", "storm");

    public static String name(boolean female, RandomSource random) {
        List<String> pool = female ? WOMEN : MEN;
        return pool.get(random.nextInt(pool.size()));
    }

    /** Each job dresses in its own colours; everyone else picks freely. */
    public static int palette(String job, RandomSource random) {
        return switch (job) {
            case "harpist", "lamplighter" -> 0;       // dawn
            case "weaver", "skymerchant" -> 1;        // dusk
            case "gardener", "windkeeper" -> 2;       // noon
            case "bellkeeper" -> 3;                   // storm
            default -> random.nextInt(PALETTES);
        };
    }

    // -- the Skymerchant ------------------------------------------------------------------------------

    private static MerchantOffer sell(int emeralds, ItemLike item, int count, int maxUses) {
        return new MerchantOffer(new ItemCost(Items.EMERALD, emeralds), new ItemStack(item, count), maxUses, 2, 0.05F);
    }

    private static MerchantOffer buy(ItemLike item, int count, int maxUses) {
        return new MerchantOffer(new ItemCost(item, count), new ItemStack(Items.EMERALD), maxUses, 2, 0.05F);
    }

    public static MerchantOffers wares() {
        MerchantOffers offers = new MerchantOffers();
        offers.add(sell(1, SkyItems.SKY_PEACH, 6, 16));
        offers.add(sell(2, SkyBlocks.SKYWOOD_SAPLING, 2, 8));
        offers.add(sell(2, SkyBlocks.CLOUD, 8, 12));
        offers.add(sell(1, SkyBlocks.SKYSTONE_BRICKS, 16, 12));
        offers.add(sell(2, SkyBlocks.WHITE_VEILCLOTH, 4, 12));
        offers.add(sell(2, SkyBlocks.SKY_VEILCLOTH, 4, 12));
        offers.add(sell(2, SkyBlocks.ROSE_VEILCLOTH, 4, 12));
        offers.add(sell(3, SkyBlocks.SKY_LANTERN, 2, 12));
        offers.add(sell(3, SkyBlocks.WIND_CHIME, 1, 8));
        offers.add(sell(3, SkyBlocks.GILDED_SKYSTONE, 4, 8));
        offers.add(sell(6, SkyBlocks.WIND_HARP, 1, 4));
        offers.add(sell(8, SkyItems.WINDSONG_FLUTE, 1, 3));
        offers.add(sell(24, SkyItems.CIRRUS_VEIL, 1, 2));
        offers.add(buy(Items.AMETHYST_SHARD, 8, 12));
        offers.add(buy(Items.FEATHER, 12, 12));
        offers.add(buy(Items.PHANTOM_MEMBRANE, 2, 12));
        offers.add(buy(Items.STRING, 16, 12));
        return offers;
    }
}
