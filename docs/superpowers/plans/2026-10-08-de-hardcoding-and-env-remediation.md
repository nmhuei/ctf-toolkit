# De-Hardcoding and Environment Variable Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement zero-dependency `.env` loading and eliminate hardcoded platform checks, colors, paths, and ports across the CTF toolkit.

**Architecture:** Create `ctf_downloader.utils.env_loader` to automatically populate `os.environ` from hierarchical `.env` files. Extend `BasePlatform` with polymorphic email verification and capability flags to eliminate hardcoded platform strings in services. Replace hardcoded UI markup with semantic theme tokens, and allow dynamic port/path overrides.

**Tech Stack:** Python 3.10+, standard library only for `.env` parsing, Rich library semantic tokens, Pytest.

**Spec:** ASD-STE100 guidelines, AGENTS.md zero-hardcoding rule, platform extensibility standard.

## Global Constraints
- Do NOT add external dependencies (no third-party python-dotenv).
- Do NOT hardcode platform identifiers in core services.
- Import semantic color tokens exclusively from `ctf_downloader.ui.theme`.
- Keep sentences short (< 25 words) per ASD-STE100 standard.
- Ensure all existing and new unit tests pass with zero regressions.

---

### Task 1: Zero-Dependency `.env` Loader & Comprehensive `.env.example`

**Files:**
- Create: `ctf_downloader/utils/env_loader.py`
- Modify: `ctf_downloader/cli.py`
- Modify: `ctf_downloader/__init__.py`
- Modify: `ctf_downloader/solver/settings.py`
- Modify: `.env.example`
- Test: `tests/test_env_loader.py`

**Interfaces:**
- Produces: `load_dotenv(target_path: Optional[Union[str, Path]] = None, override: bool = False) -> Dict[str, str]`

- [x] **Step 1: Write unit tests in `tests/test_env_loader.py`**
- [x] **Step 2: Implement `ctf_downloader/utils/env_loader.py`**
- [x] **Step 3: Connect `load_dotenv()` into `cli.py`, `__init__.py`, and `settings.py`**
- [x] **Step 4: Update `.env.example` with all 14 project environment variables**
- [x] **Step 5: Run `pytest tests/test_env_loader.py` to verify**

---

### Task 2: Eliminate Hardcoded Platform Checks in Services (Polymorphism)

**Files:**
- Modify: `ctf_downloader/platforms/base.py`
- Modify: `ctf_downloader/platforms/ctfd.py`
- Modify: `ctf_downloader/platforms/gzctf.py`
- Modify: `ctf_downloader/platforms/rctf.py`
- Modify: `ctf_downloader/services/register_service.py`
- Modify: `ctf_downloader/services/instance_keepalive.py`
- Modify: `ctf_downloader/services/watch_service.py`
- Test: `tests/test_platform_polymorphism.py`

**Interfaces:**
- Produces on `BasePlatform`:
  - `verify_email(token: str, email: str = "", extra: Dict[str, Any] = None) -> Tuple[bool, Dict[str, Any]]`
  - `extract_verify_payload(url: str) -> Optional[Dict[str, Any]]`
  - `supports_notices: bool`
  - `notices_endpoint: Optional[str]`
  - `min_instance_op_gap_seconds: float`
  - `max_instance_renews: Optional[int]`

- [x] **Step 1: Write test for platform email verification and capability flags in `tests/test_platform_polymorphism.py`**
- [x] **Step 2: Add interface methods and properties to `BasePlatform` and adapters**
- [x] **Step 3: Refactor `RegisterService` to use polymorphic email verification**
- [x] **Step 4: Refactor `InstanceKeepalive` and `WatchService` to use adapter properties instead of hardcoded strings**
- [x] **Step 5: Run tests to verify zero regressions**

---

### Task 3: Replace Hardcoded UI Color Markup with Semantic Tokens

**Files:**
- Modify: `ctf_downloader/interactive_menu.py`
- Test: `tests/test_theme_tokens_consistency.py`

**Interfaces:**
- Consumes: `ctf_downloader.ui.theme` semantic tokens (`ACCENT`, `INFO`, `SUCCESS`, `WARN`, `FG_BASE`)

- [x] **Step 1: Write AST test checking for bare `[cyan]`, `[green]`, `[yellow]` tags in `interactive_menu.py`**
- [x] **Step 2: Refactor `interactive_menu.py` lines 1353, 1356, 1357, 1423, 1426, 1430, 1626 to use semantic theme tokens**
- [x] **Step 3: Run UI tests to confirm proper rendering**

---

### Task 4: Dynamic Overrides for Ports, Paths & Binaries

**Files:**
- Modify: `ctf_downloader/storage/global_config.py`
- Modify: `ctf_downloader/bridge/constants.py`
- Modify: `ctf_downloader/services/burp_service.py`
- Modify: `ctf_downloader/services/web_dashboard.py`
- Modify: `ctf_downloader/utils/agy_resolver.py`
- Test: `tests/test_dynamic_overrides.py`

- [x] **Step 1: Write test verifying environment overrides for ports, workspace root, and binary resolution**
- [x] **Step 2: Implement `CTF_WORKSPACE_ROOT` fallback in `global_config.py`**
- [x] **Step 3: Implement port overrides in `bridge/constants.py`, `burp_service.py`, `web_dashboard.py`**
- [x] **Step 4: Add user-space Antigravity binary paths to `agy_resolver.py`**
- [x] **Step 5: Run tests to verify all overrides work as expected**

---

### Task 5: Final Validation & Integration

- [x] **Step 1: Run full test suite to guarantee 100% green tests**
- [x] **Step 2: Check git status and whitespace errors via `git diff --check`**
- [x] **Step 3: Stage changes and create clean commit**
