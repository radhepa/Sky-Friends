package dev.skyfriends;

import dev.skyfriends.item.CirrusVeilItem;
import dev.skyfriends.item.WindsongFluteItem;
import dev.skyfriends.registry.MobRegistry;
import java.util.function.Function;
import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;

/** The mod's plain items (block items come with SkyBlocks, spawn eggs with the mob registry), and its creative tab. */
public final class SkyItems {
    private SkyItems() {}

    private static <T extends Item> T add(String name, Function<Item.Properties, T> factory, Item.Properties properties) {
        var id = SkyFriends.id(name);
        return Registry.register(BuiltInRegistries.ITEM, id, factory.apply(properties.setId(ResourceKey.create(Registries.ITEM, id))));
    }

    /** Shed by Cloud Koi as they swim; woven into veilcloth and veils. */
    public static final Item SKY_SCALE = add("sky_scale", Item::new, new Item.Properties());
    /** The fruit of the skywood tree. */
    public static final Item SKY_PEACH = add("sky_peach", Item::new, new Item.Properties()
            .food(new FoodProperties.Builder().nutrition(5).saturationModifier(0.5F).build()));
    public static final WindsongFluteItem WINDSONG_FLUTE = add("windsong_flute", WindsongFluteItem::new, new Item.Properties().stacksTo(1)
            .rarity(Rarity.UNCOMMON));
    public static final CirrusVeilItem CIRRUS_VEIL = add("cirrus_veil", CirrusVeilItem::new, new Item.Properties().stacksTo(1)
            .rarity(Rarity.RARE).equippable(EquipmentSlot.CHEST));

    public static final CreativeModeTab TAB = Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, SkyFriends.id("sky_friends"),
            FabricCreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.skyfriends"))
                    .icon(() -> new ItemStack(SkyBlocks.SKY_LANTERN))
                    .displayItems((params, out) -> {
                        SkyBlocks.all().values().forEach(out::accept);
                        out.accept(SKY_SCALE);
                        out.accept(SKY_PEACH);
                        out.accept(WINDSONG_FLUTE);
                        out.accept(CIRRUS_VEIL);
                        MobRegistry.all().forEach(e -> out.accept(e.spawnEgg()));
                    })
                    .build());

    /** Loads the class (the fields above register everything). */
    public static void register() {}
}
