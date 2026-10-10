package dev.skyfriends;

import dev.skyfriends.entity.Cirri;
import dev.skyfriends.entity.CloudKoi;
import dev.skyfriends.entity.CloudWhale;
import dev.skyfriends.registry.MobEntry;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;

/**
 * Every mob in the mod. The Cirri and the Cloud Koi come from the sky villages and islets (and spawn
 * eggs); Cloud Whales are sent across the sky by the SkySpawner. The client registers a model and
 * renderer for each.
 */
public final class SkyEntities {
    private SkyEntities() {}

    public static final EntityType<Cirri> CIRRI = MobEntry.builder("cirri", Cirri::new, MobCategory.MISC)
            .size(0.6F, 1.8F, 1.62F).type(t -> t.clientTrackingRange(10)).attributes(Cirri::attributes).register();

    public static final EntityType<CloudKoi> CLOUD_KOI = MobEntry.builder("cloud_koi", CloudKoi::new, MobCategory.MISC)
            .size(0.5F, 0.4F, 0.25F).attributes(CloudKoi::attributes).register();
    public static final EntityType<CloudWhale> CLOUD_WHALE = MobEntry.builder("cloud_whale", CloudWhale::new, MobCategory.MISC)
            .size(4.0F, 3.0F, 1.8F).type(t -> t.clientTrackingRange(16)).attributes(CloudWhale::attributes).register();

    /** Loads the class (the fields above register everything). */
    public static void register() {}
}
