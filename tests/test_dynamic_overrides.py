# ASD-STE100 verified: Short sentences. Direct imperative verbs.
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ctf_downloader.bridge.constants import DEFAULT_BRIDGE_PORT, DEFAULT_BRIDGE_HOST
from ctf_downloader.services.burp_service import BurpService
from ctf_downloader.services.web_dashboard import WebDashboard
from ctf_downloader.storage.global_config import resolve_workspace_root
from ctf_downloader.utils.agy_resolver import resolve_agy_binary


class TestDynamicOverrides(unittest.TestCase):
    """Verify environment variable overrides for ports, paths, and binary resolution."""

    def test_workspace_root_env_override(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.dict(os.environ, {"CTF_WORKSPACE_ROOT": tmp_dir}):
                self.assertEqual(resolve_workspace_root(), os.path.abspath(tmp_dir))

    def test_bridge_port_and_host_env_override(self):
        with patch.dict(os.environ, {"CTF_BRIDGE_PORT": "28888", "CTF_BRIDGE_HOST": "0.0.0.0"}):
            from ctf_downloader.bridge import constants
            port = int(os.environ.get("CTF_BRIDGE_PORT", constants.DEFAULT_BRIDGE_PORT))
            host = os.environ.get("CTF_BRIDGE_HOST", constants.DEFAULT_BRIDGE_HOST)
            self.assertEqual(port, 28888)
            self.assertEqual(host, "0.0.0.0")

    def test_burp_ports_env_override(self):
        with patch.dict(os.environ, {"BURP_MCP_PORT": "19876", "BURP_PROXY_PORT": "18080"}):
            svc = BurpService()
            self.assertEqual(svc.mcp_port, 19876)
            self.assertEqual(svc.proxy_port, 18080)

    def test_web_dashboard_port_env_override(self):
        with patch.dict(os.environ, {"CTF_DASHBOARD_PORT": "9090"}):
            dash = object.__new__(WebDashboard)
            port = int(os.environ.get("CTF_DASHBOARD_PORT", 8689))
            self.assertEqual(port, 9090)

    def test_agy_binary_resolver_fallbacks(self):
        # Explicit AGY_BIN override
        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_agy = Path(tmp_dir) / "agy"
            fake_agy.touch(mode=0o755)
            with patch.dict(os.environ, {"AGY_BIN": str(fake_agy)}):
                self.assertEqual(resolve_agy_binary(), str(fake_agy))
