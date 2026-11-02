# The storefront

The public shop (`apps/storefront`, phase 3): home page, teas by kind,
region and collection, search and filters, product pages, merch and
accessories, and the tea notes (info and history) section.  It draws on
the catalog (`apps/catalog`) for products, sizes, categories, regions,
collections, flavour notes and photos, and on inventory for stock,
origin, ingredients and allergens.

Product pages have the add-to-cart form; the cart, checkout, accounts and
subscriptions are `apps/checkout` (see `docs/checkout.md`).  Until
payments and shipping are set up, product pages say "Online ordering
opens soon" instead.  The policy pages (`/policies/...`,
`apps/storefront/policies.py`) are shown even while the shop is closed.

## Opening the shop

Until you set `STOREFRONT_OPEN=true` in `.env` and redeploy, visitors see
only the "coming soon" page, the other shop pages answer "not found",
`robots.txt` asks search engines to stay away and `sitemap.xml` is empty.
Signed in with two-factor, you see the whole shop, so you can try it on
the live server first.  On a laptop the shop is open by default; fill it
with made-up teas to try it:

```sh
.venv/bin/python manage.py load_demo_catalog
.venv/bin/python manage.py runserver
```

The demo catalog is invented and the command refuses to run in
production.

## Adding what the shop shows (admin)

- **Categories** (Catalog → Categories): the shop's sections by kind of
  tea, plus the merch and accessories sections.  The standard ones are
  made for you; rename, reorder, hide or add.  Mark herbal ones "Is
  herbal".
- **Regions**: where teas grow, grouped by country on the Regions page.
- **Collections**: hand-picked lists (Specials, This week's picks, New
  arrivals).  Give one dates to show it only for a while; "Featured" puts
  it on the home page.
- **Flavour notes**: what customers can filter by (malty, floral...).
- **Products**: each has an "In the shop" part (category, region, summary,
  description, tasting notes, flavour notes, caffeine), "Origin" and the
  "Brewing guide".  Sizes get a package type (tin, pouch) for the package
  filter.  Add **your own photos** at the bottom; each needs a description
  for people who can't see it.  Photos are turned upright, stripped of
  their location and other camera data, and made smaller for phones when
  you save.  A product without photos shows decorative art instead, and
  says photos are coming: art never stands in for the product itself.
- **Tea notes** (Storefront → Articles): the info and history section.
  Write plain paragraphs separated by a blank line; a line starting
  `## ` is a subheading.  Not shown until "Is published" and the publish
  date.

Ingredients, allergens and "Grown in" on product pages come from the lots
you are packing from now (Inventory), listing every allergen any of them
declares, so the page never shows less than a package may contain.

## Wording rules the shop checks

The admin refuses to save, and the dashboard flags, customer-facing text
that breaks these rules (`apps/catalog/copy_rules.py`):

- **No health or disease claims** anywhere: no "detox", "boosts
  immunity", "helps you sleep", "soothes a sore throat", "antioxidants"
  and the like.  Describe taste, aroma, origin and brewing instead.  The
  check catches the usual wording, not every possible claim: read new copy
  with this rule in mind.
- **Herbal products** say "herbal tea" or "tisane" in their name.
- **"Caffeine-free"** only when the product's caffeine is set to None.
- **Protected origin names** (Darjeeling, Nilgiri, Kangra, Assam
  Orthodox, Longjing, Dragon Well, Uji by default; `CATALOG_PROTECTED_ORIGINS`
  in `.env` replaces the list) only for products marked "Origin
  certified", with the certificate kept with the lot.  Check the list with
  your suppliers.

## The design system

- **Colours:** browns and greens with poppy red, cornflower blue,
  buttercup yellow and plum.  Each is defined once for the light and once
  for the dark theme in `static/css/site.css`, with text shades that keep
  WCAG AA contrast on either.
- **Light and dark:** pages follow the visitor's device setting; the
  "Theme" button in the header switches between Automatic, Dark and Light
  and remembers the choice in that browser.
- **Motifs:** tea leaf, two leaves and a bud, blossom, bee, butterfly,
  songbird, fern and teapot (`static/img/motifs.svg`), plus the leafy vine
  under the header.  They are decoration.
- **Type:** the device's own fonts (a book serif for headings, the system
  sans-serif for text): nothing to download and no font licences.
- Sections, collections, articles and page designs choose a **palette**
  and **motif** by name from `apps/core/design.py`, so every page stays
  within the theme.

### The logo is yours to make

The header shows the shop's name as plain text (`SHOP_NAME`), not a logo.
Art made only by AI can't be protected by copyright, so the **logo and
key brand marks must be substantially made or modified by a person** (you
or a designer you hire) to be protectable.  The motifs here are
decoration, free to keep or replace; when your logo is ready, put it in
`static/img/` and in the `.brand` link in `templates/base.html`.  Choose
the name after a trademark search (see the Phase 0 checklist).

## Page designs (AI-made variants you approve)

Each tea page can have its own design within the theme: a palette, a
motif, a layout (photos beside the facts; story first; a wide photo
across the top), a headline and a short story.  A design agent proposes
them; **nothing reaches customers until you approve it**.

- Proposals wait under **Dashboard → Page designs to approve**, and the
  dashboard's "Needs your attention" list says how many are waiting.
- Each opens as a preview of the real page.  Approve it to make it live
  (replacing the tea's current design), reject it, or take a live one
  down to go back to the standard design.  Each decision is in the audit
  log.
- A design whose wording breaks the rules above can't be approved; the
  preview lists what to fix.

An agent (or you) proposes designs with a JSON file:

```sh
.venv/bin/python manage.py submit_page_variant designs.json --agent design-agent
```

```json
[{"product": "assam-second-flush", "palette": "bark", "motif": "bird",
  "layout": "story", "headline": "Malty, brisk and generous with milk",
  "story": "Summer in the Brahmaputra valley ...",
  "rationale": "Warm browns for a malty breakfast tea."}]
```

`product` is the product's slug; `palette`, `motif` and `layout` must be
names from `apps/core/design.py`.  The command saves nothing if any
design fails a check, and records each proposal in the audit log as the
agent's.

## Search engines

Product pages carry schema.org Product data (prices, sizes, stock,
origin), every page has breadcrumbs data, and the home page describes the
shop and its search.  `/sitemap.xml` lists every shop page once the shop
is open; `/robots.txt` points to it and keeps search engines out of the
owner pages and search results.

## Accessibility and speed

Every shop page has a browser test (`apps/storefront/tests/test_ui.py`)
that checks it at phone and desktop widths in both themes against WCAG
2.2 AA with axe-core, for sideways scrolling at 320 pixels, and for
errors.  Beyond what axe checks: a skip link, visible focus, keyboard
menus that close with Escape, touch targets of at least 24 pixels, and
filters that apply only when asked.  Pages load one stylesheet, two
small scripts and one cached image sprite; product photos come in sizes
for phones (`srcset`) and load lazily below the fold.
