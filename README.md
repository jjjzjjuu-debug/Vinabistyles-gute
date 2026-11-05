# VinAbi Styles 2.0.0 (Fabric, Minecraft 1.21.11)

Menü mit Rechts-Shift. 13 Kategorien x 8 Styles
(Neon-Lila, Lava-Rot, Eis-Blau, Toxic-Grün, Gold-Glanz, Sakura-Pink, Ozean-Türkis, Void-Weiß):
Mace, End Crystal (+Item), Obsidian (+Crying Obsidian), Wind Charge, Enderperle, Cobweb,
Rüstung (Netherite+Diamant, getragen + Item-Icons), Shield, Respawn Anchor, Glowstone (+Staub),
Enchant-Glint, Totem, XP-Flasche.

## Bauen (GitHub Actions) – Texturen werden dort automatisch erzeugt
Alles hochladen, Reiter "Actions" -> fertige .jar unter "Artifacts".
Lokal: JDK 21 + Gradle 9.2.1 -> `gradle build` -> build/libs/vinabistyles-2.0.0.jar

## Texturen ändern
    python3 gen_textures.py .      # braucht Pillow; Farben stehen oben in PAL
