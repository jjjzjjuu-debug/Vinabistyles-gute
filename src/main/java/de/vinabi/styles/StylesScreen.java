package de.vinabi.styles;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gl.RenderPipelines;
import net.minecraft.client.gui.Click;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.client.input.KeyInput;
import net.minecraft.resource.ResourcePackManager;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;
import net.minecraft.util.Util;
import org.lwjgl.glfw.GLFW;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class StylesScreen extends Screen {
    private static final int SIDE_W = 124;

    private final Map<String, Integer> applied = new HashMap<>();
    private final Map<String, Integer> pending = new HashMap<>();
    private int selCat = 0;
    private int px, py, pw, ph, rowH;

    public StylesScreen() {
        super(Text.literal("VinAbi Styles"));
    }

    // ------------------------------------------------------------ setup
    @Override
    protected void init() {
        pw = Math.min(width - 16, 500);
        ph = Math.min(height - 16, 370);
        px = (width - pw) / 2;
        py = (height - ph) / 2;
        rowH = Math.max(13, Math.min(22, (ph - 90) / Styles.CATEGORIES.size()));

        if (applied.isEmpty()) {
            loadApplied();
            pending.putAll(applied);
        }

        int bx = px + 10, bw = pw - 20, gap = 4;
        int rowA = py + ph - 74, rowB = py + ph - 50, rowC = py + ph - 26;

        int n = Styles.STYLES.size();
        int perRow = (n + 1) / 2;
        int w1 = (bw - gap * (perRow - 1)) / perRow;
        for (int i = 0; i < n; i++) {
            final int idx = i;
            Styles.Style s = Styles.STYLES.get(i);
            int col = i % perRow, row = i / perRow;
            addDrawableChild(ButtonWidget.builder(Text.literal("Alle: " + s.label()), b -> {
                for (Styles.Category c : Styles.CATEGORIES) pending.put(c.id(), idx);
            }).dimensions(bx + col * (w1 + gap), row == 0 ? rowA : rowB, w1, 20).build());
        }

        int w2 = (bw - gap * 2) / 3;
        addDrawableChild(ButtonWidget.builder(Text.literal("Alles Vanilla"), b -> {
            for (Styles.Category c : Styles.CATEGORIES) pending.put(c.id(), -1);
        }).dimensions(bx, rowC, w2, 20).build());
        addDrawableChild(ButtonWidget.builder(Text.literal("Anwenden"), b -> apply())
                .dimensions(bx + w2 + gap, rowC, w2, 20).build());
        addDrawableChild(ButtonWidget.builder(Text.literal("Schließen"), b -> close())
                .dimensions(bx + 2 * (w2 + gap), rowC, w2, 20).build());
    }

    private void loadApplied() {
        ResourcePackManager m = MinecraftClient.getInstance().getResourcePackManager();
        Collection<String> enabled = m.getEnabledIds();
        for (Styles.Category c : Styles.CATEGORIES) {
            int idx = -1;
            for (int i = 0; i < Styles.STYLES.size(); i++) {
                final Styles.Style s = Styles.STYLES.get(i);
                if (enabled.stream().anyMatch(id -> Styles.matches(id, c, s))) idx = i;
            }
            applied.put(c.id(), idx);
        }
    }

    private void apply() {
        MinecraftClient mc = MinecraftClient.getInstance();
        ResourcePackManager m = mc.getResourcePackManager();
        List<String> enabled = new ArrayList<>(m.getEnabledIds());
        enabled.removeIf(Styles::isOurs);
        List<String> ours = new ArrayList<>();
        for (Styles.Category c : Styles.CATEGORIES) {
            int idx = pending.getOrDefault(c.id(), -1);
            if (idx >= 0) {
                String id = Styles.findProfileId(m, c, Styles.STYLES.get(idx));
                if (id != null) {
                    enabled.add(id);
                    ours.add(id);
                }
            }
        }
        m.setEnabledProfiles(enabled);
        // Auswahl dauerhaft speichern (options.txt), dann Ressourcen neu laden
        mc.options.resourcePacks.removeIf(Styles::isOurs);
        mc.options.resourcePacks.addAll(ours);
        mc.options.write();
        mc.reloadResources();
        applied.clear();
        applied.putAll(pending);
    }

    private int changes() {
        int n = 0;
        for (Styles.Category c : Styles.CATEGORIES)
            if (!pending.getOrDefault(c.id(), -1).equals(applied.getOrDefault(c.id(), -1))) n++;
        return n;
    }

    // ------------------------------------------------------------ layout
    private int[] rowRect(int i) {
        return new int[]{px + 8, py + 34 + i * rowH, SIDE_W - 8, rowH - 2};
    }

    private int[] cardRect(int j) {
        int rx = px + SIDE_W + 10, rw = pw - SIDE_W - 20;
        int cardW = (rw - 16) / 3;
        int avail = ph - 34 - 82;
        int cardH = Math.min(90, (avail - 16) / 3);
        int col = j % 3, row = j / 3;
        return new int[]{rx + col * (cardW + 8), py + 34 + row * (cardH + 8), cardW, cardH};
    }

    private static boolean in(int[] r, double mx, double my) {
        return mx >= r[0] && mx < r[0] + r[2] && my >= r[1] && my < r[1] + r[3];
    }

    private static Identifier preview(Styles.Category c, Styles.Style s) {
        return Identifier.of(Styles.MOD_ID, "textures/gui/preview/" + Styles.packName(c, s) + ".png");
    }

    private static int withAlpha(int argb, int a) {
        return (a << 24) | (argb & 0xFFFFFF);
    }

    // ------------------------------------------------------------ zeichnen (nur einfache, stabile Methoden)
    private static void border(DrawContext c, int x, int y, int w, int h, int col) {
        c.fill(x, y, x + w, y + 1, col);
        c.fill(x, y + h - 1, x + w, y + h, col);
        c.fill(x, y, x + 1, y + h, col);
        c.fill(x + w - 1, y, x + w, y + h, col);
    }

    private void text(DrawContext c, String s, int x, int y, int col) {
        c.drawText(textRenderer, s, x, y, col, true);
    }

    private void centered(DrawContext c, String s, int cx, int y, int col) {
        text(c, s, cx - textRenderer.getWidth(s) / 2, y, col);
    }

    /** 16x16-Textur, skaliert auf size x size (size = Vielfaches von 16 sieht am schärfsten aus). */
    private static void icon(DrawContext c, Identifier id, int x, int y, int size) {
        float k = size / 16f;
        var m = c.getMatrices();
        m.pushMatrix();
        m.translate((float) x, (float) y);
        m.scale(k, k);
        c.drawTexture(RenderPipelines.GUI_TEXTURED, id, 0, 0, 0f, 0f, 16, 16, 16, 16);
        m.popMatrix();
    }

    // ------------------------------------------------------------ render
    @Override
    public void render(DrawContext ctx, int mx, int my, float delta) {
        for (int y = 0; y < height; y += 4) {
            float t = y / (float) height;
            int r = (int) (8 + 14 * t), g = (int) (8 + 2 * t), b = (int) (18 + 22 * t);
            ctx.fill(0, y, width, Math.min(height, y + 4), 0xE0000000 | (r << 16) | (g << 8) | b);
        }
        ctx.fill(px, py, px + pw, py + ph, 0xF00E0E1C);
        border(ctx, px, py, pw, ph, 0xFF2A2A44);

        // Titel + Farbleiste
        text(ctx, "VinAbi Styles", px + 12, py + 10, 0xFFFFFFFF);
        int seg = pw / Styles.STYLES.size();
        for (int i = 0; i < Styles.STYLES.size(); i++) {
            ctx.fill(px + i * seg, py + 26, px + (i + 1) * seg, py + 28, Styles.STYLES.get(i).color());
        }
        int ch = changes();
        if (ch > 0) {
            String t = ch + (ch == 1 ? " Änderung – Anwenden drücken" : " Änderungen – Anwenden drücken");
            text(ctx, t, px + pw - textRenderer.getWidth(t) - 12, py + 10, 0xFFFFD166);
        }

        // Sidebar
        ctx.fill(px + 4, py + 32, px + SIDE_W, py + 32 + rowH * Styles.CATEGORIES.size() + 2, 0xFF12121F);
        for (int i = 0; i < Styles.CATEGORIES.size(); i++) {
            Styles.Category c = Styles.CATEGORIES.get(i);
            int[] r = rowRect(i);
            boolean hover = in(r, mx, my), sel = i == selCat;
            int idx = pending.getOrDefault(c.id(), -1);
            int accent = idx >= 0 ? Styles.STYLES.get(idx).color() : 0xFF555570;
            if (sel) {
                ctx.fill(r[0], r[1], r[0] + r[2], r[1] + r[3], withAlpha(accent, 0x55));
                ctx.fill(r[0], r[1], r[0] + 2, r[1] + r[3], accent);
            } else if (hover) {
                ctx.fill(r[0], r[1], r[0] + r[2], r[1] + r[3], 0x33FFFFFF);
            }
            int ic = 16;
            int iy = r[1] + (r[3] - ic) / 2;
            if (idx >= 0) {
                icon(ctx, preview(c, Styles.STYLES.get(idx)), r[0] + 5, iy, ic);
            } else {
                ctx.fill(r[0] + 5, iy + 2, r[0] + 5 + ic, iy + ic - 2, 0xFF2C2C3C);
            }
            text(ctx, c.label(), r[0] + 9 + ic, r[1] + (r[3] - 8) / 2, sel ? 0xFFFFFFFF : 0xFFB8B8CC);
            if (idx >= 0) ctx.fill(r[0] + r[2] - 7, r[1] + r[3] / 2 - 2, r[0] + r[2] - 3, r[1] + r[3] / 2 + 2, accent);
        }

        // Karten
        Styles.Category cat = Styles.CATEGORIES.get(selCat);
        int rx = px + SIDE_W + 10;
        text(ctx, cat.label() + " – Style wählen", rx, py + 34 - 12, 0xFFE8E8FF);
        int selected = pending.getOrDefault(cat.id(), -1);
        int live = applied.getOrDefault(cat.id(), -1);
        double pulse = 0.65 + 0.35 * Math.sin(Util.getMeasuringTimeMs() / 260.0);

        for (int j = 0; j <= Styles.STYLES.size(); j++) {
            int[] r = cardRect(j);
            int styleIdx = j - 1;
            boolean hover = in(r, mx, my), sel = styleIdx == selected;
            int accent = styleIdx >= 0 ? Styles.STYLES.get(styleIdx).color() : 0xFF8A8AA0;

            ctx.fill(r[0], r[1], r[0] + r[2], r[1] + r[3], hover ? 0xFF24243A : 0xFF191928);
            if (sel) {
                ctx.fill(r[0], r[1], r[0] + r[2], r[1] + r[3], withAlpha(accent, 0x30));
                int a = (int) (0xFF * pulse);
                border(ctx, r[0], r[1], r[2], r[3], withAlpha(accent, a));
                border(ctx, r[0] + 1, r[1] + 1, r[2] - 2, r[3] - 2, withAlpha(accent, a / 2));
            } else {
                border(ctx, r[0], r[1], r[2], r[3], hover ? 0xFF5A5A80 : 0xFF2A2A44);
            }

            int size = (r[3] - 26 >= 32 && r[2] - 16 >= 32) ? 32 : 16;
            int ix = r[0] + (r[2] - size) / 2, iy = r[1] + 6;
            if (styleIdx >= 0) {
                icon(ctx, preview(cat, Styles.STYLES.get(styleIdx)), ix, iy, size);
            } else {
                ctx.fill(ix, iy, ix + size, iy + size, 0xFF2C2C3C);
                border(ctx, ix, iy, size, size, 0xFF55556E);
                centered(ctx, "MC", ix + size / 2, iy + size / 2 - 4, 0xFF8A8AA0);
            }
            String label = styleIdx >= 0 ? Styles.STYLES.get(styleIdx).label() : "Vanilla";
            centered(ctx, label, r[0] + r[2] / 2, r[1] + r[3] - 13, sel ? 0xFFFFFFFF : accent);
            if (styleIdx == live) {
                text(ctx, "aktiv", r[0] + 4, r[1] + 4, 0xFF6BFF8A);
            }
        }

        super.render(ctx, mx, my, delta); // Buttons
    }

    // ------------------------------------------------------------ input
    @Override
    public boolean mouseClicked(Click click, boolean doubled) {
        double mx = click.x(), my = click.y();
        if (click.button() == 0) {
            for (int i = 0; i < Styles.CATEGORIES.size(); i++) {
                if (in(rowRect(i), mx, my)) {
                    selCat = i;
                    return true;
                }
            }
            for (int j = 0; j <= Styles.STYLES.size(); j++) {
                if (in(cardRect(j), mx, my)) {
                    pending.put(Styles.CATEGORIES.get(selCat).id(), j - 1);
                    return true;
                }
            }
        }
        return super.mouseClicked(click, doubled);
    }

    @Override
    public boolean keyPressed(KeyInput input) {
        int keyCode = input.key();
        if (keyCode == GLFW.GLFW_KEY_RIGHT_SHIFT) {
            close();
            return true;
        }
        if (keyCode == GLFW.GLFW_KEY_UP || keyCode == GLFW.GLFW_KEY_DOWN) {
            int n = Styles.CATEGORIES.size();
            selCat = (selCat + (keyCode == GLFW.GLFW_KEY_DOWN ? 1 : n - 1)) % n;
            return true;
        }
        return super.keyPressed(input);
    }
}
