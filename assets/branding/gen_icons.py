#!/usr/bin/env python3
"""Generates the gpModeler icons/logos (original artwork) in place.

Usage: python3 assets/branding/gen_icons.py   (run from the repository root; requires Pillow)

Palette and typeface follow the Apache Cloudberry brand guide
(https://cloudberry.apache.org/community/brand/): Berry Orange, Berry Yellow,
black, white and the Montserrat typeface. The artwork itself is our own: the
Apache Cloudberry logo and logomark are trademarks of the ASF and must not be
altered, recreated or used as the gpModeler logo.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Colors taken from the official Apache Cloudberry logo artwork
BERRY_ORANGE = (255, 89, 0)    # #FF5900
BERRY_ORANGE_2 = (254, 124, 25)  # #FE7C19
BERRY_YELLOW = (255, 170, 0)   # #FFAA00
BLACK = (26, 24, 23)           # #1A1817, the dark theme window color
GRAY = (118, 118, 118)         # #767676, secondary text readable on dark and light themes
WHITE = (255, 255, 255)

FONT_DIR = "libs/libgui/res/fonts/"
BOLD = FONT_DIR + "montserrat-bold.ttf"
REGULAR = FONT_DIR + "montserrat.ttf"
S = 1024  # working canvas size, downscaled at the end


def font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight:
        # montserrat.ttf is a variable font, pick the requested instance
        f.set_variation_by_name(weight)
    return f


def diagonal_gradient(size, start, end):
    """Bottom-left (start) to top-right (end) gradient."""
    w, h = size
    img = Image.new("RGBA", size)
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = (x / (w - 1) + (1 - y / (h - 1))) / 2
            px[x, y] = tuple(int(start[i] + (end[i] - start[i]) * t) for i in range(3)) + (255,)
    return img


def tile_mask(size=S, margin=64, radius=230):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle((margin, margin, size - margin, size - margin), radius=radius, fill=255)
    return m


def logo(badge=None):
    mask = tile_mask()
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    # soft shadow
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 90), (0, 16), mask.filter(ImageFilter.GaussianBlur(20)))
    img = Image.alpha_composite(img, shadow)

    body = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    body.paste(diagonal_gradient((S, S), BERRY_ORANGE, BERRY_YELLOW), (0, 0), mask)
    img = Image.alpha_composite(img, body)

    d = ImageDraw.Draw(img)

    # a small entity-relationship motif: two linked tables in the top-right corner
    for x0, y0 in ((640, 170), (790, 300)):
        d.rounded_rectangle((x0, y0, x0 + 120, y0 + 90), radius=14, outline=WHITE + (235,), width=14)
        d.line((x0 + 8, y0 + 34, x0 + 112, y0 + 34), fill=WHITE + (235,), width=12)
    d.line((760, 215, 850, 215, 850, 300), fill=WHITE + (235,), width=12, joint="curve")

    f = font(BOLD, 520)
    text = "gp"
    bb = d.textbbox((0, 0), text, font=f)
    tx = (S - (bb[2] - bb[0])) // 2 - bb[0]
    ty = 600 - (bb[3] - bb[1]) // 2 - bb[1] + 40
    d.text((tx + 4, ty + 8), text, font=f, fill=(150, 50, 0, 60))
    d.text((tx, ty), text, font=f, fill=WHITE + (255,))

    if badge:
        add_badge(img, badge)
    return img


def add_badge(img, kind):
    d = ImageDraw.Draw(img)
    cx, cy, r = 800, 800, 170
    colors = {"ch": (200, 40, 30), "cli": BLACK, "se": (120, 60, 20)}
    glyph = {"ch": "!", "cli": ">_", "se": "{}"}
    d.ellipse((cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14), fill=WHITE + (255,))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=colors[kind] + (255,))
    f = font(BOLD, 190 if kind != "cli" else 150)
    bb = d.textbbox((0, 0), glyph[kind], font=f)
    d.text((cx - (bb[0] + bb[2]) / 2, cy - (bb[1] + bb[3]) / 2), glyph[kind], font=f, fill=WHITE + (255,))


def doc_icon(label):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1, fold = 170, 90, 854, 934, 190
    d.polygon([(x0, y0 + 40), (x0 + 40, y0), (x1 - fold, y0), (x1, y0 + fold), (x1, y1 - 40), (x1 - 40, y1), (x0 + 40, y1), (x0, y1 - 40)],
              fill=(250, 248, 246, 255), outline=(170, 160, 150, 255))
    d.polygon([(x1 - fold, y0), (x1, y0 + fold), (x1 - fold, y0 + fold)], fill=(225, 218, 210, 255))
    band = diagonal_gradient((x1 - x0, 230), BERRY_ORANGE, BERRY_YELLOW)
    img.paste(band, (x0, 640), band.split()[3])
    small = logo().resize((420, 420), Image.LANCZOS)
    img.alpha_composite(small, (302, 170))
    f = font(BOLD, 170)
    bb = d.textbbox((0, 0), label, font=f)
    d.text(((S - (bb[0] + bb[2])) / 2, 640 + (230 - (bb[3] - bb[1])) / 2 - bb[1]), label, font=f, fill=WHITE + (255,))
    return img


def draw_wordmark(d, x, y, f):
    """'gp' in Berry Orange, 'Modeler' in gray: readable on dark and light themes."""
    d.text((x, y), "gp", font=f, fill=BERRY_ORANGE + (255,))
    d.text((x + d.textlength("gp", font=f), y), "Modeler", font=f, fill=GRAY + (255,))
    return d.textlength("gpModeler", font=f)


def wordmark(width=558, height=119):
    k = 4
    img = Image.new("RGBA", (width * k, height * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(BOLD, int(height * k * 0.72))
    bb = d.textbbox((0, 0), "gpModeler", font=f)
    draw_wordmark(d, (width * k - (bb[2] - bb[0])) / 2 - bb[0], (height * k - (bb[3] - bb[1])) / 2 - bb[1], f)
    return img.resize((width, height), Image.LANCZOS)


def splash(size=599):
    k = 2
    img = Image.new("RGBA", (size * k, size * k), (0, 0, 0, 0))
    lg = logo().resize((int(size * k * 0.6), int(size * k * 0.6)), Image.LANCZOS)
    img.alpha_composite(lg, ((size * k - lg.width) // 2, int(size * k * 0.02)))
    d = ImageDraw.Draw(img)

    f = font(BOLD, 100 * k)
    bb = d.textbbox((0, 0), "gpModeler", font=f)
    draw_wordmark(d, (size * k - (bb[2] - bb[0])) / 2 - bb[0], 395 * k, f)

    f2 = font(REGULAR, 28 * k, b"SemiBold")
    sub = "for Greenplum & Apache Cloudberry"
    bb = d.textbbox((0, 0), sub, font=f2)
    d.text(((size * k - (bb[2] - bb[0])) / 2 - bb[0], 530 * k), sub, font=f2, fill=GRAY + (255,))
    return img.resize((size, size), Image.LANCZOS)


def save_png(img, path, size):
    img.resize((size, size), Image.LANCZOS).save(path)


def save_ico(img, path):
    img.resize((256, 256), Image.LANCZOS).save(path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def save_icns(img, path):
    img.resize((512, 512), Image.LANCZOS).save(path, format="ICNS")


if __name__ == "__main__":
    app, dbm, sch = logo(), doc_icon("DBM"), doc_icon("SCH")

    save_png(app, "assets/conf/pgmodeler_logo.png", 256)
    save_png(dbm, "assets/conf/pgmodeler_dbm.png", 256)
    save_png(sch, "assets/conf/pgmodeler_sch.png", 256)
    save_png(app, "libs/libgui/res/icons/pgmodeler_logo.png", 128)
    save_png(app, "libs/libgui/res/icons/welcome.png", 128)
    wordmark().save("libs/libgui/res/images/pgmodeler_name.png")
    splash().save("libs/libgui/res/images/pgmodeler_splash.png")

    save_ico(app, "apps/pgmodeler/res/pgmodeler.ico")
    save_ico(dbm, "apps/pgmodeler/res/pgmodeler_dbm.ico")
    save_ico(logo("ch"), "apps/pgmodeler-ch/res/pgmodeler_ch.ico")
    save_ico(logo("cli"), "apps/pgmodeler-cli/res/pgmodeler_cli.ico")
    save_ico(logo("se"), "apps/pgmodeler-se/res/pgmodeler_se.ico")
    save_icns(app, "apps/pgmodeler/res/Resources/pgmodeler.icns")
    save_icns(dbm, "apps/pgmodeler/res/Resources/pgmodeler_dbm.icns")
    print("done")
