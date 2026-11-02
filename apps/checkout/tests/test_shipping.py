"""Where the shop ships, the parcel's weight, and the EasyPost client
(with its HTTP answers stood in)."""

from decimal import Decimal
from unittest import mock

import requests
from django.test import SimpleTestCase, override_settings

from apps.catalog.models import SizeOption
from apps.checkout.places import ships_to
from apps.checkout.shipping import Address, EasyPostShipping, FakeShipping, ShippingError, parcel_grams

HOME = Address(name="Ada", street1="12 main st", city="albany", state="NY", zip="12207")


class ShipsToTests(SimpleTestCase):
    def test_contiguous_states_and_dc(self):
        for state, zip_code in [("NY", "12207"), ("CA", "94110"), ("DC", "20001"), ("FL", "33101-1234")]:
            self.assertIsNone(ships_to(state, zip_code), state)

    def test_not_alaska_hawaii_or_territories(self):
        for state in ("AK", "HI", "PR", "GU", "VI", "AA", "AE", "AP"):
            self.assertIsNotNone(ships_to(state, "12345"), state)

    def test_military_and_offshore_zip_codes_refused_whatever_the_state(self):
        for zip_code in ("09012", "34002", "96201", "96813", "99501", "00901"):
            self.assertIsNotNone(ships_to("NY", zip_code), zip_code)

    def test_bad_zip(self):
        self.assertIsNotNone(ships_to("NY", "1220"))
        self.assertIsNotNone(ships_to("NY", ""))


class WeightTests(SimpleTestCase):
    def test_size_weights(self):
        self.assertEqual(SizeOption(net_grams=50, package="tin").shipping_weight(), 160)
        self.assertEqual(SizeOption(net_grams=50, package="pouch").shipping_weight(), 65)
        self.assertEqual(SizeOption(net_grams=50, package="pouch", shipping_grams=80).shipping_weight(), 80)
        self.assertEqual(SizeOption(net_grams=None).shipping_weight(), 450)

    @override_settings(SHIPPING_BOX_GRAMS=150)
    def test_parcel_adds_the_box(self):
        pouch = SizeOption(net_grams=50, package="pouch")
        self.assertEqual(parcel_grams([(pouch, 2)]), 2 * 65 + 150)


class FakeShippingTests(SimpleTestCase):
    def test_rates_rise_with_weight_cheapest_first(self):
        light, heavy = FakeShipping().rates(HOME, 200), FakeShipping().rates(HOME, 1200)
        self.assertEqual([r.service for r in light], ["GroundAdvantage", "Priority", "Express"])
        self.assertLess(light[0].amount, heavy[0].amount)

    def test_verify_refuses_outside_contiguous_states(self):
        self.assertFalse(FakeShipping().verify(Address(street1="1 A St", city="Juneau", state="AK",
                                                       zip="99801")).ok)


def answer(status, data):
    response = mock.Mock(status_code=status, text=str(data))
    response.json.return_value = data
    return response


@override_settings(SHIPPING_SERVICES=["GroundAdvantage", "Priority"],
                   SHIP_FROM={"name": "Shop", "street1": "1 Elm St", "street2": "", "city": "Troy", "state": "NY",
                              "zip": "12180", "phone": "5185550100"})
class EasyPostTests(SimpleTestCase):
    def client_answering(self, *answers):
        session = mock.Mock()
        session.post.side_effect = list(answers)
        return EasyPostShipping("EZTKtest", session=session), session

    def test_verified_address_comes_back_as_the_post_office_writes_it(self):
        client, session = self.client_answering(answer(200, {
            "street1": "12 MAIN ST", "city": "ALBANY", "state": "NY", "zip": "12207-1001",
            "verifications": {"delivery": {"success": True, "errors": []}}}))
        result = client.verify(HOME)
        self.assertTrue(result.ok)
        self.assertEqual(result.address.zip, "12207-1001")
        self.assertTrue(result.changed_from(HOME))
        url, kwargs = session.post.call_args.args[0], session.post.call_args.kwargs
        self.assertTrue(url.endswith("/addresses"))
        self.assertEqual(kwargs["json"]["verify"], ["delivery"])
        self.assertEqual(kwargs["auth"], ("EZTKtest", ""))

    def test_undeliverable_address_explains(self):
        client, _ = self.client_answering(answer(200, {
            "street1": "12 MAIN ST", "verifications": {"delivery": {"success": False, "errors": [
                {"message": "Address not found"}]}}}))
        result = client.verify(HOME)
        self.assertFalse(result.ok)
        self.assertEqual(result.messages, ["Address not found"])

    def test_rates_only_usps_services_offered_cheapest_first(self):
        client, session = self.client_answering(answer(201, {"id": "shp_1", "rates": [
            {"id": "rate_p", "carrier": "USPS", "service": "Priority", "rate": "9.10", "delivery_days": 2},
            {"id": "rate_x", "carrier": "USPS", "service": "Express", "rate": "30.00", "delivery_days": 1},
            {"id": "rate_g", "carrier": "USPS", "service": "GroundAdvantage", "rate": "5.25", "delivery_days": 4},
            {"id": "rate_u", "carrier": "UPS", "service": "Ground", "rate": "4.00"}]}))
        rates = client.rates(HOME, 567)
        self.assertEqual([(r.id, r.amount) for r in rates], [("rate_g", Decimal("5.25")), ("rate_p", Decimal("9.10"))])
        self.assertEqual(rates[0].shipment_id, "shp_1")
        shipment = session.post.call_args.kwargs["json"]["shipment"]
        self.assertEqual(shipment["parcel"]["weight"], 20.0)  # 567 g in ounces
        self.assertEqual(shipment["from_address"]["zip"], "12180")

    def test_service_down_raises_a_customer_message(self):
        session = mock.Mock()
        session.post.side_effect = requests.ConnectionError("down")
        with self.assertRaises(ShippingError):
            EasyPostShipping("EZTKtest", session=session).rates(HOME, 100)
        client, _ = self.client_answering(answer(503, {}))
        with self.assertRaises(ShippingError):
            client.rates(HOME, 100)

    def test_no_rates_raises(self):
        client, _ = self.client_answering(answer(201, {"id": "shp_1", "rates": [], "messages": [{"message": "x"}]}))
        with self.assertRaises(ShippingError):
            client.rates(HOME, 100)
