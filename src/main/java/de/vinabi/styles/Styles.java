package de.vinabi.styles;

import net.minecraft.resource.ResourcePackManager;
import net.minecraft.resource.ResourcePackProfile;

import java.util.List;

public final class Styles {
    public static final String MOD_ID = "vinabistyles";

    public record Style(String id, String label, int color) {}
    public record Category(String id, String label) {}

    public static final List<Style> STYLES = List.of(
            new Style("neon", "Neon-Lila", 0xFFB040FF),
            new Style("lava", "Lava-Rot", 0xFFFF5618),
            new Style("ice", "Eis-Blau", 0xFF40CCFF),
            new Style("toxic", "Toxic-Grün", 0xFF5AFF50),
            new Style("gold", "Gold-Glanz", 0xFFFFC828),
            new Style("sakura", "Sakura-Pink", 0xFFFF6EB4),
            new Style("ocean", "Ozean-Türkis", 0xFF14D2BE),
            new Style("void", "Void-Weiß", 0xFFC8C8D7)
    );

    public static final List<Category> CATEGORIES = List.of(
            new Category("mace", "Mace"),
            new Category("crystal", "End Crystal"),
            new Category("obsidian", "Obsidian"),
            new Category("windcharge", "Wind Charge"),
            new Category("pearl", "Enderperle"),
            new Category("cobweb", "Cobweb"),
            new Category("armor", "Rüstung"),
            new Category("shield", "Shield"),
            new Category("anchor", "Respawn Anchor"),
            new Category("glowstone", "Glowstone"),
            new Category("glint", "Enchant-Glint"),
            new Category("totem", "Totem"),
            new Category("xpbottle", "XP-Flasche")
    );

    private Styles() {}

    public static String packName(Category c, Style s) {
        return c.id() + "_" + s.id();
    }

    /** Pack-IDs sind je nach Fabric-Version "vinabistyles:name" – deshalb tolerant vergleichen. */
    public static boolean matches(String profileId, Category c, Style s) {
        String n = packName(c, s);
        return profileId.equals(n) || profileId.endsWith(":" + n) || profileId.endsWith("/" + n);
    }

    public static boolean isOurs(String profileId) {
        for (Category c : CATEGORIES)
            for (Style s : STYLES)
                if (matches(profileId, c, s)) return true;
        return false;
    }

    public static String findProfileId(ResourcePackManager manager, Category c, Style s) {
        for (ResourcePackProfile p : manager.getProfiles()) {
            if (matches(p.getId(), c, s)) return p.getId();
        }
        return null;
    }
}
