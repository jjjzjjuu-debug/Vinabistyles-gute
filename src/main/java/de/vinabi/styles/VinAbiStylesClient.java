package de.vinabi.styles;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.fabricmc.fabric.api.resource.ResourceManagerHelper;
import net.fabricmc.fabric.api.resource.ResourcePackActivationType;
import net.fabricmc.loader.api.FabricLoader;
import net.fabricmc.loader.api.ModContainer;
import net.minecraft.client.option.KeyBinding;
import net.minecraft.client.util.InputUtil;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;
import org.lwjgl.glfw.GLFW;

public class VinAbiStylesClient implements ClientModInitializer {
    private static KeyBinding openKey;

    @Override
    public void onInitializeClient() {
        ModContainer container = FabricLoader.getInstance().getModContainer(Styles.MOD_ID).orElseThrow();

        for (Styles.Category c : Styles.CATEGORIES) {
            for (Styles.Style s : Styles.STYLES) {
                ResourceManagerHelper.registerBuiltinResourcePack(
                        Identifier.of(Styles.MOD_ID, Styles.packName(c, s)),
                        container,
                        Text.literal("VinAbi · " + c.label() + " · " + s.label()),
                        ResourcePackActivationType.NORMAL);
            }
        }

        KeyBinding.Category category = KeyBinding.Category.create(Identifier.of(Styles.MOD_ID, "main"));
        openKey = KeyBindingHelper.registerKeyBinding(new KeyBinding(
                "key.vinabistyles.open", InputUtil.Type.KEYSYM, GLFW.GLFW_KEY_RIGHT_SHIFT, category));

        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            while (openKey.wasPressed()) {
                if (client.currentScreen == null) client.setScreen(new StylesScreen());
            }
        });
    }
}
