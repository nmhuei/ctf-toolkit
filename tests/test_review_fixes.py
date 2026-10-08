"""Review round (R1-R6) — test đỏ viết TRƯỚC khi sửa.

R1: watch notices 429 KHÔNG Retry-After → backoff phải SỐNG qua reward
    (không poll lại ~15s ngay tick sau dù message báo "lùi 30s").
R2: 429 CÓ Retry-After → penalty ONE-SHOT, interval cơ sở bất biến.
R3: AuthService tra key URL CHÍNH XÁC trước mọi heuristic; không mượn
    cookie của entry khác platform (host phải khớp).
R4: build_pack idempotent giữa các lần chạy cùng ngày; hậu tố _2 chỉ áp
    cho collision giữa các entry CÙNG lần chạy.
R5: hết raw ``requests.Session()`` ngoài utils/http_client.py.
R6: auto-sync enabled 2 tầng — global = mặc định, workspace
    .ctf/config.json = override; watch đọc được; help text nói đúng.

Chạy: python3 -m pytest tests/test_review_fixes.py -q
"""
import json
import shutil
import time
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------- #
# R1 + R2 — watch notices 429: backoff sống sót, base interval bất biến
# ---------------------------------------------------------------------- #
def _resp(status, headers=None):
    r = MagicMock()
    r.status_code = status
    r.headers = headers or {}
    r.json = MagicMock(return_value={"success": True, "data": []})
    return r


def _mk_watch(tmp_path, resp):
    """WatchService với platform giả kiểu CTFd trả ``resp`` cho /notices."""
    from ctf_downloader.services.watch_service import (
        WatchService, default_auto_sync_config)

    platform = MagicMock()
    platform.ctf_info.platform_type = "ctfd"
    platform.base_url = "https://ctfd.example.com"
    platform.session.get = MagicMock(return_value=resp)

    svc = WatchService(str(tmp_path), once=True, use_live_ui=False)
    svc.platform = platform
    svc.state = svc.state_store.load()
    svc.scheduler.register("notices", 15)
    return svc, default_auto_sync_config()["auto_sync"]


class TestR1NoticesBackoffSurvivesReward:
    def test_429_without_header_backoff_survives_reward(self, tmp_path):
        svc, cfg = _mk_watch(tmp_path, _resp(429, {}))
        before = time.time()
        lines = svc._run_round(cfg)
        delta = svc.scheduler._tasks["notices"]["deadline"] - before
        assert any("429" in ln for ln in lines)
        # Message không bịa "theo Retry-After" khi header vắng mặt
        assert not any("Retry-After" in ln for ln in lines)
        # Backoff ×2 (15→30s, jitter ±20%) phải SỐNG qua reward của tick —
        # reward reset mult KHÔNG được đưa kỳ poll về ~15s.
        assert delta >= 30 * 0.8, (
            f"429 không header bị reward xoá sạch — poll lại sau {delta:.1f}s")

    def test_429_streak_escalates_across_cycles(self, tmp_path):
        svc, cfg = _mk_watch(tmp_path, _resp(429, {}))
        svc._run_round(cfg)
        svc.scheduler._tasks["notices"]["deadline"] = 0.0
        before = time.time()
        svc._run_round(cfg)
        delta = svc.scheduler._tasks["notices"]["deadline"] - before
        assert delta >= 60 * 0.8, (
            f"429 liên tiếp phải backoff ×4 (≈60s), thực tế {delta:.1f}s")


class TestR2RetryAfterOneShot:
    def test_penalty_one_shot_base_interval_immutable(self, tmp_path):
        svc, cfg = _mk_watch(tmp_path, _resp(429, {"Retry-After": "90"}))
        before = time.time()
        svc._run_round(cfg)
        t = svc.scheduler._tasks["notices"]
        # R2: interval CƠ SỞ bất biến — Retry-After là penalty tạm thời,
        # KHÔNG được set_interval đổi base vĩnh viễn.
        assert t["interval"] == 15, (
            f"set_interval đổi base vĩnh viễn ({t['interval']}s)")
        delta = t["deadline"] - before
        assert 90 * 0.8 <= delta <= 90 * 1.2 + 0.5, (
            f"kỳ này phải lùi ~90s theo Retry-After, thực tế {delta:.1f}s")
        # Kỳ kế tiếp quay về base (penalty one-shot đã tiêu)
        before2 = time.time()
        svc.scheduler.postpone("notices")
        delta2 = svc.scheduler._tasks["notices"]["deadline"] - before2
        assert delta2 <= 15 * 1.2 + 0.5

    def test_scheduler_penalty_unit_survives_reward_consumed_once(self):
        from ctf_downloader.services.watch_service import PollScheduler
        s = PollScheduler(jitter=0.0, rng=lambda lo, hi: (lo + hi) / 2)
        s.register("notices", 15)
        s.set_penalty("notices", 90)
        s.reward("notices")            # reward KHÔNG được xoá penalty
        now = time.monotonic()
        dl = s.postpone("notices", now=now)
        assert dl - now == pytest.approx(90, abs=0.5)
        now2 = time.monotonic()        # penalty đã tiêu → về base
        dl2 = s.postpone("notices", now=now2)
        assert dl2 - now2 == pytest.approx(15, abs=0.5)


# ---------------------------------------------------------------------- #
# R3 — AuthService: exact URL-key trước heuristic, không leak chéo host
# ---------------------------------------------------------------------- #
class TestR3AuthUrlKeyExact:
    @staticmethod
    def _patch_cfg(monkeypatch, auth):
        from ctf_downloader.services import auth_service
        monkeypatch.setattr(auth_service, "load_global_config",
                            lambda: {"auth": auth})
        return auth_service.AuthService

    def test_exact_url_key_wins_over_heuristic(self, monkeypatch):
        AS = self._patch_cfg(monkeypatch, {
            "https://ctfA.com": {"cookie": "A_COOKIE"},
            "https://ctfB.com": {"cookie": "B_COOKIE"},
        })
        cookie, token = AS.resolve("https://ctfB.com/")
        assert cookie == "B_COOKIE", (
            "≥2 entry URL mà key đúng tồn tại vẫn trả None")

    def test_no_cross_platform_cookie_leak(self, monkeypatch):
        AS = self._patch_cfg(monkeypatch, {
            "https://ctfA.com": {"cookie": "A_COOKIE"},
        })
        cookie, _token = AS.resolve("https://unrelated-B.net")
        assert cookie is None, (
            "workspace-URL khác platform không được mượn cookie entry duy nhất")

    def test_unique_entry_same_host_variant_key_still_resolves(
            self, monkeypatch):
        AS = self._patch_cfg(monkeypatch, {
            "https://ctfA.com/": {"cookie": "A_COOKIE"},
        })
        cookie, _token = AS.resolve("https://ctfA.com")
        assert cookie == "A_COOKIE"

    def test_dir_workspace_exact_lookup_among_many_entries(
            self, tmp_path, monkeypatch):
        ws = tmp_path / "wsX"
        ws.mkdir()
        (ws / "challenges.json").write_text(json.dumps(
            {"ctf_info": {"url": "https://ctfB.com"}}), encoding="utf-8")
        AS = self._patch_cfg(monkeypatch, {
            "https://ctfA.com": {"cookie": "A_COOKIE"},
            "https://ctfB.com": {"cookie": "B_COOKIE"},
        })
        cookie, _token = AS.resolve(str(ws))
        assert cookie == "B_COOKIE"


# ---------------------------------------------------------------------- #
# R5 — session đi qua create_session, hết raw requests.Session()
# ---------------------------------------------------------------------- #
class TestR5SessionFactoryEverywhere:
    def test_no_raw_session_in_resolver_and_tempmail(self):
        import ctf_downloader
        base = Path(ctf_downloader.__file__).parent
        for rel in ("platforms/ctftime_resolver.py", "utils/tempmail.py"):
            src = (base / rel).read_text(encoding="utf-8")
            assert "requests.Session()" not in src, (
                f"{rel} còn tự tạo requests.Session() thay vì create_session")

    @staticmethod
    def _retry_total(sess, url):
        mr = sess.get_adapter(url).max_retries
        return getattr(mr, "total", 0)

    def test_tempmail_session_comes_from_factory(self):
        from ctf_downloader.utils.tempmail import TempMailClient
        sess = TempMailClient().session
        assert self._retry_total(sess, "https://api.mail.tm") == 3

    def test_ctftime_session_comes_from_factory(self):
        from ctf_downloader.platforms.ctftime_resolver import CTFtimeResolver
        sess = CTFtimeResolver().session
        assert self._retry_total(sess, "https://ctftime.org") == 3
        # UA bắt buộc của CTFtime vẫn được giữ sau khi chuyển factory
        assert sess.headers["User-Agent"].startswith("ctf-downloader/")


# ---------------------------------------------------------------------- #
# R6 — auto-sync enabled: global mặc định, workspace override
# ---------------------------------------------------------------------- #
class TestR6AutoSyncPrecedence:
    @staticmethod
    def _gc(monkeypatch, enabled):
        from ctf_downloader.storage import global_config as gc
        monkeypatch.setattr(gc, "load_global_config",
                            lambda: {"auto_sync": {"enabled": enabled}})

    def test_pure_resolution_two_tiers(self):
        from ctf_downloader.services.watch_service import (
            resolve_auto_sync_enabled)
        # Không workspace config → global là mặc định
        assert resolve_auto_sync_enabled(
            None, {"auto_sync": {"enabled": False}}) is False
        assert resolve_auto_sync_enabled(None, {}) is True
        assert resolve_auto_sync_enabled(None, None) is True
        # Có cả hai → workspace thắng
        assert resolve_auto_sync_enabled(
            {"auto_sync": {"enabled": True}},
            {"auto_sync": {"enabled": False}}) is True
        assert resolve_auto_sync_enabled(
            {"auto_sync": {"enabled": False}},
            {"auto_sync": {"enabled": True}}) is False
        # Workspace có config nhưng thiếu key → rơi xuống global
        assert resolve_auto_sync_enabled(
            {"auto_sync": {}}, {"auto_sync": {"enabled": False}}) is False

    def test_effective_flag_method_two_tiers(self, tmp_path, monkeypatch):
        from ctf_downloader.services.watch_service import WatchService
        self._gc(monkeypatch, False)
        svc = WatchService(str(tmp_path), once=True, use_live_ui=False)
        # Tầng 1: global off, chưa có workspace config → tắt
        assert svc._effective_auto_sync_enabled(svc._resolve_cfg()) is False
        # Tầng 2: workspace override ON thắng global OFF
        svc.cfg_store.save({"version": 1, "auto_sync": {"enabled": True}})
        assert svc._effective_auto_sync_enabled(svc._resolve_cfg()) is True
        # Workspace OFF + global ON → vẫn OFF (workspace thắng)
        self._gc(monkeypatch, True)
        svc.cfg_store.save({"version": 1, "auto_sync": {"enabled": False}})
        assert svc._effective_auto_sync_enabled(svc._resolve_cfg()) is False

    def test_run_gate_blocks_when_global_off(self, tmp_path, monkeypatch):
        from ctf_downloader.services.watch_service import WatchService
        self._gc(monkeypatch, False)
        svc = WatchService(str(tmp_path), once=True, use_live_ui=False)
        with patch.object(WatchService, "_setup_platform") as sp:
            rc = svc.run()
        assert rc == 0
        sp.assert_not_called()
        assert not (tmp_path / ".ctf" / "watch_state.json.lock").exists()

    def test_help_text_states_precedence(self):
        from ctf_downloader.cli_commands import _CONFIG_KEYS
        desc = _CONFIG_KEYS["auto-sync"]["desc"].lower()
        assert "workspace" in desc
        assert "mặc định" in desc
        assert "override" in desc or "ghi đè" in desc



def test_keepalive_expedite_shortens_deadline_once_without_interval_change():
    """Urgent tracker deadlines wake once; base ALIVE cadence stays 60s."""
    from ctf_downloader.services.watch_service import PollScheduler

    now = 1_000.0
    sched = PollScheduler(jitter=0.0, rng=lambda lo, hi: lo)
    sched.register("keepalive", 60, due_now=False)
    sched._tasks["keepalive"]["deadline"] = now + 60

    assert sched.expedite("keepalive", now + 5) is True
    assert sched._tasks["keepalive"]["interval"] == 60
    assert sched._tasks["keepalive"]["deadline"] == now + 5

    sched.postpone("keepalive", now=now + 5)
    assert sched._tasks["keepalive"]["interval"] == 60
    assert sched._tasks["keepalive"]["deadline"] == now + 65


def test_watch_service_keepalive_setup_failure_warns_once(tmp_path):
    from unittest.mock import patch

    from ctf_downloader.services.watch_service import WatchService

    svc = WatchService(str(tmp_path), once=True, use_live_ui=False)
    with patch("ctf_downloader.services.instance_service.InstanceService") as service_ctor, \
            patch.object(WatchService, "_setup_platform"), \
            patch.object(WatchService, "_resolve_window", return_value=None), \
            patch.object(WatchService, "_open_live"), \
            patch.object(WatchService, "_main_loop"), \
            patch.object(WatchService, "_shutdown"), \
            patch.object(WatchService, "_effective_auto_sync_enabled", return_value=True), \
            patch("ctf_downloader.services.instance_keepalive.InstanceKeepAlive",
                  side_effect=RuntimeError("setup boom")):
        service_ctor.return_value.repo = None
        assert svc.run() == 0

    assert "setup boom" in svc.keepalive_init_error
    with patch("ctf_downloader.services.watch_service.Logger.warning") as warning:
        assert svc._tick_keepalive() == []
        assert svc._tick_keepalive() == []
    messages = [call.args[0] for call in warning.call_args_list]
    assert sum(message.startswith("WatchService keepalive unavailable:")
               for message in messages) == 1


def test_keepalive_setup_warning_does_not_hide_other_watch_task_error(tmp_path):
    from unittest.mock import patch

    from ctf_downloader.services.watch_service import PollScheduler, WatchService

    scheduler = PollScheduler(jitter=0.0, rng=lambda lo, hi: lo)
    scheduler.register("scoreboard", 60)
    scheduler.register("keepalive", 60)
    svc = WatchService(str(tmp_path), once=True, use_live_ui=False,
                       scheduler=scheduler)
    svc.keepalive_init_error = "InstanceKeepAlive initialization failed: setup boom"
    with patch.object(svc, "_tick_scoreboard",
                      side_effect=RuntimeError("scoreboard boom")), \
            patch("ctf_downloader.services.watch_service.Logger.warning") as warning:
        lines = svc._run_round({})

    assert any("task scoreboard lỗi: scoreboard boom" in line for line in lines)
    messages = [call.args[0] for call in warning.call_args_list]
    assert sum(message.startswith("WatchService keepalive unavailable:")
               for message in messages) == 1


def test_keepalive_tick_supports_partially_constructed_watch_service():
    from ctf_downloader.services.watch_service import WatchService

    svc = WatchService.__new__(WatchService)
    svc.keepalive = None
    assert svc._tick_keepalive() == []


def test_watch_service_applies_expedite_only_for_tracker_deadline_states(tmp_path):
    from types import SimpleNamespace
    from ctf_downloader.services.watch_service import PollScheduler, WatchService

    svc = WatchService(str(tmp_path), once=True, use_live_ui=False,
                       scheduler=PollScheduler(jitter=0.0,
                                               rng=lambda lo, hi: lo))
    svc.scheduler.register("keepalive", 60, due_now=False)
    import time
    wall_base = time.time()
    mono_base = time.monotonic()
    svc.scheduler._tasks["keepalive"]["deadline"] = wall_base + 1000
    svc.keepalive = SimpleNamespace(trackers={
        "retry": SimpleNamespace(state="RENEW_FAILED", phase_deadline=mono_base + 100),
        "boot": SimpleNamespace(state="RESTARTING", phase_deadline=mono_base + 200),
        "backoff": SimpleNamespace(state="RESTART_BACKOFF", backoff_deadline=mono_base + 300),
        "alive": SimpleNamespace(state="ALIVE", phase_deadline=mono_base + 1),
    })

    svc._expedite_keepalive_deadline()
    assert abs(svc.scheduler._tasks["keepalive"]["deadline"] - (wall_base + 100)) < 0.1
    assert svc.scheduler._tasks["keepalive"]["interval"] == 60


def test_watch_round_applies_keepalive_expedite_after_regular_postpone(tmp_path):
    from types import SimpleNamespace
    from unittest.mock import patch
    import time

    from ctf_downloader.services.watch_service import PollScheduler, WatchService

    scheduler = PollScheduler(jitter=0.0, rng=lambda lo, hi: lo)
    scheduler.register("keepalive", 60, due_now=True)
    svc = WatchService(str(tmp_path), once=True, use_live_ui=False,
                       scheduler=scheduler)
    svc.keepalive = SimpleNamespace(trackers={
        "retry": SimpleNamespace(state="RENEW_FAILED",
                                  phase_deadline=time.monotonic() + 5),
    })
    with patch.object(svc, "_tick_keepalive", return_value=[]):
        svc._run_round({})

    assert scheduler._tasks["keepalive"]["interval"] == 60
    assert scheduler._tasks["keepalive"]["deadline"] < time.time() + 6


def test_update_local_instance_info_syncs_challenge_readme_and_parses_endpoints(tmp_path):
    import json
    from ctf_downloader.services.instance_service import InstanceService
    from ctf_downloader.storage.workspace_repo import WorkspaceRepo

    chal_dir = tmp_path / "Web" / "chall1"
    chal_sub = chal_dir / "challenge"
    solver_sub = chal_dir / "solver"
    chal_sub.mkdir(parents=True)
    solver_sub.mkdir(parents=True)

    meta_file = chal_dir / "metadata.json"
    meta_file.write_text(json.dumps({"id": 101, "name": "chall1", "category": "Web"}), encoding="utf-8")

    readme_file = chal_sub / "README.md"
    readme_file.write_text("# chall1\n\n## 📝 Description\nFind the flag.\n", encoding="utf-8")

    solve_file = solver_sub / "solve.py"
    solve_file.write_text('HOST = "old.host"\nPORT = 1111\nTARGET_URL = "http://old"\n', encoding="utf-8")

    svc = InstanceService.__new__(InstanceService)
    svc.workspace_path = str(tmp_path)
    svc.repo = WorkspaceRepo(str(tmp_path))

    # Test nc endpoint
    svc._update_local_instance_info(101, entry="nc 10.10.10.10 9999", time_left=1800, status="running")

    # Verify challenge/README.md was updated with the service block
    readme_content = readme_file.read_text(encoding="utf-8")
    assert "## 🔌 Connection / Service" in readme_content
    assert "nc 10.10.10.10 9999" in readme_content

    # Verify solve.py was updated with parsed host and port
    solve_content = solve_file.read_text(encoding="utf-8")
    assert 'HOST = "10.10.10.10"' in solve_content
    assert 'PORT = 9999' in solve_content

    # Test IPv6 host:port without crash
    svc._update_local_instance_info(101, entry="[::1]:8888", time_left=1200, status="running")
    solve_content_v6 = solve_file.read_text(encoding="utf-8")
    assert 'HOST = "::1"' in solve_content_v6
    assert 'PORT = 8888' in solve_content_v6

    # Test DEFAULT_HOST and DEFAULT_PORT in solve.py
    solve_file.write_text('DEFAULT_HOST = "old.pwn.host"\nDEFAULT_PORT = 1337\n', encoding="utf-8")
    svc._update_local_instance_info(101, entry="pwn.ctf.org:31337", time_left=600, status="running")
    solve_content_def = solve_file.read_text(encoding="utf-8")
    assert 'DEFAULT_HOST = "pwn.ctf.org"' in solve_content_def
    assert 'DEFAULT_PORT = 31337' in solve_content_def


def test_release_lock_preserves_other_pid(tmp_path):
    from pathlib import Path
    from ctf_downloader.services.watch_service import WatchStateStore

    store = WatchStateStore(str(tmp_path))
    lock_file = Path(store.lock_path)
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    lock_file.write_text("999999", encoding="utf-8")

    # release_lock without force does not remove lock of another PID
    store.release_lock(force=False)
    assert lock_file.exists()
    assert lock_file.read_text().strip() == "999999"

    # release_lock with force removes it
    store.release_lock(force=True)
    assert not lock_file.exists()


def test_hoard_flag_syncs_flag_txt(tmp_path):
    import json
    from ctf_downloader.services.submit_service import SubmitService
    from ctf_downloader.storage.workspace_repo import WorkspaceRepo

    chal_dir = tmp_path / "Crypto" / "rsa1"
    chal_dir.mkdir(parents=True)
    meta_file = chal_dir / "metadata.json"
    meta_file.write_text(json.dumps({"id": 42, "name": "rsa1", "category": "Crypto"}), encoding="utf-8")

    (tmp_path / "challenges.json").write_text(json.dumps({
        "ctf_info": {"url": "http://ctf.test", "platform_type": "ctfd"},
        "challenges": [{"id": 42, "name": "rsa1", "category": "Crypto"}]
    }), encoding="utf-8")

    svc = SubmitService.__new__(SubmitService)
    svc.workspace_dir = str(tmp_path)
    svc.repo = WorkspaceRepo(str(tmp_path))
    svc.url = "http://ctf.test"
    svc.explicit_flag_format = None
    svc.challenges_cache = {"42": {"id": 42, "name": "rsa1", "category": "Crypto"}}

    ok, msg = svc.hoard_flag(42, "FLAG{hoard_to_file}")
    assert ok is True

    flag_file = chal_dir / "flag.txt"
    assert flag_file.exists()
    assert flag_file.read_text(encoding="utf-8").strip() == "FLAG{hoard_to_file}"
