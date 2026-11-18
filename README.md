<div align="center">

# GGCAL-sync

**Headless timetable scraper and Google Calendar sync for FTU HCMC.**

[![CI](https://github.com/doducanhkhoi-ops/GGCAL-sync/actions/workflows/ci.yml/badge.svg)](https://github.com/doducanhkhoi-ops/GGCAL-sync/actions/workflows/ci.yml)
[![Security Audit](https://github.com/doducanhkhoi-ops/GGCAL-sync/actions/workflows/security.yml/badge.svg)](https://github.com/doducanhkhoi-ops/GGCAL-sync/actions/workflows/security.yml)
[![CodeQL](https://github.com/doducanhkhoi-ops/GGCAL-sync/actions/workflows/codeql.yml/badge.svg)](https://github.com/doducanhkhoi-ops/GGCAL-sync/actions/workflows/codeql.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/doducanhkhoi-ops/GGCAL-sync)](./LICENSE)

</div>

---

Pulls weekly class schedules from `qldt.hcmc.ftu.edu.vn` and pushes them to Google Calendar with automatic OAuth token refresh, duplicate prevention, and makeup-class tagging.

---

## Why GGCAL-sync?

- **6-week lookahead**: Scans 6 upcoming weeks by default (`--weeks N` to override) in a single headless session.
- **2x daily automation**: GitHub Actions cron runs at `07:00` and `18:00 ICT` (`00:00` / `11:00 UTC`) with zero local uptime required.
- **Zero duplicates**: Queries `calendars/primary/events` per time window before inserting, skipping already-synced classes.
- **Makeup detection**: Flags `tkb-daybu` cells and makeup keywords with `[HỌC BÙ]` and Google Calendar `colorId: 3`.
- **Dual reminders**: Attaches `120m` and `30m` popup alerts to every synced session in `Asia/Ho_Chi_Minh`.
- **Browser fallback**: Launches headless Chrome via Selenium 4 and falls back to Edge if Chrome is unavailable.

---

## Feature Overview

| Component | Behavior |
| --- | --- |
| **Scraper** | Authenticates on FTU HCMC portal and paginates weekly timetable views |
| **HTML Parser** | Resolves `rowspan`/`colspan` grid cells into structured JSON events |
| **OAuth Manager** | Validates `token.json` and refreshes expired access tokens via `oauth2.googleapis.com` |
| **Calendar Sync** | Deduplicates by `[start_iso, end_iso]` window and writes events via Calendar API v3 |
| **CLI** | Supports `--weeks`, `--dry-run`, `--parse-html`, and `--version` |

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/doducanhkhoi-ops/GGCAL-sync.git
cd GGCAL-sync
pip install -r requirements.txt
```

### 2. Configure credentials

Create `.env` from the template:

```bash
cp .env.example .env
```

```env
STUDENT_ID=your_student_id
STUDENT_PASS=your_password
```

Place your Google OAuth Desktop app client file as `credentials.json` and `token.json` in the repository root.

> [!NOTE]
> Set the OAuth consent screen publishing status to **In production** in Google Cloud Console so refresh tokens do not expire after 7 days.

### 3. Run

```bash
# Sync next 6 weeks (default)
python main_sync.py

# Dry run without writing to Google Calendar
python main_sync.py --weeks 4 --dry-run

# Parse a saved HTML timetable to JSON
python main_sync.py --parse-html tests/fixtures/sample_timetable.html
```

Output (`--parse-html`):

```json
[
  {
    "course": "Kinh tế lượng",
    "group": "K59.1",
    "room": "A201",
    "teacher": "Nguyễn Văn A",
    "is_makeup": false,
    "date": "2026-11-18",
    "start_time": "07:00",
    "end_time": "09:30",
    "day_header": "Thứ 2 18/11"
  }
]
```

---

## CLI Reference

| Flag | Default | Description |
| --- | --- | --- |
| `--weeks N` | `6` | Number of upcoming weeks to scan (`>= 1`) |
| `--dry-run` | `false` | Parse and log events without calling Google Calendar API |
| `--parse-html PATH` | — | Parse a local HTML file and print JSON events to stdout |
| `--version` | — | Print CLI version and exit |

---

## GitHub Actions

Add 4 repository secrets under **Settings → Secrets and variables → Actions**:

| Secret | Value |
| --- | --- |
| `STUDENT_ID` | FTU student ID |
| `STUDENT_PASS` | FTU portal password |
| `CREDENTIALS_JSON` | Full contents of `credentials.json` |
| `TOKEN_JSON` | Full contents of `token.json` |

Workflow [`.github/workflows/sync_calendar.yml`](.github/workflows/sync_calendar.yml) runs automatically at `00:00` and `11:00 UTC` daily and can be triggered manually via `workflow_dispatch`.

---

## Testing & Security

```bash
python -m unittest discover -s tests -v
```

Automated verification on every push to `main`:

| Check | Tool | Scope |
| --- | --- | --- |
| **Unit & CLI Tests** | `pytest` (`3.10`, `3.11`, `3.12`) | HTML `rowspan`/`colspan` parsing, OAuth refresh, deduplication, CLI flags |
| **SAST** | GitHub CodeQL | Static vulnerability analysis across Python source |
| **Security Lint** | `bandit` + `ruff` | HTTP timeouts, exception handling, code hygiene |
| **CVE Audit** | `pip-audit` + Dependabot | Known vulnerabilities in `requirements.txt` & GitHub Actions |

---

## License

[Apache License 2.0](./LICENSE)
