from django.test import SimpleTestCase, override_settings

from apps.catalog import copy_rules


class HealthClaimTests(SimpleTestCase):
    def test_catches_common_claims(self):
        for text in [
            "Chamomile helps you sleep.",
            "A gentle detox for spring.",
            "Boosts your metabolism.",
            "Rich in antioxidants.",
            "Soothes a sore throat.",
            "Ginger to treat nausea.",
            "Supports healthy digestion.",
            "Used as a remedy for colds.",
            "May lower blood pressure.",
            "Prevents the flu.",
            "Great for weight loss.",
            "Anti-inflammatory spices.",
            "Strengthens the immune system.",
        ]:
            with self.subTest(text=text):
                self.assertTrue(copy_rules.health_claims(text), text)

    def test_taste_and_brewing_words_pass(self):
        for text in [
            "A lovely treat on a cold morning.",
            "Treat yourself to a second cup.",
            "Delicious cold-brewed or iced.",
            "A palate-cleansing finish.",
            "Healthy-looking leaves, carefully sorted.",
            "Malty, brisk and generous with milk.",
            "Pour over ice for a refreshing summer drink.",
            "",
            None,
        ]:
            with self.subTest(text=text):
                self.assertEqual(copy_rules.health_claims(text), [], text)

    def test_reports_words_in_order(self):
        claims = copy_rules.health_claims("A detox tea that cures colds")
        self.assertEqual(len(claims), 3)
        self.assertTrue(claims[0].startswith('"detox"'))
        self.assertTrue(claims[1].startswith('"cures"'))

    def test_match_inside_another_is_reported_once(self):
        self.assertEqual(copy_rules.health_claims("Our tea boosts immunity."),
                         ['"boosts immunity" (boosts a body function)'])
        self.assertEqual(copy_rules.health_claims("Boosts your metabolism and immunity"),
                         ['"Boosts your metabolism" (boosts a body function)', '"immunity" (immunity)'])

    def test_problem_message_names_the_field(self):
        problems = copy_rules.health_claim_problems("Heals everything", "Summary")
        self.assertEqual(len(problems), 1)
        self.assertIn("Summary reads as a health or disease claim", problems[0])
        self.assertEqual(copy_rules.health_claim_problems("Floral and sweet"), [])


class HerbalNameTests(SimpleTestCase):
    def test_needs_herbal_tea_or_tisane(self):
        self.assertTrue(copy_rules.herbal_name_problems("Chamomile Meadow"))
        self.assertEqual(copy_rules.herbal_name_problems("Chamomile Meadow Herbal Tea"), [])
        self.assertEqual(copy_rules.herbal_name_problems("Hibiscus berry tisane"), [])
        self.assertEqual(copy_rules.herbal_name_problems("Mint herbal infusion"), [])

    def test_empty_name_is_left_to_required_field_checks(self):
        self.assertEqual(copy_rules.herbal_name_problems(""), [])


class CaffeineFreeTests(SimpleTestCase):
    def test_only_when_caffeine_is_none(self):
        self.assertTrue(copy_rules.caffeine_free_problems("Naturally caffeine-free", caffeine_is_none=False))
        self.assertTrue(copy_rules.caffeine_free_problems("No caffeine at all", caffeine_is_none=False))
        self.assertEqual(copy_rules.caffeine_free_problems("Naturally caffeine-free", caffeine_is_none=True), [])
        self.assertEqual(copy_rules.caffeine_free_problems("Bold and brisk", caffeine_is_none=False), [])


class OrganicTests(SimpleTestCase):
    def test_organic_only_when_sold_as_organic(self):
        for text in ["Organic sencha", "Organically grown in Shizuoka"]:
            with self.subTest(text=text):
                self.assertTrue(copy_rules.organic_problems(text, sold_as_organic=False))
                self.assertEqual(copy_rules.organic_problems(text, sold_as_organic=True), [])
        self.assertEqual(copy_rules.organic_problems("Grassy and sweet", sold_as_organic=False), [])
        self.assertEqual(copy_rules.organic_problems("", sold_as_organic=False), [])
        self.assertEqual(copy_rules.organic_problems(None, sold_as_organic=False), [])

    def test_certified_wording_and_seal_never_pass(self):
        for text in ["Certified organic sencha", "Certified-organic leaf", "Organic certified", "Organically certified",
                     "USDA Organic", "Carries the organic seal", "Certified 100% organic"]:
            with self.subTest(text=text):
                problems = copy_rules.organic_problems(text, sold_as_organic=True, where="Summary")
                self.assertEqual(len(problems), 1, problems)
                self.assertIn("Summary says", problems[0])


@override_settings(CATALOG_PROTECTED_ORIGINS=["Darjeeling", "Assam Orthodox"])
class ProtectedOriginTests(SimpleTestCase):
    def test_found_case_insensitively_as_whole_words(self):
        self.assertEqual(copy_rules.protected_origins_in("A darjeeling-style blend"), ["Darjeeling"])
        self.assertEqual(copy_rules.protected_origins_in("Assam orthodox leaf"), ["Assam Orthodox"])
        self.assertEqual(copy_rules.protected_origins_in("Plain Assam"), [])

    def test_only_for_certified_products(self):
        self.assertTrue(copy_rules.origin_problems("Darjeeling first flush", certified=False))
        self.assertEqual(copy_rules.origin_problems("Darjeeling first flush", certified=True), [])
        self.assertEqual(copy_rules.origin_problems("Nilgiri", certified=False), [])
