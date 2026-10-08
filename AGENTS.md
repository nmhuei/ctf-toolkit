# Antigravity Agent Guidelines for auto_download_ctf_challenge (ASD-STE100 Standard)

## 1. Collaborative Architecture and Review Rule
- **Cronjob Verification:**
  - When the 20-minute cronjob triggers, verify adherence to `AGENTS.md` rules.

## 2. Zero-Hardcoding and Dynamic Extensibility
- **Platform Extensibility:**
  - Do NOT hardcode platform identifiers, adapters, or choices in core logic or menus.
  - Use dynamic platform discovery to load declarative JSON schemas and Python adapters.
  - Provide standardized platform templates for new platform integration.
- **Theme and UI Tokens:**
  - Do NOT hardcode colors, hex codes, or paths in business logic.
  - Import semantic color tokens exclusively from `ctf_downloader.ui.theme`:
    - `ACCENT`, `ACCENT_DEEP`, `FG_BASE`, `FG_FAINT`, `FG_MUTED`, `SUCCESS`, `SOLVED`, `WARN`, `ERROR`, `INFO`.
    - Do NOT use `DANGER` (use `ERROR` instead).

## 3. Autonomous Execution Authority
- **Self-Directed Refactoring:**
  - The agent has full authority to design, refactor, and optimize code for simplicity and performance.
  - Execute planning, implementation, testing, and debugging continuously without blocking for confirmation.

## 4. Solver Testing and Validation
- **Acceptance Criteria:**
  - Solver engine tests (AGYworker, SuperBQA) pass when the execution pipeline operates stably and prompt formatting succeeds.
  - Do NOT require a complete live CTF flag extraction during local unit tests.

## 5. User Interface Standards
- **Layout Consistency:**
  - Enforce uniform Cockpit layout across all interactive menus and hub displays.
  - Use `Table.grid(padding=(0, 1))` enclosed in `Padding(grid, (0, 2))`.
  - Do NOT use manual space padding strings.
- **Standard Action Columns:**
  - Structure grid columns: `[Key]`, `[Swatch]` (theme previews), and `[Title]`.
  - Highlight active entries in green (`menu.active`).
  - Embed option `[0]` (`Return to Main Menu`) directly within the table.
- **Exception Isolation:**
  - Enclose UI loops in `try...except (EOFError, KeyboardInterrupt): break`.
  - Isolate BQA auto-recovery (`offer_bqa_recovery`) from interactive console menus.

## 6. Isolated Test Environment & Sandbox Rule (bqa-trash)
- **Mandatory Sandbox Location (`~/Downloads/bqa-trash/`):**
  1. *Sân chơi nghịch ngợm thoải mái:* Cho phép tải file tạm, chạy script nháp, cào dữ liệu rác, bung file nén trong `~/Downloads/bqa-trash/`.
  2. *Không bị mất khi tắt máy:* Nằm trên ổ cứng thật nên dữ liệu không bị xóa khi shutdown (ưu điểm hơn `/tmp`).
  3. *Thùng rác một chạm:* Người dùng có thể xóa sạch toàn bộ thư mục này bất kỳ lúc nào mà không sợ xóa nhầm mã nguồn chính.
- **Cleanliness:**
  - Do NOT create test files or folders in the repository root.

## 7. ASD-STE100 Documentation and Communication Standard
- **Scope:** All documentation, guidelines, comments, and reports MUST adhere to ASD-STE100 principles.
- **Rules:**
  - Write short sentences (< 25 words).
  - Use direct, active imperative verbs.
  - Use consistent technical terms across modules.
  - Present information in structured tables and concise steps.
