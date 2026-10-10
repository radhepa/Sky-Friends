package dev.skyfriends.item;

import dev.skyfriends.SkySounds;
import dev.skyfriends.entity.Cirri;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/** A skywood flute: play a phrase, and every Cirri within twenty blocks turns to listen and drifts close. */
public class WindsongFluteItem extends Item {
    public WindsongFluteItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level instanceof ServerLevel server) {
            server.playSound(null, player.getX(), player.getEyeY(), player.getZ(), SkySounds.WINDSONG_FLUTE, SoundSource.RECORDS, 1.0F, 1.0F);
            server.sendParticles(ParticleTypes.NOTE, player.getX(), player.getEyeY() + 0.4, player.getZ(), 3, 0.4, 0.2, 0.4, 1.0);
            for (Cirri c : server.getEntitiesOfClass(Cirri.class, player.getBoundingBox().inflate(20), Cirri::isAlive)) c.listen(player, 160);
            player.getCooldowns().addCooldown(stack, 50);
        }
        return InteractionResult.SUCCESS;
    }
}
