package dev.skyfriends.block;

import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.state.BlockState;

/** Stairs of a Sky Friends block (vanilla's constructor isn't public). */
public class SkyStairBlock extends StairBlock {
    public SkyStairBlock(BlockState base, Properties properties) {
        super(base, properties);
    }
}
