from pathlib import Path
from types import SimpleNamespace

from ctf_downloader.models import Challenge
from ctf_downloader.services.pull_service import PullService
from ctf_downloader.storage.workspace_repo import WorkspaceRepo


def test_pull_refresh_preserves_existing_metadata_state(tmp_path, monkeypatch):
    config = SimpleNamespace(
        output_dir=str(tmp_path),
        url="https://example.test",
        timeout=5,
        force_redownload=False,
        size_limit_bytes=None,
        verify_downloads=False,
        allow_private_redirects=False,
        download_third_party=False,
        create_solve_template=False,
    )
    challenge = Challenge(
        id="rest-1",
        name="REST challenge",
        category="web",
        description="updated description",
    )

    old_dir = Path(tmp_path) / "REST challenge-rest-1"
    old_dir.mkdir()
    WorkspaceRepo(str(tmp_path)).write_metadata(
        old_dir / "metadata.json",
        {
            "id": "rest-1",
            "name": "REST challenge",
            "submitted_flag": "local-only",
            "status": {"solved": True},
        },
    )

    monkeypatch.setattr(
        "ctf_downloader.services.pull_service.DownloadManager.download_challenge_files",
        lambda *args, **kwargs: [],
    )

    PullService._full_process(config, object(), challenge)

    refreshed = WorkspaceRepo(str(tmp_path)).read_metadata(old_dir / "metadata.json")
    assert refreshed["submitted_flag"] == "local-only"
    assert refreshed["status"] == {"solved": True}
