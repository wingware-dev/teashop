"""The shop in a real browser: every kind of page at phone and desktop
widths in the light and dark themes, with the WCAG 2.2 AA checks and
screenshots (apps/core/uitesting.py), and the theme button, menus and
filters driven by hand."""

import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image, ImageDraw

from apps.catalog.models import Product, ProductPhoto
from apps.core.uitesting import BrowserTestCase
from apps.storefront import demo
from apps.storefront.models import PageVariant


def stand_in_photo(color, size=(1200, 900)):
    """A drawn stand-in for the owner's product photo (a tin on a table)."""
    image = Image.new("RGB", size, (236, 226, 208))
    draw = ImageDraw.Draw(image)
    w, h = size
    draw.rectangle([0, int(h * 0.7), w, h], fill=(150, 112, 78))
    draw.rounded_rectangle([int(w * 0.35), int(h * 0.25), int(w * 0.65), int(h * 0.78)], radius=30, fill=color)
    draw.rectangle([int(w * 0.35), int(h * 0.25), int(w * 0.65), int(h * 0.33)], fill=(90, 90, 90))
    draw.ellipse([int(w * 0.1), int(h * 0.55), int(w * 0.3), int(h * 0.75)], fill=(122, 79, 44))
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=85)
    return buffer.getvalue()


@override_settings(STOREFRONT_OPEN=True, ROOT_URLCONF="apps.storefront.tests.media_urls")
class ShopUITests(BrowserTestCase):
    def setUp(self):
        super().setUp()
        self.media = tempfile.mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.media)
        self.media_override.enable()
        demo.load(owner=self.owner()[0])

    def tearDown(self):
        self.media_override.disable()
        shutil.rmtree(self.media, ignore_errors=True)
        super().tearDown()

    def add_photos(self, slug):
        product = Product.objects.get(slug=slug)
        for order, (color, alt) in enumerate([((47, 95, 167), "A blue tea tin on a wooden table"),
                                              ((192, 57, 43), "A red tea tin beside a dish of loose leaves")]):
            ProductPhoto.objects.create(product=product, sort_order=order, alt_text=alt,
                                        image=SimpleUploadedFile(f"photo{order}.jpg", stand_in_photo(color)))
        return product

    # -- Pages ---------------------------------------------------------

    def test_home(self):
        self.check_page("/", "shop-home")

    def test_all_teas(self):
        self.check_page(reverse("storefront:all_teas"), "teas-all")

    def test_category(self):
        self.check_page("/teas/black/", "teas-category-black")

    def test_herbal_category(self):
        self.check_page("/teas/herbal/", "teas-category-herbal")

    def test_filtered_listing(self):
        self.check_page("/teas/?note=honey&caffeine=low&caffeine=medium&sort=price", "teas-filtered")

    def test_no_results(self):
        self.check_page("/search/?q=nothing-like-this", "search-no-results", viewports=["phone"])

    def test_search(self):
        self.check_page("/search/?q=honey", "search-results")

    def test_regions(self):
        self.check_page(reverse("storefront:regions"), "regions")

    def test_region(self):
        self.check_page("/regions/darjeeling/", "region-darjeeling")

    def test_collection(self):
        self.check_page("/collections/this-weeks-picks/", "collection-this-weeks-picks")

    def test_product_with_photos(self):
        product = self.add_photos("earl-grey-cornflower")
        self.check_page(product.get_absolute_url(), "product-photos")

    def test_product_with_allergens(self):
        self.check_page("/products/vanilla-almond-black/", "product-allergens")

    def test_organic_product(self):
        product = Product.objects.get(slug="assam-second-flush")
        product.sold_as_organic = True
        product.save()
        product.tea.lots.update(organic=True)
        self.check_page(product.get_absolute_url(), "product-organic")

    def test_herbal_product(self):
        self.check_page("/products/chamomile-meadow/", "product-herbal")

    def test_product_with_live_wide_design(self):
        self.check_page("/products/silver-needle/", "product-design-wide")

    def test_merch_section(self):
        self.check_page(reverse("storefront:goods"), "merch")

    def test_merch_product(self):
        self.check_page("/products/glass-teapot/", "merch-product")

    def test_tea_notes(self):
        self.check_page(reverse("storefront:articles"), "tea-notes")

    def test_tea_note(self):
        self.check_page("/tea-notes/how-black-tea-gets-its-colour/", "tea-note")

    # -- The owner's side of page designs ------------------------------

    def test_design_list(self):
        self.check_page(reverse("storefront:variant_list"), "owner-page-designs", signed_in=True)

    def test_design_preview_and_approve(self):
        draft = PageVariant.objects.get(product__slug="assam-second-flush")
        self.check_page(draft.get_absolute_url(), "owner-page-design-preview", signed_in=True)
        page = self.new_page("desktop", "light", signed_in=True)
        page.goto(self.url(draft.get_absolute_url()))
        page.get_by_label("Note (optional)").fill("Looks good")
        page.get_by_role("button", name="Approve and make live").click()
        page.wait_for_url(self.url(reverse("storefront:variant_list")))
        self.check_current(page, "owner-page-designs-after-approve")
        draft.refresh_from_db()
        self.assertEqual(draft.status, PageVariant.Status.LIVE)
        customer = self.new_page("phone", "light")
        customer.goto(self.url("/products/assam-second-flush/"))
        self.assertTrue(customer.get_by_text("Malty, brisk and generous with milk").is_visible())
        self.check_current(customer, "product-design-story")

    # -- Behaviour -----------------------------------------------------

    def background(self, page):
        return page.evaluate("getComputedStyle(document.body).backgroundColor")

    def test_theme_follows_device_then_button_overrides_and_persists(self):
        page = self.new_page("desktop", "light")
        page.goto(self.url("/"))
        light = self.background(page)
        button = page.get_by_role("button", name="Theme: Automatic")
        self.assertTrue(button.is_visible())
        button.click()
        self.assertTrue(page.get_by_role("button", name="Theme: Dark").is_visible())
        dark = self.background(page)
        self.assertNotEqual(light, dark)
        page.reload()
        self.assertEqual(self.background(page), dark)  # remembered, and no flash of light first
        self.assertEqual(page.evaluate("document.documentElement.dataset.theme"), "dark")
        self.check_current(page, "theme-chosen-dark", theme="dark")
        page.get_by_role("button", name="Theme: Dark").click()  # -> light, on a dark device or not
        self.assertEqual(self.background(page), light)
        page.get_by_role("button", name="Theme: Light").click()  # -> automatic: the device's light
        self.assertEqual(self.background(page), light)
        self.assertIsNone(page.evaluate("localStorage.getItem('theme')"))

    def test_device_dark_with_light_chosen(self):
        page = self.new_page("phone", "dark")
        page.goto(self.url("/"))
        dark = self.background(page)
        page.get_by_role("button", name="Theme: Automatic").click()  # -> dark (no change)
        page.get_by_role("button", name="Theme: Dark").click()  # -> light
        self.assertNotEqual(self.background(page), dark)
        self.check_current(page, "theme-chosen-light-on-dark-device", theme="light")

    def test_teas_menu_by_keyboard(self):
        page = self.new_page("desktop", "light")
        page.goto(self.url("/"))
        summary = page.locator("details.menu > summary")
        summary.focus()
        page.keyboard.press("Enter")
        link = page.get_by_role("link", name="Oolong", exact=True).first
        is_open = "document.querySelector('details.menu').open"
        self.assertTrue(link.is_visible())
        self.assertTrue(page.evaluate(is_open))
        page.keyboard.press("Escape")
        # Ask the menu: once it closes, a role locator skips its hidden links
        # and finds the page's own "Oolong" tile instead.
        self.assertFalse(page.evaluate(is_open))
        self.assertEqual(page.evaluate("document.activeElement.tagName"), "SUMMARY")
        page.keyboard.press("Enter")
        self.assertTrue(page.evaluate(is_open))
        self.check_current(page, "menu-teas-open")

    def test_filtering_on_a_phone(self):
        page = self.new_page("phone", "light")
        page.goto(self.url("/teas/"))
        page.get_by_text("Filter and sort").click()
        page.get_by_label("None (caffeine-free)").check()
        page.get_by_role("button", name="Show teas").click()
        page.wait_for_url("**caffeine=none**")
        names = page.locator(".product-card h3").all_inner_texts()
        self.assertEqual(sorted(names), ["Chamomile Meadow Herbal Tea", "Hibiscus Berry Tisane"])
        self.check_current(page, "teas-filtered-phone")

    def test_skip_link(self):
        page = self.new_page("desktop", "light")
        page.goto(self.url("/teas/"))
        page.keyboard.press("Tab")
        skip = page.get_by_role("link", name="Skip to main content")
        self.assertTrue(skip.is_visible())
        page.keyboard.press("Enter")
        self.assertEqual(page.evaluate("document.activeElement.id"), "main")


@override_settings(STOREFRONT_OPEN=False)
class ClosedShopUITests(BrowserTestCase):
    def test_coming_soon(self):
        self.check_page("/", "coming-soon")
