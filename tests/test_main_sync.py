import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import main_sync

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_timetable.html"


class TestParseScheduleFromHtml(unittest.TestCase):
    def test_parses_regular_and_makeup_events_with_rowspan(self):
        html = FIXTURE_PATH.read_text(encoding="utf-8")
        events = main_sync.parse_schedule_from_html(html)

        self.assertEqual(len(events), 3)

        first = events[0]
        self.assertEqual(first["course"], "Kinh tế lượng")
        self.assertEqual(first["group"], "K59.1")
        self.assertEqual(first["room"], "A201")
        self.assertEqual(first["teacher"], "Nguyễn Văn A")
        self.assertFalse(first["is_makeup"])
        self.assertEqual(first["date"], "2026-11-18")
        self.assertEqual(first["start_time"], "07:00")
        self.assertEqual(first["end_time"], "09:30")

        makeup_class = events[1]
        self.assertEqual(makeup_class["course"], "Tài chính doanh nghiệp")
        self.assertTrue(makeup_class["is_makeup"])
        self.assertEqual(makeup_class["date"], "2026-11-20")
        self.assertEqual(makeup_class["start_time"], "13:30")
        self.assertEqual(makeup_class["end_time"], "16:00")

        makeup_name = events[2]
        self.assertEqual(makeup_name["course"], "Tiếng Anh chuyên ngành (Học bù)")
        self.assertTrue(makeup_name["is_makeup"])
        self.assertEqual(makeup_name["date"], "2026-11-19")
        self.assertEqual(makeup_name["start_time"], "09:45")
        self.assertEqual(makeup_name["end_time"], "11:30")

    def test_returns_empty_list_when_no_schedule_table(self):
        events = main_sync.parse_schedule_from_html("<html><body><p>Empty</p></body></html>")
        self.assertEqual(events, [])


class TestGetValidAccessToken(unittest.TestCase):
    def test_raises_when_token_file_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_token = os.path.join(tmpdir, "token.json")
            with patch.object(main_sync, "TOKEN_FILE", missing_token):
                with self.assertRaises(FileNotFoundError):
                    main_sync.get_valid_access_token()

    def test_returns_existing_valid_token(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            token_path = os.path.join(tmpdir, "token.json")
            with open(token_path, "w", encoding="utf-8") as f:
                json.dump({"access_token": "valid-tok", "refresh_token": "ref-tok"}, f)

            ok_resp = MagicMock(status_code=200)
            with patch.object(main_sync, "TOKEN_FILE", token_path), \
                 patch.object(main_sync.requests, "get", return_value=ok_resp) as mock_get:
                token = main_sync.get_valid_access_token()

            self.assertEqual(token, "valid-tok")
            mock_get.assert_called_once()

    def test_refreshes_expired_token_and_persists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            token_path = os.path.join(tmpdir, "token.json")
            creds_path = os.path.join(tmpdir, "credentials.json")
            with open(token_path, "w", encoding="utf-8") as f:
                json.dump({"access_token": "expired-tok", "refresh_token": "ref-tok"}, f)
            with open(creds_path, "w", encoding="utf-8") as f:
                json.dump({"installed": {"client_id": "cid", "client_secret": "csec"}}, f)

            expired_resp = MagicMock(status_code=401)
            refresh_resp = MagicMock(status_code=200)
            refresh_resp.json.return_value = {"access_token": "new-tok"}

            with patch.object(main_sync, "TOKEN_FILE", token_path), \
                 patch.object(main_sync, "CREDENTIALS_FILE", creds_path), \
                 patch.object(main_sync.requests, "get", return_value=expired_resp), \
                 patch.object(main_sync.requests, "post", return_value=refresh_resp):
                token = main_sync.get_valid_access_token()

            self.assertEqual(token, "new-tok")
            saved = json.loads(Path(token_path).read_text(encoding="utf-8"))
            self.assertEqual(saved["access_token"], "new-tok")


class TestSyncToGoogleCalendar(unittest.TestCase):
    def setUp(self):
        self.sample_events = [
            {
                "course": "Kinh tế lượng",
                "group": "K59.1",
                "room": "A201",
                "teacher": "Nguyễn Văn A",
                "is_makeup": False,
                "date": "2026-11-18",
                "start_time": "07:00",
                "end_time": "09:30",
                "day_header": "Thứ 2 18/11",
            },
            {
                "course": "Tài chính doanh nghiệp",
                "group": "K59.2",
                "room": "B105",
                "teacher": "Trần Thị B",
                "is_makeup": True,
                "date": "2026-11-20",
                "start_time": "13:30",
                "end_time": "16:00",
                "day_header": "Thứ 4 20/11",
            },
        ]

    def test_dry_run_skips_network_calls(self):
        with patch.object(main_sync, "get_valid_access_token") as mock_tok, \
             patch.object(main_sync.requests, "post") as mock_post:
            summary = main_sync.sync_to_google_calendar(self.sample_events, dry_run=True)

        mock_tok.assert_not_called()
        mock_post.assert_not_called()
        self.assertEqual(summary, {"added": 0, "skipped": 2, "total": 2})

    def test_deduplicates_existing_and_creates_new_with_makeup_styling(self):
        existing_resp = MagicMock(status_code=200)
        existing_resp.json.return_value = {"items": [{"summary": "Kinh tế lượng"}]}

        empty_resp = MagicMock(status_code=200)
        empty_resp.json.return_value = {"items": []}

        created_resp = MagicMock(status_code=201)

        with patch.object(main_sync, "get_valid_access_token", return_value="tok"), \
             patch.object(main_sync.requests, "get", side_effect=[existing_resp, empty_resp]), \
             patch.object(main_sync.requests, "post", return_value=created_resp) as mock_post:
            summary = main_sync.sync_to_google_calendar(self.sample_events, dry_run=False)

        self.assertEqual(summary, {"added": 1, "skipped": 1, "total": 2})
        mock_post.assert_called_once()
        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["summary"], "[HỌC BÙ] Tài chính doanh nghiệp")
        self.assertEqual(payload["colorId"], "3")
        self.assertEqual(payload["start"]["timeZone"], "Asia/Ho_Chi_Minh")
        self.assertEqual(
            [o["minutes"] for o in payload["reminders"]["overrides"]],
            [30, 120],
        )


if __name__ == "__main__":
    unittest.main()
