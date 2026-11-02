"""The catalog's storefront side: sections, copy checks on products, the
facts product pages show, and product photos."""

import io
import shutil
import tempfile
from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from apps.catalog import images
from apps.catalog.models import Category, Collection, Product, ProductPhoto
from apps.inventory.models import Item, Lot
from apps.inventory.testing import make_item, make_lot


def jpeg_bytes(size=(1600, 1200), exif=None, color=(60, 110, 60)):
    buffer = io.BytesIO()
    image = Image.new("RGB", size, color)
    if exif is not None:
        image.save(buffer, "JPEG", exif=exif)
    else:
        image.save(buffer, "JPEG")
    return buffer.getvalue()


def herbal_category():
    return Category.objects.get(slug="herbal")


class SeededSectionsTests(TestCase):
    def test_standard_categories_and_collections_exist(self):
        self.assertTrue(Category.objects.filter(slug="black", section="tea").exists())
        self.assertTrue(Category.objects.get(slug="herbal").is_herbal)
        self.assertTrue(Category.objects.filter(slug="teaware", section="goods").exists())
        self.assertEqual(set(Collection.objects.values_list("slug", flat=True)),
                         {"specials", "this-weeks-picks", "new-arrivals"})

    def test_urls_follow_section(self):
        self.assertEqual(Category.objects.get(slug="black").get_absolute_url(), "/teas/black/")
        self.assertEqual(Category.objects.get(slug="teaware").get_absolute_url(), "/merch-and-accessories/teaware/")

    def test_section_intro_is_checked_for_health_claims(self):
        category = Category(name="Wellness", slug="wellness", intro="Teas that boost your immunity")
        with self.assertRaises(ValidationError) as caught:
            category.full_clean()
        self.assertIn("intro", caught.exception.message_dict)


class CollectionDatesTests(TestCase):
    def test_showing_respects_dates_and_active(self):
        today = date(2026, 11, 1)
        Collection.objects.all().delete()
        current = Collection.objects.create(name="Now", slug="now", starts_on=today - timedelta(days=1),
                                            ends_on=today)
        Collection.objects.create(name="Later", slug="later", starts_on=today + timedelta(days=1))
        Collection.objects.create(name="Over", slug="over", ends_on=today - timedelta(days=1))
        Collection.objects.create(name="Off", slug="off", is_active=False)
        open_ended = Collection.objects.create(name="Always", slug="always")
        self.assertEqual(set(Collection.objects.showing(today)), {current, open_ended})

    def test_end_before_start_is_refused(self):
        collection = Collection(name="Bad", slug="bad", starts_on=date(2026, 5, 2), ends_on=date(2026, 5, 1))
        with self.assertRaises(ValidationError):
            collection.full_clean()


class ProductCopyTests(TestCase):
    def setUp(self):
        self.assam = make_item("Assam")

    def product(self, **fields):
        fields.setdefault("tea", self.assam)
        fields.setdefault("name", "Assam")
        fields.setdefault("slug", "assam")
        return Product(**fields)

    def test_health_claim_in_any_customer_text_is_refused(self):
        for field in ["summary", "description", "tasting_notes", "brew_notes", "origin_detail"]:
            with self.subTest(field=field):
                product = self.product(**{field: "Helps digestion after meals"})
                with self.assertRaises(ValidationError) as caught:
                    product.full_clean()
                self.assertIn(field, caught.exception.message_dict)

    def test_clean_copy_passes(self):
        self.product(summary="Malty and brisk", tasting_notes="Honey and dried fruit").full_clean()

    def test_herbal_product_name_must_say_so(self):
        chamomile = make_item("Chamomile", kind=Item.Kind.HERBAL)
        with self.assertRaises(ValidationError) as caught:
            self.product(tea=chamomile, name="Chamomile Meadow", slug="cm").full_clean()
        self.assertIn("name", caught.exception.message_dict)
        self.product(tea=chamomile, name="Chamomile Meadow Herbal Tea", slug="cm").full_clean()

    def test_herbal_category_makes_it_herbal(self):
        product = self.product(category=herbal_category(), name="Rooibos", slug="rooibos")
        self.assertTrue(product.is_herbal)
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_caffeine_free_only_with_caffeine_none(self):
        with self.assertRaises(ValidationError):
            self.product(summary="Caffeine-free comfort", caffeine="low").full_clean()
        self.product(summary="Caffeine-free comfort", caffeine="none").full_clean()

    @override_settings(CATALOG_PROTECTED_ORIGINS=["Darjeeling"])
    def test_protected_origin_needs_certification(self):
        with self.assertRaises(ValidationError) as caught:
            self.product(name="Darjeeling First Flush", slug="dj").full_clean()
        self.assertIn("name", caught.exception.message_dict)
        self.product(name="Darjeeling First Flush", slug="dj", origin_certified=True).full_clean()

    def test_organic_wording_follows_the_exemption(self):
        with self.assertRaises(ValidationError) as caught:
            self.product(name="Organic Sencha", slug="os").full_clean()
        self.assertIn("name", caught.exception.message_dict)
        self.product(name="Organic Sencha", slug="os", sold_as_organic=True).full_clean()
        with self.assertRaises(ValidationError) as caught:
            self.product(summary="Certified organic", sold_as_organic=True).full_clean()
        self.assertIn("summary", caught.exception.message_dict)

    def test_category_must_match_kind(self):
        with self.assertRaises(ValidationError) as caught:
            self.product(category=Category.objects.get(slug="teaware")).full_clean()
        self.assertIn("category", caught.exception.message_dict)


class ShopFactsTests(TestCase):
    def test_union_of_usable_lots(self):
        tea = make_item("Vanilla Black", ingredient_name="black tea")
        make_lot(tea, country="India", ingredients="black tea, almond pieces, natural vanilla flavour",
                 allergens=["tree-nuts"], best_by=date(2027, 1, 1))
        make_lot(tea, country="Sri Lanka, India", allergens=["milk"], best_by=date(2027, 6, 1))
        held = make_lot(tea, country="Kenya", allergens=["soybeans"])
        held.status = Lot.Status.ON_HOLD
        held.save()
        product = Product.objects.create(name="Vanilla Black", slug="vb", tea=tea)
        facts = product.shop_facts()
        self.assertEqual(facts["countries"], ["India", "Sri Lanka"])
        self.assertEqual(facts["allergens"], ["Tree nuts", "Milk"])
        self.assertEqual(facts["ingredients"], "black tea, almond pieces, natural vanilla flavour")
        self.assertTrue(facts["has_stock"])

    def test_no_stock_falls_back_to_item_wording(self):
        tea = make_item("Sencha", ingredient_name="green tea")
        product = Product.objects.create(name="Sencha", slug="sencha", tea=tea)
        self.assertEqual(product.shop_facts(), {"countries": [], "ingredients": "green tea", "allergens": [],
                                                "has_stock": False})

    def test_organic_product_counts_only_organic_lots(self):
        tea = make_item("Sencha", ingredient_name="green tea")
        make_lot(tea, country="Japan", organic=True)
        make_lot(tea, country="China", organic=False)
        product = Product.objects.create(name="Sencha", slug="sencha", tea=tea, sold_as_organic=True)
        self.assertEqual(product.shop_facts()["countries"], ["Japan"])

    def test_goods_have_no_facts(self):
        product = Product.objects.create(name="Teapot", slug="teapot", kind=Product.Kind.GOODS)
        self.assertIsNone(product.shop_facts())


class ProductPhotoTests(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media)
        self.override.enable()
        self.product = Product.objects.create(name="Teapot", slug="teapot", kind=Product.Kind.GOODS)

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media, ignore_errors=True)

    def upload(self, data, name="IMG_0001.png"):
        return ProductPhoto.objects.create(product=self.product, image=SimpleUploadedFile(name, data),
                                           alt_text="A glass teapot")

    def test_location_and_other_metadata_are_removed(self):
        exif = Image.Exif()
        exif[0x010F] = "PhoneMaker"  # camera make
        exif[0x8825] = {1: "N", 2: (42.0, 5.0, 0.0)}  # GPS latitude
        data = jpeg_bytes(exif=exif.tobytes())
        with Image.open(io.BytesIO(data)) as original:  # the test photo does carry a location
            self.assertIn(2, original.getexif().get_ifd(0x8825))
        photo = self.upload(data, name="IMG_0001.jpeg")
        with Image.open(photo.image.path) as saved:
            self.assertEqual(dict(saved.getexif()), {})
            self.assertNotIn("icc_profile", saved.info)
        self.assertTrue(photo.image.name.endswith(".jpg"))

    def test_turned_upright_from_orientation_tag(self):
        exif = Image.Exif()
        exif[0x0112] = 6  # rotate 90 degrees when shown
        photo = self.upload(jpeg_bytes(size=(800, 600), exif=exif.tobytes()), name="side.jpg")
        self.assertEqual((photo.width, photo.height), (600, 800))

    def test_large_photo_is_limited_and_renditions_made(self):
        photo = self.upload(jpeg_bytes(size=(3000, 2000)))
        self.assertEqual((photo.width, photo.height), (images.MAX_SIDE, 1333))
        for width in images.RENDITION_WIDTHS:
            name = images.rendition_name(photo, width)
            self.assertTrue(photo.image.storage.exists(name), name)
            with photo.image.storage.open(name) as file, Image.open(file) as copy:
                self.assertEqual(copy.width, width)
                self.assertEqual(copy.format, "WEBP")
        self.assertIn(" 480w", photo.srcset())
        self.assertTrue(photo.srcset().endswith(f"{photo.image.url} 2000w"))
        self.assertTrue(photo.small_url.endswith("-480.webp"))

    def test_small_photo_gets_no_larger_copies(self):
        photo = self.upload(jpeg_bytes(size=(700, 500)))
        self.assertEqual(images.widths_for(photo), [480])
        self.assertEqual(photo.url_for_width(960), photo.image.url)

    def test_not_an_image_is_refused(self):
        with self.assertRaises(ValidationError):
            self.upload(b"not a picture", name="notes.jpg")

    def test_delete_removes_files(self):
        photo = self.upload(jpeg_bytes())
        storage, name = photo.image.storage, photo.image.name
        renditions = [images.rendition_name(photo, w) for w in images.widths_for(photo)]
        photo.delete()
        self.assertFalse(storage.exists(name))
        for rendition in renditions:
            self.assertFalse(storage.exists(rendition))

    def test_alt_text_is_required(self):
        photo = ProductPhoto(product=self.product, alt_text="  ")
        with self.assertRaises(ValidationError) as caught:
            photo.clean()
        self.assertIn("alt_text", caught.exception.message_dict)
