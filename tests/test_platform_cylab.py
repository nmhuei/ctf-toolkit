"""Unit test template for custom CTF platform adapter.

Usage:
1. Copy this template to `tests/test_platform_<platform_key>.py`.
2. Replace `cylab` with your platform key and verify deterministic behavior.
3. Run `pytest tests/test_platform_<platform_key>.py`.
"""
from unittest.mock import MagicMock
from ctf_downloader.platforms.registry import get_spec


def test_platform_lifecycle():
    base_url = "https://ctf.example.org"

    # Setup session mock
    session = MagicMock()
    resp_auth = MagicMock()
    resp_auth.status_code = 200
    resp_auth.json.return_value = {"username": "testuser"}

    resp_challs_p1 = MagicMock()
    resp_challs_p1.status_code = 200
    resp_challs_p1.json.return_value = {
        "count": 1,
        "results": [
            {
                "id": 1,
                "name": "Sanity Check",
                "category": "Misc",
                "event_points": 100,
                "solved_by_user": False,
            }
        ],
    }

    resp_inst = MagicMock()
    resp_inst.status_code = 200
    resp_inst.json.return_value = {
        "description": "Welcome <a href='/files/welcome.txt'>here</a>",
        "hints": ["Hint 1"],
        "endpoints": [{"hostname": "chall.cylab", "port": 1337}],
    }

    resp_submit = MagicMock()
    resp_submit.status_code = 200
    resp_submit.json.return_value = {"correct": True, "message": "Flag accepted!"}

    def fake_get(url, **kwargs):
        if "user_status" in url:
            return resp_auth
        if "instance" in url:
            return resp_inst
        if "challenges" in url:
            if "page=1" in url:
                return resp_challs_p1
            # Next page empty to break pagination
            empty = MagicMock()
            empty.status_code = 200
            empty.json.return_value = {"count": 1, "results": []}
            return empty
        return None

    session.get.side_effect = fake_get
    session.post.return_value = resp_submit

    spec = get_spec("cylab")
    platform = spec.cls(base_url, session)

    # 1. Test authentication
    assert platform.authenticate() is True

    # 2. Test challenges fetching
    challs = platform.fetch_challenges()
    assert len(challs) == 1
    assert challs[0].id == "1"
    assert challs[0].name == "Sanity Check"
    assert challs[0].category == "Misc"
    assert challs[0].points == 100
    assert challs[0].connection_info == "nc chall.cylab 1337"

    # 3. Test attachment URL resolution
    assert platform.get_full_file_url("files/welcome.txt") == "https://ctf.example.org/files/welcome.txt"

    # 4. Test flag submission
    ok, msg = platform.submit_flag("1", "FLAG{example}")
    assert ok is True
    assert platform.last_verdict == "correct"
