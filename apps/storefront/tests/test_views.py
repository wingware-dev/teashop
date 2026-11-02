import json
import re

from django.test import TestCase, override_settings
from django.urls import reverse

from apps.catalog.models import Product, SizeOption
from apps.core.testing import login_verified, make_owner
from apps.storefront import demo
from apps.storefront.models import Article


def structured_data(response):
    """The JSON-LD objects on a page."""
    html = response.content.decode()
    return [json.loads(m) for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]


def slugs(response):
    return [product.slug for product in response.context["products"]]


@override_settings(STOREFRONT_OPEN=True)
class ShopPagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        demo.load()

    def test_every_page_answers(self):
        for url in ["/", "/teas/", "/teas/black/", "/teas/herbal/", "/regions/", "/regions/assam/",
                    "/collections/specials/", "/search/?q=honey", "/products/assam-second-flush/",
                    "/products/glass-teapot/", "/merch-and-accessories/", "/merch-and-accessories/teaware/",
                    "/tea-notes/", "/tea-notes/brewing-green-tea/"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_home_shows_sections_and_search_box_data(self):
        response = self.client.get("/")
        self.assertContains(response, "Shop by kind of tea")
        self.assertContains(response, "This week&#x27;s picks")
        self.assertContains(response, "Glass Teapot")
        self.assertEqual(structured_data(response)[0]["@type"], "WebSite")
        self.assertNotContains(response, 'name="robots"')

    def test_category_lists_only_its_products(self):
        response = self.client.get("/teas/herbal/")
        self.assertEqual(sorted(slugs(response)), ["chamomile-meadow", "hibiscus-berry-tisane"])
        self.assertNotIn("categories", response.context["choices"])

    def test_goods_category_is_not_reachable_as_a_tea_category(self):
        self.assertEqual(self.client.get("/teas/teaware/").status_code, 404)
        self.assertEqual(self.client.get("/merch-and-accessories/black/").status_code, 404)

    def test_region_and_collection(self):
        self.assertEqual(slugs(self.client.get("/regions/assam/")), ["assam-second-flush"])
        self.assertEqual(sorted(slugs(self.client.get("/collections/specials/"))),
                         ["dong-ding-oolong", "silver-needle", "vanilla-almond-black"])

    def test_search_matches_every_word(self):
        self.assertEqual(slugs(self.client.get("/search/?q=bergamot")), ["earl-grey-cornflower"])
        self.assertEqual(slugs(self.client.get("/search/?q=honey+roasted")), ["dong-ding-oolong"])
        self.assertEqual(slugs(self.client.get("/search/?q=Taiwan")), ["dong-ding-oolong"])
        self.assertEqual(slugs(self.client.get("/search/?q=zzzz")), [])

    def test_search_page_is_not_indexed(self):
        self.assertContains(self.client.get("/search/?q=tea"), '<meta name="robots" content="noindex">')

    def test_filters_combine(self):
        self.assertEqual(sorted(slugs(self.client.get("/teas/?caffeine=none"))),
                         ["chamomile-meadow", "hibiscus-berry-tisane"])
        # Every chosen note, not any.
        self.assertEqual(sorted(slugs(self.client.get("/teas/?note=honey&note=floral"))),
                         ["chamomile-meadow", "dong-ding-oolong", "silver-needle"])
        tins = slugs(self.client.get("/teas/?package=tin"))
        self.assertIn("silver-needle", tins)
        self.assertNotIn("dong-ding-oolong", tins)
        cheap = slugs(self.client.get("/teas/?price_max=8.50"))
        self.assertIn("chamomile-meadow", cheap)  # $8.00
        self.assertIn("yunnan-golden-buds", cheap)  # from $8.00
        self.assertNotIn("dong-ding-oolong", cheap)  # $15.00
        self.assertEqual(slugs(self.client.get("/teas/?region=nantou&category=oolong")), ["dong-ding-oolong"])

    def test_sorting(self):
        prices = [p.from_price for p in self.client.get("/teas/?sort=price").context["products"]]
        self.assertEqual(prices, sorted(prices))
        prices = [p.from_price for p in self.client.get("/teas/?sort=-price").context["products"]]
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_bad_filter_values_are_ignored(self):
        for query in ["price_max=abc", "price_max=-3", "price_max=NaN", "sort=evil", "caffeine=lots",
                      "package=crate", "page=999", "page=x"]:
            with self.subTest(query=query):
                response = self.client.get(f"/teas/?{query}")
                self.assertEqual(response.status_code, 200)
                self.assertTrue(slugs(response))

    def test_only_offered_filter_options_are_shown(self):
        choices = self.client.get("/teas/herbal/").context["choices"]
        self.assertEqual([value for value, _ in choices["caffeine"]], ["none"])
        self.assertEqual([value for value, _ in choices["packages"]], ["pouch"])

    def test_product_page_facts(self):
        response = self.client.get("/products/vanilla-almond-black/")
        self.assertContains(response, "Tree nuts")
        self.assertContains(response, "black tea, almond pieces, natural vanilla flavour")
        self.assertContains(response, "203 °F (95 °C)")
        self.assertContains(response, "3 g for a 250 ml (8 oz) cup")
        self.assertContains(response, "$10.00")
        self.assertContains(response, "In stock")
        self.assertContains(response, "Add to cart")

    def test_organic_wording_only_for_products_sold_as_organic(self):
        response = self.client.get("/products/silver-needle/")
        self.assertNotContains(response, "Organic")
        self.assertNotContains(response, "organic")

        tea = Product.objects.get(slug="silver-needle")
        tea.sold_as_organic = True
        tea.save()
        tea.tea.lots.update(organic=True)
        response = self.client.get("/products/silver-needle/")
        self.assertContains(response, '<span class="chip">Organic</span>', html=True)
        self.assertContains(response, "<dt>Organic</dt><dd>Organic tea</dd>", html=True)
        self.assertContains(response, "do not carry the USDA organic seal")
        # The exemption allows "organic", never a claim to be certified.
        self.assertNotRegex(response.content.decode(), r"(?i)certified[- ]organic|organic[- ]certified")

    def test_product_structured_data(self):
        data = structured_data(self.client.get("/products/assam-second-flush/"))
        product = next(d for d in data if d["@type"] == "Product")
        self.assertEqual(product["name"], "Assam Second Flush")
        self.assertEqual(product["countryOfOrigin"], "India")
        self.assertEqual([o["price"] for o in product["offers"]], ["9.00", "16.00"])
        self.assertTrue(all(o["priceCurrency"] == "USD" for o in product["offers"]))
        self.assertEqual(product["offers"][0]["availability"], "https://schema.org/InStock")
        crumbs = next(d for d in data if d["@type"] == "BreadcrumbList")
        self.assertEqual([c["name"] for c in crumbs["itemListElement"]], ["Home", "Black tea", "Assam Second Flush"])

    def test_structured_data_cannot_break_out_of_its_script(self):
        product = Product.objects.get(slug="silver-needle")
        product.summary = "</script><script>alert(1)</script>"
        product.save()
        response = self.client.get("/products/silver-needle/")
        self.assertNotContains(response, "<script>alert(1)")
        product_data = next(d for d in structured_data(response) if d["@type"] == "Product")
        self.assertEqual(product_data["description"], "</script><script>alert(1)</script>")

    def test_sold_out_size(self):
        # Stand-in for selling it all: no usable tea left.
        Product.objects.get(slug="silver-needle").tea.lots.update(quantity_on_hand=0)
        response = self.client.get("/products/silver-needle/")
        self.assertContains(response, "Sold out")
        offer = next(d for d in structured_data(response) if d["@type"] == "Product")["offers"][0]
        self.assertEqual(offer["availability"], "https://schema.org/OutOfStock")

    def test_inactive_products_and_sizes_are_hidden(self):
        Product.objects.filter(slug="silver-needle").update(is_active=False)
        self.assertEqual(self.client.get("/products/silver-needle/").status_code, 404)
        self.assertNotIn("silver-needle", slugs(self.client.get("/teas/")))
        SizeOption.objects.filter(product__slug="dong-ding-oolong").update(is_active=False)
        self.assertEqual(self.client.get("/products/dong-ding-oolong/").status_code, 404)
        self.assertNotIn("dong-ding-oolong", slugs(self.client.get("/teas/")))

    def test_unpublished_and_future_articles_are_hidden(self):
        Article.objects.filter(slug="brewing-green-tea").update(is_published=False)
        self.assertEqual(self.client.get("/tea-notes/brewing-green-tea/").status_code, 404)
        self.assertNotContains(self.client.get("/tea-notes/"), "Brewing green tea")

    def test_article_body_is_rendered_and_escaped(self):
        article = Article.objects.get(slug="brewing-green-tea")
        article.body = "## Water\n\nCool it <b>first</b>."
        article.save()
        response = self.client.get(article.get_absolute_url())
        self.assertContains(response, "<h2>Water</h2>", html=True)
        self.assertContains(response, "Cool it &lt;b&gt;first&lt;/b&gt;.")

    def test_sitemap_lists_shop_pages(self):
        response = self.client.get("/sitemap.xml")
        self.assertContains(response, "/products/assam-second-flush/")
        self.assertContains(response, "/teas/black/")
        self.assertContains(response, "/regions/assam/")
        self.assertContains(response, "/tea-notes/brewing-green-tea/")
        self.assertNotContains(response, "/owner/")

    def test_robots_points_to_sitemap_without_naming_admin(self):
        text = self.client.get("/robots.txt").content.decode()
        self.assertIn("Sitemap: http://testserver/sitemap.xml", text)
        self.assertIn("Disallow: /owner/", text)
        self.assertNotIn("admin", text)

    def test_only_get(self):
        self.assertEqual(self.client.post("/teas/").status_code, 405)


@override_settings(STOREFRONT_OPEN=False)
class ClosedShopTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        demo.load()

    def test_visitors_see_coming_soon_only(self):
        response = self.client.get("/")
        self.assertContains(response, "Specialty teas, coming soon")
        self.assertNotContains(response, "Search teas")
        for url in ["/teas/", "/products/assam-second-flush/", "/regions/", "/tea-notes/", "/search/?q=tea"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_search_engines_kept_out(self):
        self.assertEqual(self.client.get("/robots.txt").content.decode(), "User-agent: *\nDisallow: /\n")
        self.assertNotContains(self.client.get("/sitemap.xml"), "<loc>")

    def test_owner_can_try_the_shop(self):
        owner, device = make_owner()
        login_verified(self.client, owner, device)
        self.assertContains(self.client.get("/"), "Shop by kind of tea")
        self.assertEqual(self.client.get("/products/assam-second-flush/").status_code, 200)

    def test_password_only_session_is_not_enough(self):
        owner, _ = make_owner()
        self.client.force_login(owner)
        self.assertEqual(self.client.get("/teas/").status_code, 404)

    def test_owner_pages_still_work(self):
        owner, device = make_owner()
        login_verified(self.client, owner, device)
        self.assertEqual(self.client.get(reverse("core:owner_dashboard")).status_code, 200)
