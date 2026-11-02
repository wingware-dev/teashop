from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from apps.catalog.models import Product, SizeOption
from apps.checkout.models import Order, Subscription
from apps.emaillist.models import Mailing, Subscriber
from apps.fulfillment import boxes
from apps.fulfillment.models import BoxSize, PackageDimensions, Scale
from apps.inventory.models import Allergen, Lot, Receipt, Supplier
from apps.marketing.models import Idea
from apps.support.models import Conversation, Draft

MODELS = [Product, Supplier, Lot, Receipt, BoxSize, PackageDimensions, Scale, Order, Subscription, Subscriber, Mailing, Conversation,
          Draft, Idea]


@override_settings(DEBUG=True, PRODUCTION=False)
class LoadDemoShopTests(TestCase):
    def test_loads_a_sample_business_and_is_safe_to_run_twice(self):
        call_command("load_demo_shop", stdout=StringIO())
        counts = {model.__name__: model.objects.count() for model in MODELS}
        call_command("load_demo_shop", stdout=StringIO())
        self.assertEqual({model.__name__: model.objects.count() for model in MODELS}, counts)

        self.assertEqual(Product.objects.filter(kind=Product.Kind.TEA).count(), 10)
        self.assertEqual(Supplier.objects.count(), 3)
        self.assertTrue(Lot.objects.filter(allergens=Allergen.objects.get(code="tree-nuts")).exists())
        self.assertEqual(Receipt.objects.get().lots.count(), 2)
        self.assertEqual(counts["BoxSize"], 3)
        self.assertEqual(counts["Scale"], 1)
        tea_sizes = SizeOption.objects.filter(product__kind=Product.Kind.TEA)
        self.assertEqual(counts["PackageDimensions"], tea_sizes.count())
        self.assertFalse(tea_sizes.filter(dimensions=None).exists())
        # The measurements drive the box suggestion: a pouch fits the
        # mailer, a tall 100 g tin needs a box.
        pouch = SizeOption.objects.get(sku="ASSAM-SECOND-50")
        tin = SizeOption.objects.get(sku="ASSAM-SECOND-100")
        self.assertEqual(boxes.suggest([(pouch, 1)]).box.item.code, "MAILER-6X9")
        self.assertEqual(boxes.suggest([(tin, 1)]).box.item.code, "BOX-8X6X4")
        self.assertEqual(set(Order.objects.values_list("status", flat=True)), set(Order.Status.values))
        for order in Order.objects.prefetch_related("lines"):
            with self.subTest(order=order.payment_id):
                self.assertTrue(order.lines.exists())
        self.assertEqual(Subscription.objects.get().orders.count(), 1)
        self.assertEqual(Mailing.objects.get().status, Mailing.Status.DRAFT)
        self.assertEqual(Draft.objects.get().conversation.status, Conversation.Status.DRAFTED)
        self.assertGreaterEqual(counts["Idea"], 4)

    @override_settings(DEBUG=False)
    def test_refused_with_debug_off(self):
        with self.assertRaises(CommandError):
            call_command("load_demo_shop", stdout=StringIO())
        self.assertFalse(Product.objects.exists())
