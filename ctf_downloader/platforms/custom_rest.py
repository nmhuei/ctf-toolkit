import re
import urllib.parse
import unicodedata
import requests
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup
from rich.markup import escape
from .base import BasePlatform, Challenge
from ..utils.logger import Logger
from .registry import register


@register("custom_rest", label="Custom REST / Next.js CTF", throttle=5.0)
class CustomRESTPlatform(BasePlatform):
    """
    Integration for modern Next.js / Node / REST CTF platforms (such as TamilCTF / CTF-Platform).
    Endpoints:
      - /api/auth/me
      - /api/challenges
      - /api/challenges/<id>
      - /api/challenges/<id>/submit
    """
    def __init__(self, base_url: str, session: requests.Session):
        from ..utils.urlnorm import normalize_base_url
        super().__init__(normalize_base_url(base_url), session)
        self.ctf_info.platform_type = "custom_rest"

    def _extract_title(self) -> None:
        try:
            h_resp = self.session.get(self.base_url, timeout=5)
            if h_resp.status_code == 200:
                soup = BeautifulSoup(h_resp.text, "html.parser")
                title_el = soup.find("title")
                if title_el and title_el.text:
                    self.ctf_info.title = title_el.text.strip().split(" - ")[0].split(" | ")[0].strip()
        except Exception:
            pass

        if not self.ctf_info.title or self.ctf_info.title == "CTF Competition":
            domain = urllib.parse.urlparse(self.base_url).netloc
            clean_dom = domain.replace("ctf.", "").replace("www.", "").replace(".org", "").replace(".com", "").replace(".", "_")
            self.ctf_info.title = f"{clean_dom.capitalize()}_CTF"

    def _extract_open_target_url(self, description: str) -> Optional[str]:
        """Return the URL behind an ``Open Target`` link in challenge HTML.

        Some REST platforms expose the challenge prompt as HTML and render
        the actual target only as a button in that prompt. Preserve the target
        as connection information; it is a live service URL, not an attachment
        to download as a challenge file.
        """
        if not description or "<" not in description:
            return None

        try:
            soup = BeautifulSoup(description, "html.parser")
            for anchor in soup.find_all("a", href=True):
                label = " ".join(anchor.get_text(" ", strip=True).split()).casefold()
                if label != "open target":
                    continue

                href = anchor["href"].strip()
                if not href or href.startswith(("#", "javascript:", "mailto:")):
                    continue
                target_url = self.get_full_file_url(href)
                if urllib.parse.urlparse(target_url).scheme in {"http", "https"}:
                    return target_url
        except Exception:
            return None

        return None

    def _fetch_challenge_page(self, name: str, item: Dict[str, Any],
                              detail_data: Dict[str, Any]) -> Optional[Tuple[str, str]]:
        """Fetch the platform's challenge page when its API omits prompt data."""
        page_path = (
            detail_data.get("challenge_page_url")
            or item.get("challenge_page_url")
            or detail_data.get("page_url")
            or item.get("page_url")
            # Several platforms use target_url for their internal challenge
            # page route; the actual external target is linked inside it.
            or detail_data.get("target_url")
            or item.get("target_url")
        )
        if not page_path:
            # Prefer the platform's canonical route key. Display names are
            # not guaranteed to map to URL slugs (for example, a challenge
            # named "Frequency and Consequence" can use the slug "misc2").
            slug = (
                detail_data.get("slug")
                or item.get("slug")
            )
            if not slug:
                ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
                slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.casefold()).strip("-")
            if not slug:
                return None
            page_path = f"/challenges/{urllib.parse.quote(str(slug).strip('/'))}/"

        page_url = self.get_full_file_url(str(page_path).strip())
        page = urllib.parse.urlparse(page_url)
        platform = urllib.parse.urlparse(self.base_url)
        if page.scheme not in {"http", "https"} or page.netloc != platform.netloc:
            return None

        try:
            response = self.session.get(page_url, timeout=10)
            if response.status_code == 200 and response.text:
                return response.text, response.url or page_url
        except Exception:
            pass
        return None

    def _extract_page_files(self, page_html: str, page_url: str) -> List[Tuple[str, str]]:
        """Return same-page artifact links omitted from the REST challenge API."""
        if not page_html or not page_url:
            return []

        try:
            soup = BeautifulSoup(page_html, "html.parser")
            page = urllib.parse.urlparse(page_url)
            page_prefix = page.path.rstrip("/") + "/"
            platform_host = urllib.parse.urlparse(self.base_url).netloc
            files: List[Tuple[str, str]] = []
            seen = set()

            for anchor in soup.find_all("a", href=True):
                href = anchor["href"].strip()
                if not href or href.startswith(("#", "javascript:", "mailto:")):
                    continue
                file_url = urllib.parse.urljoin(page_url, href)
                parsed = urllib.parse.urlparse(file_url)
                if (parsed.scheme not in {"http", "https"}
                        or parsed.netloc != platform_host
                        or not parsed.path.startswith(page_prefix)):
                    continue

                path_tail = parsed.path[len(page_prefix):].strip("/")
                if not path_tail:
                    continue
                label = " ".join(anchor.get_text(" ", strip=True).split())
                filename_match = re.search(r"[A-Za-z0-9_.-]+\.[A-Za-z0-9]{1,8}", label)
                filename = (
                    filename_match.group(0)
                    if filename_match
                    else urllib.parse.unquote(path_tail.rsplit("/", 1)[-1])
                )
                key = (file_url, filename)
                if key not in seen:
                    seen.add(key)
                    files.append(key)
            return files
        except Exception:
            return []

    def _extract_target_url_from_page(self, page_html: str,
                                     page_url: Optional[str] = None) -> Optional[str]:
        """Find the external link in the challenge page's Target section."""
        target_url = self._extract_open_target_url(page_html)
        if target_url:
            return target_url
        if not page_html:
            return None

        try:
            soup = BeautifulSoup(page_html, "html.parser")
            platform_host = urllib.parse.urlparse(self.base_url).netloc
            for card in soup.find_all(class_="card"):
                heading = card.find(["h1", "h2", "h3", "h4", "h5"])
                if not heading or " ".join(heading.get_text(" ", strip=True).split()).casefold() != "target":
                    continue
                for anchor in card.find_all("a", href=True):
                    target_url = urllib.parse.urljoin(
                        page_url or self.base_url, anchor["href"].strip())
                    parsed = urllib.parse.urlparse(target_url)
                    if parsed.scheme in {"http", "https"} and parsed.netloc != platform_host:
                        return target_url
        except Exception:
            return None
        return None

    @staticmethod
    def _page_text(page_html: str) -> str:
        """Get readable challenge-page text without navigation and scripts."""
        soup = BeautifulSoup(page_html, "html.parser")
        for element in soup.find_all(["script", "style", "nav", "header", "footer", "noscript"]):
            element.decompose()
        cards = soup.find_all(class_="card")
        if cards:
            return "\n\n".join(card.get_text("\n", strip=True) for card in cards)
        content = soup.find("main") or soup.body or soup
        return content.get_text("\n", strip=True)

    def authenticate(self) -> bool:
        """
        Validates authentication via /api/auth/me, /api/me, or checks challenge list.
        """
        self._extract_title()

        # Check /api/auth/me
        try:
            resp = self.session.get(f"{self.base_url}/api/auth/me", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                user_data = (
                    data.get("data", {}).get("user")
                    if isinstance(data, dict) and isinstance(data.get("data"), dict)
                    else (data.get("user") if isinstance(data, dict) else None)
                )
                if user_data:
                    username = user_data.get("username") or user_data.get("name") or user_data.get("email")
                    self.ctf_info.user_name = username
                    Logger.success(f"Đã xác thực User: [info]{escape(str(username))}[/info]", markup=True)
                    return True
        except Exception:
            pass

        # Check /api/me
        try:
            resp = self.session.get(f"{self.base_url}/api/me", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and (data.get("logged_in") or data.get("user")):
                    user_data = data.get("user") or {}
                    username = (
                        user_data.get("username")
                        or user_data.get("name")
                        or user_data.get("email")
                        or user_data.get("bracket")
                    )
                    if username:
                        self.ctf_info.user_name = username
                    Logger.success(f"Đã xác thực User: [info]{escape(str(username or 'logged_in'))}[/info]", markup=True)
                    return True
        except Exception:
            pass

        # Check /api/challenges directly
        try:
            resp = self.session.get(f"{self.base_url}/api/challenges", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                has_challs = False
                if isinstance(data, dict):
                    if data.get("success") and "challenges" in data.get("data", {}):
                        has_challs = True
                    elif "challenges" in data and isinstance(data["challenges"], list):
                        has_challs = True
                    elif isinstance(data.get("data"), list):
                        has_challs = True
                elif isinstance(data, list):
                    has_challs = True
                if has_challs:
                    Logger.info("Đã xác nhận truy cập public vào challenges trên nền tảng REST.")
                    return True
        except Exception:
            pass

        Logger.error("Xác thực thất bại trên nền tảng REST CTF.")
        return False

    def fetch_challenges(self) -> List[Challenge]:
        """
        Fetches all challenges via /api/challenges and detailed info via /api/challenges/{id}.
        """
        try:
            resp = self.session.get(f"{self.base_url}/api/challenges", timeout=15)
            if resp.status_code != 200:
                Logger.error(f"Không tải được challenges từ /api/challenges (HTTP {resp.status_code})")
                return []

            json_data = resp.json()
            raw_challs = []
            if isinstance(json_data, dict):
                if "challenges" in json_data and isinstance(json_data["challenges"], list):
                    raw_challs = json_data["challenges"]
                elif "data" in json_data:
                    data_field = json_data["data"]
                    if isinstance(data_field, dict) and "challenges" in data_field:
                        raw_challs = data_field["challenges"]
                    elif isinstance(data_field, list):
                        raw_challs = data_field
                elif json_data.get("success") is False:
                    Logger.error(f"Lỗi API: {json_data.get('error') or json_data.get('message')}")
                    return []
            elif isinstance(json_data, list):
                raw_challs = json_data

            if not isinstance(raw_challs, list):
                Logger.error("Không tìm thấy challenges trong response từ /api/challenges")
                return []

            if not raw_challs:
                Logger.info("Nền tảng REST CTF chưa có challenge nào (danh sách trống).")
                self.ctf_info.challenges = []
                return []

            Logger.info(f"Tìm thấy {len(raw_challs)} challenges trên nền tảng. Đang tải chi tiết...")

            detailed_challenges = []
            for item in raw_challs:
                if not isinstance(item, dict):
                    continue
                chall_id = item.get("id") or item.get("_id")
                name = item.get("title") or item.get("name", f"Challenge_{chall_id}")
                category = item.get("category", "Misc").strip().capitalize()
                points_raw = item.get("points") or item.get("maxPoints") or item.get("value") or 0
                try:
                    points = int(points_raw)
                except (ValueError, TypeError):
                    points = 0
                author = item.get("author")
                description = item.get("description") or item.get("prompt_text") or item.get("prompt_html") or ""
                tags = item.get("tags", [])
                is_solved = bool(item.get("isSolved") or item.get("solved") or item.get("solved_by_me"))
                solves = item.get("solves") or item.get("solves_count") or 0
                conn_info = item.get("target_url") or item.get("connection_info") or ""

                # Fetch detailed view if available
                detail_data = {}
                try:
                    det_resp = self.session.get(f"{self.base_url}/api/challenges/{chall_id}", timeout=10)
                    if det_resp.status_code == 200:
                        det_json = det_resp.json()
                        if isinstance(det_json, dict):
                            payload_data = det_json.get("data") if det_json.get("success") else None
                            if isinstance(payload_data, dict):
                                detail_data = (
                                    payload_data.get("challenge")
                                    if isinstance(payload_data.get("challenge"), dict)
                                    else payload_data
                                )
                            elif "challenge" in det_json and isinstance(det_json["challenge"], dict):
                                detail_data = det_json["challenge"]
                            elif "data" in det_json and isinstance(det_json["data"], dict):
                                detail_data = det_json["data"]
                            else:
                                detail_data = det_json
                            description = (
                                detail_data.get("description")
                                or detail_data.get("prompt_text")
                                or detail_data.get("prompt_html")
                                or description
                            )
                            if not conn_info and detail_data.get("target_url"):
                                conn_info = detail_data["target_url"]
                            elif not conn_info and detail_data.get("connection_info"):
                                conn_info = detail_data["connection_info"]
                except Exception:
                    pass

                # Some platforms only render the target button on the challenge
                # page, while their API omits both the prompt and target URL.
                page_html = None
                challenge_page_url = None
                open_target_url = self._extract_open_target_url(description)
                if not open_target_url:
                    page_result = self._fetch_challenge_page(name, item, detail_data)
                    if page_result:
                        page_html, challenge_page_url = page_result
                    open_target_url = self._extract_target_url_from_page(
                        page_html or "", challenge_page_url)
                if open_target_url:
                    conn_info = open_target_url
                if page_html:
                    description = self._page_text(page_html)

                # target_url may name the platform's own challenge page rather
                # than the live service. Keep such routes for fetching content,
                # but don't publish them as connection instructions.
                if conn_info:
                    # Only discard an absolute platform page URL. Relative target
                    # routes (for example "/challenges/foo/") are meaningful
                    # connection hints returned by some REST APIs.
                    raw_connection = str(conn_info)
                    parsed_connection = urllib.parse.urlparse(raw_connection)
                    base_host = urllib.parse.urlparse(self.base_url).netloc
                    if (parsed_connection.scheme in {"http", "https"}
                            and parsed_connection.netloc == base_host
                            and parsed_connection.path.rstrip("/").startswith("/challenges/")):
                        conn_info = None

                # Parse files/attachments
                files_list = []
                raw_files = (
                    detail_data.get("files")
                    or detail_data.get("attachments")
                    or item.get("files")
                    or item.get("attachments")
                    or []
                )
                if isinstance(raw_files, list):
                    for f in raw_files:
                        if isinstance(f, str):
                            files_list.append((self.get_full_file_url(f), f.split("/")[-1]))
                        elif isinstance(f, dict):
                            f_url = f.get("url") or f.get("location") or f.get("path")
                            f_name = f.get("name") or (f_url.split("/")[-1] if f_url else "attachment")
                            if f_url:
                                files_list.append((self.get_full_file_url(f_url), f_name))

                if page_html and challenge_page_url:
                    known_urls = {file_url for file_url, _ in files_list}
                    for file_url, file_name in self._extract_page_files(
                            page_html, challenge_page_url):
                        if file_url not in known_urls:
                            files_list.append((file_url, file_name))
                            known_urls.add(file_url)

                hints_list = []
                raw_hints = detail_data.get("hints") or item.get("hints") or []
                if isinstance(raw_hints, list):
                    for h in raw_hints:
                        if isinstance(h, str):
                            hints_list.append({"content": h})
                        elif isinstance(h, dict):
                            hints_list.append(h)

                chall_obj = Challenge(
                    id=chall_id,
                    name=name,
                    category=category,
                    points=points,
                    description=description,
                    author=author,
                    tags=tags,
                    hints=hints_list,
                    files=files_list,
                    connection_info=conn_info or None,
                    solved_by_me=is_solved,
                    solves_count=solves,
                    raw_data=detail_data or item
                )
                detailed_challenges.append(chall_obj)

            self.ctf_info.challenges = detailed_challenges
            return detailed_challenges

        except Exception as e:
            Logger.error(f"Lỗi khi tải challenges REST CTF: {str(e)}")
            return []

    def get_full_file_url(self, file_path: str) -> str:
        if file_path.startswith("http://") or file_path.startswith("https://"):
            return file_path
        return urllib.parse.urljoin(self.base_url, file_path)

    def submit_flag(self, challenge_id: Any, flag: str) -> Tuple[bool, str]:
        """
        Submits flag via /api/challenges/{challenge_id}/submit.
        """
        url = f"{self.base_url}/api/challenges/{challenge_id}/submit"
        payload = {"flag": flag.strip()}

        try:
            resp = self.session.post(url, json=payload, timeout=15)
            data = resp.json() if "json" in resp.headers.get("content-type", "") else {}

            if resp.status_code == 200 and data.get("success"):
                return True, "🎉 Flag chính xác! Đã giải xong challenge!"
            elif resp.status_code == 400:
                msg = data.get("message") or data.get("error") or "Flag không đúng."
                return False, f"❌ {msg}"
            elif resp.status_code == 403:
                msg = data.get("message") or data.get("error") or "Yêu cầu là thành viên team hoặc bị từ chối quyền."
                return False, f"🚫 {msg}"
            else:
                return False, f"Máy chủ trả HTTP {resp.status_code}: {data.get('message') or resp.text[:100]}"

        except Exception as e:
            return False, f"Ngoại lệ khi submit flag: {str(e)}"
