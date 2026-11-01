from django.test import RequestFactory, SimpleTestCase, override_settings

from apps.core.net import client_ip


class ClientIpTests(SimpleTestCase):
    def request(self, **meta):
        return RequestFactory().get("/", **meta)

    @override_settings(TRUST_X_REAL_IP=False)
    def test_uses_peer_address_without_proxy(self):
        request = self.request(REMOTE_ADDR="203.0.113.5", HTTP_X_REAL_IP="198.51.100.9")
        self.assertEqual(client_ip(request), "203.0.113.5")

    @override_settings(TRUST_X_REAL_IP=True)
    def test_uses_x_real_ip_behind_caddy(self):
        request = self.request(REMOTE_ADDR="172.18.0.4", HTTP_X_REAL_IP="198.51.100.9")
        self.assertEqual(client_ip(request), "198.51.100.9")

    @override_settings(TRUST_X_REAL_IP=True)
    def test_garbage_header_falls_back_to_peer(self):
        request = self.request(REMOTE_ADDR="172.18.0.4", HTTP_X_REAL_IP="not-an-ip")
        self.assertEqual(client_ip(request), "172.18.0.4")

    @override_settings(TRUST_X_REAL_IP=True)
    def test_never_trusts_x_forwarded_for(self):
        request = self.request(REMOTE_ADDR="172.18.0.4", HTTP_X_FORWARDED_FOR="1.2.3.4")
        self.assertEqual(client_ip(request), "172.18.0.4")

    def test_ipv6_is_normalised(self):
        request = self.request(REMOTE_ADDR="2001:DB8::0001")
        self.assertEqual(client_ip(request), "2001:db8::1")

    def test_missing_address_is_none(self):
        request = self.request(REMOTE_ADDR="")
        self.assertIsNone(client_ip(request))
