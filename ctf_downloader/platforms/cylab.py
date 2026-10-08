"""CyLab Security Academy Platform Adapter (picoCTF-based architecture)."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple
from urllib.parse import urljoin, urlsplit

from .base import BasePlatform, safe_get_json
from .registry import register
from ..models import Challenge
from ..utils.logger import Logger


@register(
    "cylab",
    label="CyLab Security Academy",
    throttle=2.0,
    html_markers=("CyLab Security Academy", "learn.cylabacademy.org"),
    cookie_hints=("sessionid", "csrftoken", "cf_clearance"),
    supports_container=True,
    supports_scoreboard=True,
)
class CylabAdapter(BasePlatform):
    """Platform driver for CyLab Security Academy."""

    @property
    def root_url(self) -> str:
        parsed = urlsplit(self.base_url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def authenticate(self) -> bool:
        """Validate active session credentials via /api/user_status/."""
        url = f"{self.root_url}/api/user_status/"
        data, status = safe_get_json(self.session, url, statuses=(200, 401, 403))
        if status == 200 and data is not None and isinstance(data, dict):
            Logger.info("Xác thực thành công trên CyLab Security Academy!")
            return True
        return False

    def fetch_challenges(self) -> List[Challenge]:
        """Fetch all challenges across paginated API and resolve instance details."""
        challenges: List[Challenge] = []
        page = 1
        page_size = 100

        while True:
            url = urljoin(f"{self.base_url}/", f"api/challenges/?page={page}&page_size={page_size}")
            data, status = safe_get_json(self.session, url, statuses=(200,))
            if status != 200 or not data or not isinstance(data, dict):
                break

            results = data.get("results", [])
            if not results:
                break

            total_count = data.get("count", 0)
            Logger.info(f"Đang tải trang {page} ({len(results)} challenges / tổng {total_count})...")

            for item in results:
                cid = str(item.get("id", ""))
                if not cid:
                    continue

                name = str(item.get("name", f"Challenge {cid}"))
                cat_raw = item.get("category")
                if isinstance(cat_raw, dict):
                    category = str(cat_raw.get("name", "Misc")).strip()
                else:
                    category = str(cat_raw or "Misc").strip()

                points = int(item.get("event_points") or 0)
                solved_by_me = bool(item.get("solved_by_user", False))

                # Fetch instance detail (description, hints, file links)
                inst_url = urljoin(f"{self.base_url}/", f"api/challenges/{cid}/instance/")
                inst_data, inst_status = safe_get_json(self.session, inst_url, statuses=(200,))

                description = ""
                hints: List[str] = []
                files_urls: List[str] = []
                connection_info = ""

                if inst_status == 200 and isinstance(inst_data, dict):
                    description = str(inst_data.get("description", ""))
                    hints = [str(h) for h in inst_data.get("hints", [])]
                    
                    # Extract files from description links
                    # e.g. <a href='https://challenge-files.cylabacademy.net/...' download>here</a>
                    file_links = re.findall(r'<a\s+[^>]*href=[\'"]([^\'"]+)[\'"]', description)
                    for fl in file_links:
                        if not fl.startswith("#") and not fl.startswith("javascript:"):
                            files_urls.append(self.get_full_file_url(fl))

                    # Extract netcat endpoints
                    endpoints = inst_data.get("endpoints", [])
                    if isinstance(endpoints, list) and endpoints:
                        ep_strs = []
                        for ep in endpoints:
                            if isinstance(ep, dict):
                                h = ep.get("hostname")
                                p = ep.get("port")
                                if h and p:
                                    ep_strs.append(f"nc {h} {p}")
                        if ep_strs:
                            connection_info = "; ".join(ep_strs)

                ch = Challenge(
                    id=cid,
                    name=name,
                    category=category,
                    points=points,
                    description=description,
                    hints=hints,
                    files=files_urls,
                    solved_by_me=solved_by_me,
                    connection_info=connection_info,
                )
                challenges.append(ch)

            # Check if there are more pages
            if len(challenges) >= total_count or len(results) < page_size:
                break
            page += 1

        Logger.success(f"Đã chuẩn hóa thành công {len(challenges)} challenges từ CyLab Security Academy.")
        return challenges

    def get_full_file_url(self, file_path: str) -> str:
        """Convert relative attachment path to full URL."""
        if file_path.startswith(("http://", "https://")):
            return file_path
        return urljoin(f"{self.base_url}/", file_path.lstrip("/"))

    def _get_csrf_and_headers(self) -> Dict[str, str]:
        csrf = ""
        cookies = getattr(self.session, "cookies", None)
        if cookies:
            try:
                csrf = cookies.get("csrftoken", "")
            except Exception:
                pass
        headers = {
            "Content-Type": "application/json",
            "Referer": f"{self.root_url}/library"
        }
        if csrf:
            headers["X-CSRFToken"] = csrf
        return headers

    def start_instance(self, challenge_id: Any) -> Tuple[bool, Dict[str, Any]]:
        """Start/deploy on-demand container instance."""
        headers = self._get_csrf_and_headers()
        url = f"{self.root_url}/api/challenges/{challenge_id}/instance/"
        try:
            resp = self.session.put(url, json={}, headers=headers, timeout=20)
            if resp.status_code in (200, 204):
                import time
                status_info = self.get_instance_status(challenge_id)
                for _ in range(5):
                    if status_info.get("status") == "running" and status_info.get("entry"):
                        break
                    time.sleep(2)
                    status_info = self.get_instance_status(challenge_id)
                return True, status_info
            return False, {"message": f"Failed to start instance (status {resp.status_code}): {resp.text[:100]}"}
        except Exception as e:
            return False, {"message": f"Error starting instance: {e}"}

    def stop_instance(self, challenge_id: Any) -> Tuple[bool, str]:
        """Stop/destroy active container instance."""
        headers = self._get_csrf_and_headers()
        url = f"{self.root_url}/api/challenges/{challenge_id}/instance/"
        try:
            resp = self.session.delete(url, headers=headers, timeout=15)
            if resp.status_code in (200, 204):
                return True, "Container stopped successfully."
            return False, f"Failed to stop instance (status {resp.status_code}): {resp.text[:100]}"
        except Exception as e:
            return False, f"Error stopping instance: {e}"

    def extend_instance(self, challenge_id: Any) -> Tuple[bool, str]:
        """Extend lifetime of active container instance."""
        headers = self._get_csrf_and_headers()
        url = f"{self.root_url}/api/challenges/{challenge_id}/instance/"
        try:
            resp = self.session.put(url, json={}, headers=headers, timeout=15)
            if resp.status_code in (200, 204):
                return True, "Container extended successfully."
            return False, f"Failed to extend instance: status {resp.status_code}"
        except Exception as e:
            return False, f"Error extending instance: {e}"

    def get_instance_status(self, challenge_id: Any) -> Dict[str, Any]:
        """Get current status and endpoint connection of container instance."""
        headers = self._get_csrf_and_headers()
        url = f"{self.root_url}/api/challenges/{challenge_id}/instance/"
        try:
            resp = self.session.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                return {"status": "error", "entry": None, "time_left": None, "message": f"HTTP {resp.status_code}"}
            data = resp.json()
            is_running = str(data.get("status", "")).upper() == "RUNNING"
            expires_in = data.get("expires_in")
            
            entry = None
            endpoints = data.get("endpoints", [])
            if isinstance(endpoints, list) and endpoints:
                ep0 = endpoints[0]
                if isinstance(ep0, dict) and ep0.get("hostname") and ep0.get("port"):
                    entry = f"{ep0['hostname']}:{ep0['port']}"
            
            if not entry:
                desc = str(data.get("description", ""))
                nc_match = re.search(r"nc\s+([a-zA-Z0-9.-]+)\s+(\d+)", desc)
                if nc_match:
                    entry = f"{nc_match.group(1)}:{nc_match.group(2)}"
                else:
                    url_match = re.search(r"https?://([a-zA-Z0-9.-]+(?::\d+)?)", desc)
                    if url_match:
                        entry = url_match.group(1)

            return {
                "status": "running" if is_running else "stopped",
                "entry": entry,
                "time_left": expires_in,
                "description": data.get("description", ""),
                "on_demand": bool(data.get("on_demand", False)),
            }
        except Exception as e:
            return {"status": "error", "entry": None, "time_left": None, "message": str(e)}

    def submit_flag(self, challenge_id: Any, flag: str) -> Tuple[bool, str]:
        """Submit flag to /api/submissions/ with CSRF verification."""
        url = f"{self.root_url}/api/submissions/"
        headers = self._get_csrf_and_headers()

        try:
            cid_int = int(challenge_id)
        except ValueError:
            cid_int = challenge_id

        payload = {"challenge": cid_int, "flag": flag.strip()}

        try:
            resp = self.session.post(url, json=payload, headers=headers, timeout=15)
            data = resp.json()
            is_correct = bool(data.get("correct", False))
            self.last_verdict = "correct" if is_correct else "incorrect"
            msg = "Correct flag!" if is_correct else "Incorrect flag."
            return is_correct, msg
        except Exception as e:
            return False, f"Submit error: {e}"
