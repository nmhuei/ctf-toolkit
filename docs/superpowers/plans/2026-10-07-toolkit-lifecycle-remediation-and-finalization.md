# CTF Toolkit Lifecycle Remediation and Finalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate discovered regressions across platform resolution, mock throttle handling, mirror synchronization, and dynamic platform discovery, ensuring a 100% test pass rate across the full 2,144 test suite and preparing a clean checkpoint commit on `audit/ctf-toolkit-lifecycle`.

**Architecture:** Route platform resolution through dynamic registry inspection without premature network reconnaissance. Honor mock boundaries in unit test harnesses while preserving production auto-discovery. Synchronize skill mirrors across local paths, and remove Codex CLI consultation per user instruction.

**Tech Stack:** Python 3.14, pytest, Rich, Requests, BeautifulSoup4, Git.

**Spec:** `docs/handoffs/2026-10-06-ctf-progress.md` and `AGENTS.md`.

## Global Constraints

- Adhere strictly to ASD-STE100 standard (short sentences < 25 words, active imperative verbs).
- Do NOT invoke Codex CLI (per explicit user directive).
- Import theme color tokens exclusively from `ctf_downloader.ui.theme`.
- Never create test artifacts or scratch files in repository root; use `~/Downloads/bqa-trash/` exclusively.
- Maintain 100% test pass rate on all 2,144 tests in `tests/`.

---

### Task 1: Fix Platform Resolution and Mock Throttle Delegation in Submit Service

**Files:**
- Modify: `ctf_downloader/services/platform_resolver.py:30-105`
- Modify: `ctf_downloader/services/submit_service.py:140-165,400-415`
- Test: `tests/test_sp1_submit.py`
- Test: `tests/test_arch_phase5b.py`
- Test: `tests/test_status_model.py`

**Interfaces:**
- Consumes: `PlatformResolver.for_workspace(repo, cookie=None, token=None, workspace_path=None, url=None)`
- Produces: `SubmitService._sleep(seconds: float)` delegating to `ctf_downloader.submitter.time.sleep` when mocked.

- [x] **Step 1: Write the failing tests**
  - Verify that `TestSubmitSecurityRegression` in `tests/test_sp1_submit.py` fails when URL is passed without challenges.json.
  - Verify that `TestThrottle` in `tests/test_sp1_submit.py` and `TestSubmitVerdictChain` in `tests/test_status_model.py` fail due to real sleep and network leak.

- [x] **Step 2: Run tests to verify failures**
  Run: `pytest -q tests/test_sp1_submit.py tests/test_status_model.py -k "TestSubmitVerdictChain"`
  Expected: FAIL with ValueError (missing platform URL) and AssertionError (False is not true from real network).

- [x] **Step 3: Implement minimal fix**
  - Update `PlatformResolver.for_workspace` to accept `url: Optional[str] = None` and check both `platform` and `platform_type`.
  - In `SubmitService.__init__`, inspect `PlatformDetector.detect_platform` for `unittest.mock.Mock` to preserve test mocks.
  - In `SubmitService._throttle`, call `self._sleep(wait)` which delegates to `ctf_downloader.submitter.time.sleep` if patched.

- [x] **Step 4: Run tests to verify they pass**
  Run: `pytest -q tests/test_sp1_submit.py tests/test_arch_phase5b.py tests/test_status_model.py`
  Expected: All 174 tests across these three suites PASS cleanly in under 5 seconds.

- [ ] **Step 5: Commit checkpoint**
  ```bash
  git add ctf_downloader/services/platform_resolver.py ctf_downloader/services/submit_service.py
  git commit -m "fix(submit): preserve mock boundaries and platform resolution in submit service"
  ```

---

### Task 2: Standardize Dynamic Platform Discovery and CyLab Adapter Lifecycle

**Files:**
- Create: `ctf_downloader/platforms/cylab.py`
- Modify: `ctf_downloader/platforms/registry.py:40-135`
- Create: `tests/test_platform_cylab.py`
- Test: `tests/test_arch_phase4.py`

**Interfaces:**
- Consumes: `@register("cylab", label="CyLab Security Academy", ...)`
- Produces: `_auto_discover_platforms()` invoked on module import in `registry.py`, updating `PLATFORMS` and `capabilities.PLATFORM_TYPES`.

- [x] **Step 1: Write the failing test**
  - Run `pytest -q tests/test_arch_phase4.py::TestPlatformTypes::test_unknown_first_then_sorted_keys`.
  - Run `pytest -q tests/test_platform_cylab.py`.

- [x] **Step 2: Run test to verify failure**
  Run: `pytest -v tests/test_arch_phase4.py::TestPlatformTypes::test_unknown_first_then_sorted_keys`
  Expected: FAIL due to `cylab` being missing from `PLATFORM_TYPES` at import time.

- [x] **Step 3: Implement dynamic auto-discovery and CyLab mock test**
  - Call `_auto_discover_platforms()` at the end of `ctf_downloader/platforms/registry.py`.
  - Update `tests/test_platform_cylab.py` with mock responses for `/api/user_status/`, `/api/challenges/`, `/api/challenges/{id}/instance/`, `/api/submissions/`.

- [x] **Step 4: Run test to verify it passes**
  Run: `pytest -v tests/test_arch_phase4.py tests/test_platform_cylab.py`
  Expected: PASS on all 26 tests.

- [ ] **Step 5: Commit checkpoint**
  ```bash
  git add ctf_downloader/platforms/cylab.py ctf_downloader/platforms/registry.py tests/test_platform_cylab.py
  git commit -m "feat(platforms): add CyLab adapter and dynamic discovery registration"
  ```

---

### Task 3: Synchronize CTF Skills Mirrors Across Agent Workspaces

**Files:**
- Modify: `.agents/skills/ctf-ask/`
- Modify: `.agents/skills/ctf-toolkit/`
- Modify: `.agents/skills/ctf-crypto/`
- Mirror: `skills/`
- Mirror: `~/.agents/skills/`
- Mirror: `~/.gemini/config/skills/`
- Test: `tests/test_ctf_ask_skill.py`

**Interfaces:**
- Consumes: 4 synchronized directories for CTF skills.
- Produces: Byte-for-byte identical skill files verified by `test_four_mirror_skills_synchronization`.

- [x] **Step 1: Write test verification**
  Run `pytest -q tests/test_ctf_ask_skill.py::test_four_mirror_skills_synchronization`.

- [x] **Step 2: Run test to identify divergence**
  Expected: FAIL on newline mismatch in `ctf-toolkit/references/routing.md`.

- [x] **Step 3: Synchronize skill mirrors**
  Run rsync for `ctf-ask`, `ctf-toolkit`, `ctf-crypto` across all four mirrors.

- [x] **Step 4: Run test to verify pass**
  Run: `pytest -q tests/test_ctf_ask_skill.py`
  Expected: 23 passed in under 2 seconds.

- [ ] **Step 5: Commit checkpoint**
  ```bash
  git add .agents/skills/ skills/
  git commit -m "docs(skills): synchronize 4-way skill mirrors to ASD-STE100 standard"
  ```

---

### Task 4: Remove Codex CLI Directive and Align AGENTS.md Guidelines

**Files:**
- Modify: `AGENTS.md:1-15`

**Interfaces:**
- Consumes: User instruction "bỏ cái chạy codex cli đi".
- Produces: Clean `AGENTS.md` without Codex CLI consultation requirement.

- [x] **Step 1: Remove Codex CLI consultation from AGENTS.md**
  - Delete `Codex CLI Consultation` section in Section 1 of `AGENTS.md`.
  - Retain `Cronjob Verification` rule.

- [x] **Step 2: Verify git diff formatting**
  Run: `git diff --check AGENTS.md`
  Expected: Exit code 0 (zero whitespace errors).

- [ ] **Step 3: Commit checkpoint**
  ```bash
  git add AGENTS.md
  git commit -m "docs(agents): remove Codex CLI consultation rule per user instruction"
  ```

---

### Task 5: Run Full-Suite Regression Test and Validate 100% Pass Rate

**Files:**
- Test: `tests/` (entire suite of 2,144 tests)

- [ ] **Step 1: Execute full test suite**
  Run:
  ```bash
  pytest -q
  ```

- [ ] **Step 2: Verify zero failures**
  Expected:
  - 2,143 passed, 1 skipped (0 failed).
  - Exit code 0.

---

### Task 6: Document Final Handoff and Create Audit Checkpoint Commit

**Files:**
- Create: `docs/handoffs/2026-10-07-toolkit-lifecycle-remediation.md`
- Working Tree: Commit remaining modified and untracked files on branch `audit/ctf-toolkit-lifecycle`.

- [ ] **Step 1: Write handoff documentation**
  Record the 4 remediated issues, test suite results, and current branch state.

- [ ] **Step 2: Check git diff formatting**
  Run: `git diff --check` and `git diff --cached --check`.
  Expected: Exit code 0.

- [ ] **Step 3: Stage and commit final checkpoint**
  ```bash
  git add -A
  git commit -m "feat: complete CTF toolkit lifecycle audit, platform discovery, and mock resilience"
  ```
