"""The storefront design system's vocabulary: the motifs and accent
palettes that sections, products and AI-made page variants choose from.

Variants pick from these names only, never free-form colours or images,
so every page stays inside the common theme and keeps its contrast: each
palette is defined once in static/css/site.css (``.palette-<name>``) for
both the light and dark themes and checked by the browser tests.  Each
motif is a symbol in static/img/motifs.svg (``#motif-<name>``).

To add one: add it here, add its CSS or SVG symbol, and run the browser
tests.
"""

MOTIFS = [
    ("leaf", "Tea leaf"),
    ("sprig", "Two leaves and a bud"),
    ("blossom", "Blossom"),
    ("bee", "Bee"),
    ("butterfly", "Butterfly"),
    ("bird", "Songbird"),
    ("fern", "Fern"),
    ("teapot", "Teapot"),
]
MOTIF_NAMES = [name for name, _ in MOTIFS]

PALETTES = [
    ("moss", "Moss green"),
    ("bark", "Bark brown"),
    ("poppy", "Poppy red"),
    ("cornflower", "Cornflower blue"),
    ("buttercup", "Buttercup yellow"),
    ("plum", "Plum"),
]
PALETTE_NAMES = [name for name, _ in PALETTES]

# Page layouts a product page variant can use (storefront/product.html).
LAYOUTS = [
    ("classic", "Photos beside the facts"),
    ("story", "Story first, then the facts"),
    ("wide", "Wide photo across the top"),
]
LAYOUT_NAMES = [name for name, _ in LAYOUTS]
