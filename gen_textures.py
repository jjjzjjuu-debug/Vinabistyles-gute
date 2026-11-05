import os, sys, random, zlib, json
from PIL import Image

PAL = {
    'neon':  dict(main=(176, 64, 255), dark=(26, 8, 46),  mid=(88, 28, 148),  light=(236, 170, 255)),
    'lava':  dict(main=(255, 86, 24),  dark=(44, 8, 6),   mid=(150, 34, 12),  light=(255, 206, 96)),
    'ice':   dict(main=(64, 204, 255), dark=(8, 20, 44),  mid=(24, 90, 150),  light=(214, 248, 255)),
    'toxic': dict(main=(90, 255, 80),  dark=(8, 32, 10),  mid=(30, 130, 34),  light=(220, 255, 170)),
    'gold':  dict(main=(255, 200, 40), dark=(40, 28, 4),  mid=(150, 105, 10), light=(255, 240, 150)),
    'sakura': dict(main=(255, 110, 180), dark=(46, 10, 30), mid=(150, 40, 100), light=(255, 210, 235)),
    'ocean': dict(main=(20, 210, 190), dark=(4, 30, 34),  mid=(10, 110, 110), light=(190, 255, 245)),
    'void':  dict(main=(200, 200, 215), dark=(8, 8, 12),  mid=(60, 60, 78),   light=(250, 250, 255)),
}
WHITE = (255, 255, 255)


def new(w, h):
    return Image.new('RGBA', (w, h), (0, 0, 0, 0))


def solid(w, h):
    return Image.new('RGBA', (w, h), (0, 0, 0, 255))


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def put(im, x, y, c, a=255):
    if 0 <= x < im.width and 0 <= y < im.height:
        im.putpixel((x, y), (c[0], c[1], c[2], a))


def rect(im, x0, y0, x1, y1, c, a=255):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(im, x, y, c, a)


def frame(im, x0, y0, x1, y1, c):
    for x in range(x0, x1 + 1):
        put(im, x, y0, c); put(im, x, y1, c)
    for y in range(y0, y1 + 1):
        put(im, x0, y, c); put(im, x1, y, c)


def line(im, x0, y0, x1, y1, c, a=255):
    dx = abs(x1 - x0); dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        put(im, x0, y0, c, a)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy


def outline(im, c):
    src = im.copy()
    for y in range(im.height):
        for x in range(im.width):
            if src.getpixel((x, y))[3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < im.width and 0 <= ny < im.height and src.getpixel((nx, ny))[3] > 0:
                        put(im, x, y, c)
                        break


def smooth_noise(w, h, r, cell):
    gw, gh = w // cell + 2, h // cell + 2
    grid = [[r.random() for _ in range(gw)] for _ in range(gh)]

    def f(x, y):
        gx, gy = x / cell, y / cell
        x0, y0 = int(gx), int(gy)
        tx, ty = gx - x0, gy - y0
        a = grid[y0][x0] * (1 - tx) + grid[y0][x0 + 1] * tx
        b = grid[y0 + 1][x0] * (1 - tx) + grid[y0 + 1][x0 + 1] * tx
        return a * (1 - ty) + b * ty
    return f


# ---------------------------------------------------------------- blocks
def dark_base(p, r, w=16, h=16, cell=4, lo=0.1, hi=0.5):
    im = solid(w, h)
    n = smooth_noise(w, h, r, cell)
    for y in range(h):
        for x in range(w):
            t = 0.6 * n(x, y) + 0.4 * r.random()
            put(im, x, y, lerp(p['dark'], p['mid'], lo + (hi - lo) * t))
    return im


def g_obsidian(p, r):
    im = dark_base(p, r)
    for _ in range(3):
        x, y = r.randrange(16), r.randrange(16)
        for _ in range(r.randint(6, 11)):
            put(im, x % 16, y % 16, p['light'] if r.random() < 0.3 else p['main'])
            x += r.choice([-1, 0, 1, 1]); y += r.choice([-1, 0, 1, 1])
    cry = dark_base(p, r)
    for x in range(1, 15, 3):
        top = r.randint(2, 6)
        for y in range(top, top + r.randint(5, 9)):
            put(cry, x, y, p['main'] if y % 3 else p['light'])
            if r.random() < 0.5: put(cry, x + 1, y, p['mid'])
    return {'block/obsidian.png': im, 'block/crying_obsidian.png': cry}


def g_glowstone(p, r):
    im = solid(16, 16)
    n = smooth_noise(16, 16, r, 3)
    for y in range(16):
        for x in range(16):
            c = lerp(p['main'], p['light'], n(x, y))
            if r.random() < 0.10: c = lerp(c, p['mid'], 0.55)
            if r.random() < 0.05: c = lerp(c, WHITE, 0.6)
            put(im, x, y, c)
    dust = new(16, 16)
    for row, hw in enumerate((1, 2, 3, 4, 5, 5)):
        for x in range(8 - hw, 8 + hw):
            y = 7 + row
            t = r.random()
            put(dust, x, y, p['light'] if t < 0.3 else (p['main'] if t < 0.8 else p['mid']))
    for x, y in ((8, 7), (6, 9), (10, 10)):
        put(dust, x, y, WHITE)
    outline(dust, p['dark'])
    return {'block/glowstone.png': im, 'item/glowstone_dust.png': dust}


def g_cobweb(p, r):
    im = new(16, 16)
    c = lerp(WHITE, p['light'], 0.55)
    dirs = [(0, 0), (7, 0), (15, 0), (0, 7), (15, 7), (0, 15), (7, 15), (15, 15)]
    for ex, ey in dirs:
        line(im, 7, 7, ex, ey, c, 235)
    for rad in (3, 6):
        pts = [(7 + round(rad * dx), 7 + round(rad * dy)) for dx, dy in
               ((0, -1), (.7, -.7), (1, 0), (.7, .7), (0, 1), (-.7, .7), (-1, 0), (-.7, -.7))]
        for i in range(8):
            a, b = pts[i], pts[(i + 1) % 8]
            line(im, a[0], a[1], b[0], b[1], c, 220)
    for _ in range(5):
        put(im, r.randrange(2, 14), r.randrange(2, 14), p['main'], 255) if False else None
    for x, y in ((7, 7), (8, 8), (3, 3), (12, 12)):
        put(im, x, y, p['main'])
    return {'block/cobweb.png': im}


def g_anchor(p, r):
    out = {'block/respawn_anchor_bottom.png': dark_base(p, r)}
    for name, glow in (('top', True), ('top_off', False)):
        im = dark_base(p, r)
        frame(im, 0, 0, 15, 15, p['mid'])
        frame(im, 3, 3, 12, 12, p['main'] if glow else p['mid'])
        if glow:
            rect(im, 5, 5, 10, 10, p['light'])
            rect(im, 6, 6, 9, 9, WHITE)
        out[f'block/respawn_anchor_{name}.png'] = im
    for n in range(5):
        im = dark_base(p, r)
        rect(im, 0, 0, 15, 1, p['mid']); rect(im, 0, 14, 15, 15, p['mid'])
        for i in range(n):
            y = 11 - 3 * i
            rect(im, 3, y, 12, y + 1, p['main'])
            rect(im, 3, y, 12, y, p['light'])
        out[f'block/respawn_anchor_side{n}.png'] = im
    return out


# ---------------------------------------------------------------- entities
def g_crystal(p, r):
    im = solid(64, 32)
    n = smooth_noise(64, 32, r, 4)
    for y in range(32):
        for x in range(64):
            d = abs((x % 8) - 3.5) + abs((y % 8) - 3.5)
            if d < 1.6: c = p['light']
            elif d < 3.4: c = lerp(p['main'], p['light'], n(x, y) * 0.5)
            elif d < 5: c = lerp(p['mid'], p['main'], 0.4 + 0.4 * n(x, y))
            else: c = p['mid']
            if y >= 16: c = lerp(p['dark'], c, 0.35)
            put(im, x, y, c)
    return {'entity/end_crystal/end_crystal.png': im, 'item/end_crystal.png': pv_crystal(p, r)}


def armor_tex(p, r):
    im = solid(64, 32)
    n = smooth_noise(64, 32, r, 6)
    for y in range(32):
        for x in range(64):
            c = lerp(p['dark'], p['mid'], 0.25 + 0.5 * n(x, y))
            if x % 4 == 0 or y % 4 == 0: c = lerp(c, p['dark'], 0.5)
            elif x % 4 == 1 and y % 4 == 1: c = lerp(c, p['light'], 0.35)
            if y % 8 == 7: c = p['main']
            if r.random() < 0.02: c = p['light']
            put(im, x, y, c)
    return im


def shade_edges(im, p):
    src = im.copy()
    for y in range(im.height):
        for x in range(im.width):
            if src.getpixel((x, y))[3]:
                left = x == 0 or src.getpixel((x - 1, y))[3] == 0
                up = y == 0 or src.getpixel((x, y - 1))[3] == 0
                right = x == im.width - 1 or src.getpixel((x + 1, y))[3] == 0
                down = y == im.height - 1 or src.getpixel((x, y + 1))[3] == 0
                if left or up: put(im, x, y, p['light'])
                elif right or down: put(im, x, y, p['mid'])


def armor_icons(p):
    out = {}
    h = new(16, 16)
    rect(h, 3, 3, 12, 12, p['main']); rect(h, 5, 8, 10, 12, (0, 0, 0), 0)
    for x, y in ((3, 3), (12, 3)): h.putpixel((x, y), (0, 0, 0, 0))
    rect(h, 6, 5, 9, 5, p['light'])
    out['helmet'] = h
    c = new(16, 16)
    rect(c, 4, 2, 11, 14, p['main']); rect(c, 1, 3, 3, 9, p['main']); rect(c, 12, 3, 14, 9, p['main'])
    rect(c, 6, 2, 9, 3, (0, 0, 0), 0); rect(c, 7, 6, 8, 11, p['light'])
    out['chestplate'] = c
    l = new(16, 16)
    rect(l, 4, 2, 11, 5, p['main']); rect(l, 4, 6, 6, 14, p['main']); rect(l, 9, 6, 11, 14, p['main'])
    rect(l, 4, 4, 11, 4, p['light'])
    out['leggings'] = l
    b = new(16, 16)
    rect(b, 2, 5, 5, 10, p['main']); rect(b, 1, 11, 6, 13, p['main'])
    rect(b, 10, 5, 13, 10, p['main']); rect(b, 9, 11, 14, 13, p['main'])
    out['boots'] = b
    for im in out.values():
        shade_edges(im, p)
        outline(im, p['dark'])
    return out


def g_armor(p, r):
    a, b = armor_tex(p, r), armor_tex(p, r)
    out = {}
    icons = armor_icons(p)
    for mat in ('netherite', 'diamond'):
        out[f'entity/equipment/humanoid/{mat}.png'] = a
        out[f'entity/equipment/humanoid_leggings/{mat}.png'] = b
        for piece, im in icons.items():
            out[f'item/{mat}_{piece}.png'] = im
    return out


def g_shield(p, r):
    im = dark_base(p, r, 64, 64, 6, 0.1, 0.45)
    frame(im, 1, 1, 12, 22, p['main'])
    frame(im, 3, 3, 10, 20, p['mid'])
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            d = abs(dx) + abs(dy)
            if d <= 4:
                put(im, 6 + dx, 11 + dy, p['light'] if d <= 1 else p['main'])
    rect(im, 26, 0, 31, 5, p['mid'])
    return {'entity/shield_base_nopattern.png': im, 'entity/shield_base.png': im,
            'entity/shield/shield_base_nopattern.png': im, 'entity/shield/shield_base.png': im}


def g_glint(p, r):
    im = solid(64, 64)
    for y in range(64):
        for x in range(64):
            k = max(0.0, 1 - abs((x + y) % 16 - 8) / 5)
            k2 = max(0.0, 1 - abs((x * 2 + y * 3) % 32 - 16) / 3) * 0.35
            k = min(1.0, k + k2)
            c = lerp(p['main'], p['light'], k * k)
            put(im, x, y, tuple(int(v * k) for v in c))
    return {'misc/enchanted_glint_item.png': im, 'misc/enchanted_glint_entity.png': im,
            'misc/enchanted_item_glint.png': im}


# ---------------------------------------------------------------- items
def g_mace(p, r):
    im = new(16, 16)
    line(im, 2, 14, 8, 8, p['mid']); line(im, 3, 14, 9, 8, p['dark'])
    line(im, 2, 13, 8, 7, p['light'])
    cx, cy = 10, 5
    for y in range(16):
        for x in range(16):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d <= 3.2:
                dx, dy = x - cx, y - cy
                put(im, x, y, p['light'] if dx + dy < -1 else (p['mid'] if dx + dy > 1 else p['main']))
    for x, y in ((10, 1), (14, 5), (6, 5), (10, 9), (13, 2), (7, 2), (13, 8), (7, 8)):
        put(im, x, y, p['light'])
    outline(im, p['dark'])
    return {'item/mace.png': im}


def g_windcharge(p, r):
    im = new(16, 16)
    for arm in (0, 1):
        t = 0.0
        while t < 12.5:
            rad = 1.2 + t * 0.45
            a = t + arm * 3.14159
            x, y = round(7.5 + rad * __import__('math').cos(a)), round(7.5 + rad * __import__('math').sin(a))
            put(im, x, y, p['light'] if int(t * 2) % 2 else p['main'])
            t += 0.25
    for y in range(6, 10):
        for x in range(6, 10):
            if (x - 7.5) ** 2 + (y - 7.5) ** 2 <= 2.9:
                put(im, x, y, WHITE)
    return {'item/wind_charge.png': im}


def g_pearl(p, r):
    im = new(16, 16)
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            if d <= 6.5:
                t = (((x - 5) ** 2 + (y - 5) ** 2) ** 0.5) / 11
                c = lerp(p['light'], p['main'], t * 2) if t < 0.5 else lerp(p['main'], p['dark'], (t - 0.5) * 2)
                if d > 5.6: c = lerp(c, p['dark'], 0.45)
                put(im, x, y, c)
    for x, y in ((4, 4), (5, 4), (4, 5), (5, 3)):
        put(im, x, y, WHITE)
    for x, y in ((9, 9), (10, 8), (10, 10), (8, 10), (9, 11)):
        put(im, x, y, p['main'])
    return {'item/ender_pearl.png': im}


def g_totem(p, r):
    im = new(16, 16)
    rect(im, 5, 1, 10, 5, p['main'])
    rect(im, 2, 6, 13, 8, p['main'])
    rect(im, 5, 6, 10, 12, p['main'])
    rect(im, 5, 13, 7, 14, p['main']); rect(im, 8, 13, 10, 14, p['main'])
    src = im.copy()
    for y in range(16):
        for x in range(16):
            if src.getpixel((x, y))[3]:
                left = x == 0 or src.getpixel((x - 1, y))[3] == 0
                up = y == 0 or src.getpixel((x, y - 1))[3] == 0
                right = x == 15 or src.getpixel((x + 1, y))[3] == 0
                down = y == 15 or src.getpixel((x, y + 1))[3] == 0
                if left or up: put(im, x, y, p['light'])
                elif right or down: put(im, x, y, p['mid'])
    put(im, 6, 3, p['dark']); put(im, 9, 3, p['dark']); put(im, 7, 5, p['dark']); put(im, 8, 5, p['dark'])
    put(im, 7, 9, p['light']); put(im, 8, 9, p['light']); put(im, 7, 10, WHITE); put(im, 8, 10, WHITE)
    outline(im, p['dark'])
    return {'item/totem_of_undying.png': im}


def g_xp(p, r):
    im = new(16, 16)
    rect(im, 6, 1, 9, 2, p['mid'])
    rect(im, 7, 3, 8, 5, lerp(p['light'], WHITE, 0.5))
    glass = lerp(p['light'], WHITE, 0.5)
    for y in range(16):
        for x in range(16):
            v = ((x - 7.5) / 5.5) ** 2 + ((y - 10) / 4.8) ** 2
            if v <= 1:
                if v > 0.72: put(im, x, y, glass)
                else: put(im, x, y, lerp(p['light'], p['main'], (y - 6) / 8))
    for x, y in ((6, 9), (10, 11), (8, 8), (5, 12)):
        put(im, x, y, WHITE)
    outline(im, p['dark'])
    return {'item/experience_bottle.png': im}


GEN = {
    'mace': g_mace, 'crystal': g_crystal, 'obsidian': g_obsidian, 'windcharge': g_windcharge,
    'pearl': g_pearl, 'cobweb': g_cobweb, 'armor': g_armor, 'shield': g_shield,
    'anchor': g_anchor, 'glowstone': g_glowstone, 'glint': g_glint, 'totem': g_totem, 'xpbottle': g_xp,
}


# ---------------------------------------------------------------- previews (16x16)
def pv_crystal(p, r):
    im = new(16, 16)
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            d = abs(dx) + abs(dy)
            if d <= 7.5:
                if d < 1.8: c = WHITE
                elif dx < 0 and dy < 0: c = p['light']
                elif dx >= 0 and dy < 0: c = p['main']
                elif dx < 0: c = p['main']
                else: c = p['mid']
                put(im, x, y, c)
    outline(im, p['dark'])
    return im


def pv_armor(p, r):
    im = new(16, 16)
    rect(im, 3, 2, 12, 12, p['main'])
    rect(im, 5, 7, 10, 12, (0, 0, 0), 0)
    for y in range(2, 13):
        for x in range(3, 13):
            if im.getpixel((x, y))[3]:
                if x == 3 or y == 2: put(im, x, y, p['light'])
                elif x == 12 or y == 6 and x > 10: put(im, x, y, p['mid'])
    for x, y in ((3, 2), (12, 2)):
        im.putpixel((x, y), (0, 0, 0, 0))
    for x in range(6, 10): put(im, x, 4, p['light'])
    outline(im, p['dark'])
    return im


def pv_shield(p, r):
    im = new(16, 16)
    for y in range(1, 15):
        hw = 6 if y < 8 else max(0, 6 - round((y - 7) * 6 / 7))
        for x in range(8 - hw, 8 + hw):
            put(im, x, y, p['mid'])
    for x, y in ((8, 5), (7, 6), (8, 6), (7, 5), (8, 7), (7, 7)):
        put(im, x, y, p['light'])
    outline(im, p['main'])
    return im


def pv_glint(p, r):
    im = solid(16, 16)
    for y in range(16):
        for x in range(16):
            k = max(0.0, 1 - abs((x + y) % 8 - 4) / 3)
            c = lerp(p['dark'], lerp(p['main'], p['light'], k), 0.25 + 0.75 * k)
            put(im, x, y, c)
    return im


PREVIEW = {
    'mace': 'item/mace.png', 'windcharge': 'item/wind_charge.png', 'pearl': 'item/ender_pearl.png',
    'totem': 'item/totem_of_undying.png', 'xpbottle': 'item/experience_bottle.png',
    'obsidian': 'block/obsidian.png', 'glowstone': 'block/glowstone.png', 'cobweb': 'block/cobweb.png',
    'anchor': 'block/respawn_anchor_side4.png',
    'crystal': pv_crystal, 'armor': pv_armor, 'shield': pv_shield, 'glint': pv_glint,
}


def main(root):
    res = os.path.join(root, 'src/main/resources')
    prev_dir = os.path.join(res, 'assets/vinabistyles/textures/gui/preview')
    os.makedirs(prev_dir, exist_ok=True)
    sheet = {}
    for cat, gen in GEN.items():
        for sid, p in PAL.items():
            r = random.Random(zlib.crc32(f'{cat}{sid}'.encode()))
            files = gen(p, r)
            name = f'{cat}_{sid}'
            for rel, im in files.items():
                path = os.path.join(res, 'resourcepacks', name, 'assets/minecraft/textures', rel)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                im.save(path)
            with open(os.path.join(res, 'resourcepacks', name, 'pack.mcmeta'), 'w') as f:
                json.dump({'pack': {'pack_format': 75, 'min_format': 75, 'max_format': 75, 'description': f'VinAbi Styles - {name}'}}, f)
            pv = PREVIEW[cat]
            img = pv(p, r) if callable(pv) else files[pv].copy()
            if img.size != (16, 16):
                img = img.resize((16, 16), Image.NEAREST)
            img.save(os.path.join(prev_dir, f'{name}.png'))
            sheet[(cat, sid)] = img
    # contact sheet for visual check
    cats = list(GEN)
    S = 4
    cs = Image.new('RGBA', (len(PAL) * 17 * S, len(cats) * 17 * S), (60, 60, 70, 255))
    for j, cat in enumerate(cats):
        for i, sid in enumerate(PAL):
            cs.alpha_composite(sheet[(cat, sid)].resize((16 * S, 16 * S), Image.NEAREST), (i * 17 * S, j * 17 * S))
    cs.save('/tmp/contact.png')


if __name__ == '__main__':
    main(sys.argv[1])
