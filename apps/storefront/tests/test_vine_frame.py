"""The vine frame: customer pages wear it, owner pages don't, and its
drawings in the motif sprite are where the template tag and vines.js
expect them."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.core.testing import login_verified, make_owner
from apps.storefront import demo
from apps.storefront.templatetags.storefront import ORNAMENT_BOXES, ornament

STATIC = Path(settings.BASE_DIR) / "static"
SVG_NS = "{http://www.w3.org/2000/svg}"


def wears_frame(response):
    html = response.content.decode()
    return "data-vines=" in html and "js/vines.js" in html and 'class="shop' in html


@override_settings(STOREFRONT_OPEN=True)
class VineFrameTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        demo.load()

    def test_customer_pages_wear_the_frame(self):
        for url in ["/", "/teas/", "/products/assam-second-flush/", "/cart/", "/policies/shipping/",
                    "/your-account/sign-in/", "/subscriptions/", "/email-list/", "/tea-notes/"]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(wears_frame(response))

    def test_owner_pages_keep_the_plain_look(self):
        owner, device = make_owner()
        login_verified(self.client, owner, device)
        for url in [reverse("core:owner_dashboard"), reverse("storefront:variant_list"),
                    reverse("checkout:sales_by_state"), reverse("emaillist:owner_home")]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertFalse(wears_frame(response))
                self.assertContains(response, '<div class="vine">')

    def test_home_has_the_arched_picture_and_dividers(self):
        html = self.client.get("/").content.decode()
        self.assertIn('class="hero-scene"', html)
        self.assertGreaterEqual(html.count('class="vine-divider"'), 3)
        self.assertIn('class="vine-ground"', html)


class OrnamentDrawingTests(TestCase):
    def setUp(self):
        # Parsing fails on any XML error, such as "--" in a comment, which
        # makes browsers drop every drawing after it.
        root = ET.parse(STATIC / "img" / "motifs.svg").getroot()
        self.view_boxes = {symbol.get("id"): symbol.get("viewBox") for symbol in root.iter(f"{SVG_NS}symbol")}

    def test_each_ornament_is_in_the_sprite_with_the_tags_view_box(self):
        for name, box in ORNAMENT_BOXES.items():
            with self.subTest(name=name):
                self.assertEqual(self.view_boxes.get(f"orn-{name}"), " ".join(str(n) for n in box))

    def test_vines_js_places_the_same_ornaments(self):
        script = (STATIC / "js" / "vines.js").read_text()
        boxes = dict(
            (name.strip('"'), tuple(int(n) for n in numbers.split(",")))
            for name, numbers in re.findall(r'("?[\w-]+"?): \[([-\d, ]+)\]', script.split("var BOX = {")[1].split("};")[0])
        )
        self.assertEqual(boxes, ORNAMENT_BOXES)

    def test_ornament_tag_draws_at_the_origin(self):
        html = ornament("bird", 10, 20, 5, 1.5, "lv2")
        self.assertIn('href="/static/img/motifs.svg#orn-bird"', html)
        self.assertIn('x="-32" y="-34" width="57" height="36"', html)
        self.assertIn('transform="translate(10 20) rotate(5) scale(1.5)"', html)
        self.assertIn('class="lv2"', html)

    def test_fonts_and_licences_are_shipped(self):
        for name in ["federant-latin.woff2", "alegreya-latin.woff2", "alegreya-italic-latin.woff2",
                     "Federant-OFL.txt", "Alegreya-OFL.txt"]:
            with self.subTest(name=name):
                self.assertTrue((STATIC / "fonts" / name).is_file())
