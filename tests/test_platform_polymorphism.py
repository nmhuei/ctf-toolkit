# ASD-STE100 verified: Short sentences. Direct imperative verbs.
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from ctf_downloader.platforms.base import BasePlatform
from ctf_downloader.platforms.ctfd import CTFdPlatform
from ctf_downloader.platforms.gzctf import GZCTFPlatform
from ctf_downloader.platforms.rctf import RCTFPlatform
from ctf_downloader.services.instance_keepalive import InstanceKeepAlive, InstanceTracker
from ctf_downloader.services.register_service import RegisterService
from ctf_downloader.services.watch_service import WatchService


class ConcretePlatform(BasePlatform):
    def authenticate(self):
        return True

    def fetch_challenges(self):
        return []

    def get_full_file_url(self, file_path: str):
        return file_path

    def submit_flag(self, challenge_id, flag: str):
        return True, ""


class TestPlatformPolymorphism(unittest.TestCase):
    """Test platform capability flags and polymorphic hooks."""

    def test_base_platform_capabilities(self):
        plat = ConcretePlatform("https://ctf.test", MagicMock())
        self.assertFalse(plat.supports_notices)
        self.assertIsNone(plat.notices_endpoint)
        self.assertEqual(plat.min_instance_op_gap_seconds, 0.0)
        self.assertIsNone(plat.max_instance_renews)
        self.assertTrue(plat.restart_rotates_flag)
        self.assertIsNone(plat.extract_verify_payload("https://ctf.test/confirm/123"))

    def test_ctfd_capabilities_and_verify(self):
        plat = CTFdPlatform("https://ctf.test", MagicMock())
        self.assertTrue(plat.supports_notices)
        self.assertEqual(plat.notices_endpoint, "/api/v1/notices")
        self.assertEqual(plat.min_instance_op_gap_seconds, 61.0)
        self.assertEqual(plat.max_instance_renews, 5)
        self.assertTrue(plat.restart_rotates_flag)

        payload = plat.extract_verify_payload("https://ctf.test/confirm/token_123")
        self.assertIsNotNone(payload)
        self.assertEqual(payload["url"], "https://ctf.test/confirm/token_123")

        # Session GET simulation
        session = MagicMock()
        session.get.return_value = SimpleNamespace(status_code=200)
        ok, data = plat.verify_email(session, payload)
        self.assertTrue(ok)
        session.get.assert_called_once_with("https://ctf.test/confirm/token_123", timeout=20)

    def test_gzctf_capabilities_and_verify(self):
        plat = GZCTFPlatform("https://gz.test", MagicMock())
        self.assertFalse(plat.supports_notices)
        self.assertIsNone(plat.notices_endpoint)
        self.assertEqual(plat.min_instance_op_gap_seconds, 0.0)
        self.assertIsNone(plat.max_instance_renews)
        self.assertFalse(plat.restart_rotates_flag)

        raw_url = "https://gz.test/account/verify?token=tok123&email=user%40test.com"
        payload = plat.extract_verify_payload(raw_url)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["token"], "tok123")
        self.assertEqual(payload["email"], "user@test.com")

        # Session POST simulation
        session = MagicMock()
        session.post.return_value = SimpleNamespace(status_code=200, json=lambda: {"msg": "ok"})
        ok, data = plat.verify_email(session, payload, base_url="https://gz.test")
        self.assertTrue(ok)
        session.post.assert_called_once_with(
            "https://gz.test/api/account/verify",
            json={"token": "tok123", "email": "user@test.com"},
            timeout=20,
        )

    def test_rctf_capabilities_and_verify(self):
        plat = RCTFPlatform("https://rctf.test", MagicMock())
        self.assertFalse(plat.supports_notices)
        self.assertIsNone(plat.notices_endpoint)
        self.assertEqual(plat.min_instance_op_gap_seconds, 0.0)
        self.assertIsNone(plat.max_instance_renews)
        self.assertTrue(plat.restart_rotates_flag)

        raw_url = "https://rctf.test/verify?token=rctf_tok"
        payload = plat.extract_verify_payload(raw_url)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["token"], "rctf_tok")

        # Session POST simulation
        session = MagicMock()
        session.post.return_value = SimpleNamespace(
            status_code=200,
            json=lambda: {"kind": "goodRegisterV2", "data": {"token": "xyz"}},
        )
        ok, data = plat.verify_email(session, payload, base_url="https://rctf.test")
        self.assertTrue(ok)
        session.post.assert_called_once_with(
            "https://rctf.test/api/v2/auth/verify",
            json={"verifyToken": "rctf_tok"},
            timeout=20,
        )

    def test_instance_keepalive_polymorphism(self):
        # Whale tracker with gap and max renews
        whale_plat = CTFdPlatform("https://ctfd.test", MagicMock())
        whale_svc = InstanceKeepAlive(MagicMock(platform=whale_plat))
        whale_tr = InstanceTracker(
            challenge_id=1,
            name="whale_task",
            min_op_gap=whale_plat.min_instance_op_gap_seconds,
            max_renews=whale_plat.max_instance_renews,
            rotates_flag=whale_plat.restart_rotates_flag,
        )
        self.assertEqual(whale_tr.min_op_gap, 61.0)
        self.assertEqual(whale_tr.max_renews, 5)
        self.assertTrue(whale_svc.restart_rotates_flag(whale_tr))

        # GZCTF tracker with zero gap and no renew limit
        gz_plat = GZCTFPlatform("https://gz.test", MagicMock())
        gz_svc = InstanceKeepAlive(MagicMock(platform=gz_plat))
        gz_tr = InstanceTracker(
            challenge_id=2,
            name="gz_task",
            min_op_gap=gz_plat.min_instance_op_gap_seconds,
            max_renews=gz_plat.max_instance_renews,
            rotates_flag=gz_plat.restart_rotates_flag,
        )
        self.assertEqual(gz_tr.min_op_gap, 0.0)
        self.assertIsNone(gz_tr.max_renews)
        self.assertFalse(gz_svc.restart_rotates_flag(gz_tr))

    def test_watch_service_notices_polymorphism(self):
        ctfd_plat = MagicMock(spec=CTFdPlatform)
        ctfd_plat.supports_notices = True
        ctfd_plat.notices_endpoint = "/api/v1/notices"
        ctfd_plat.base_url = "https://ctfd.test"
        ctfd_plat.session = MagicMock()
        ctfd_plat.session.get.return_value = SimpleNamespace(status_code=304, headers={})

        watch = object.__new__(WatchService)
        watch.platform = ctfd_plat
        watch.state = {}
        watch.guard = None
        watch.scheduler = MagicMock()
        notices = watch._tick_notices(window_active=True)
        self.assertEqual(notices, [])
        ctfd_plat.session.get.assert_called_once()

        # Non-supporting platform skips tick notices immediately
        custom_plat = MagicMock(spec=BasePlatform)
        custom_plat.supports_notices = False
        watch_custom = object.__new__(WatchService)
        watch_custom.platform = custom_plat
        watch_custom.state = {}
        watch_custom.guard = None
        self.assertEqual(watch_custom._tick_notices(window_active=True), [])
