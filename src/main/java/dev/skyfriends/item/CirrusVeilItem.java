package dev.skyfriends.item;

import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;

/**
 * A Cirrus Veil, worn in the chest slot: whenever its wearer is falling, it catches the air and they
 * drift down gently (Slow Falling) unless they hold sneak to drop. A Cirri's gift for guests of the
 * sky villages, who would otherwise have a long way to fall.
 */
public class CirrusVeilItem extends Item {
    public CirrusVeilItem(Properties properties) {
        super(properties);
    }

    @Override
    public void inventoryTick(ItemStack stack, ServerLevel level, Entity entity, EquipmentSlot slot) {
        if (slot != EquipmentSlot.CHEST || !(entity instanceof Player player)) return;
        // (the server learns a player's falling from their movement: fall distance, not velocity)
        if (!player.onGround() && !player.isShiftKeyDown() && !player.isFallFlying() && !player.getAbilities().flying
                && player.fallDistance > 1.5) {
            player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 15, 0, true, false, true));
        }
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> tooltip, TooltipFlag flag) {
        tooltip.accept(Component.translatable("item.skyfriends.cirrus_veil.desc").withStyle(ChatFormatting.GRAY));
    }
}
