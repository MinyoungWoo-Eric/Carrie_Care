# -*- coding: utf-8 -*-
"""
공용 영속 저장소 모듈.

가족이 같은 링크로 들어와도 체크 상태가 공유되어야 하므로,
Streamlit의 session_state(브라우저 탭마다 따로 존재하는 임시 메모리)가 아니라
모든 세션이 함께 읽고 쓰는 Google Sheets 를 저장소로 사용한다.

    [아빠 폰] ─┐
    [엄마 폰] ─┼─→ Streamlit 앱 ─→ Google Sheets (공용 저장소)
    [언니 폰] ─┘

저장 구조 (워크시트 "checks", 1행은 헤더):
    date       | item_id      | checked | checked_by | updated_at
    2026-07-12 | dad_walk     | TRUE    | 아빠       | 2026-07-12 19:42
    2026-07-12 | mom_breakfast| TRUE    | 엄마       | 2026-07-12 06:31
    ...

(date, item_id) 쌍이 고유 키이며, 체크/해제 시 해당 행을 갱신(없으면 추가)한다.

Google Sheets 설정(secrets)이 없으면 로컬 JSON 파일 저장소로 자동 대체된다.
→ 로컬 개발/테스트용. Streamlit Cloud에서는 재시작 시 파일이 사라지므로
  실제 배포에서는 반드시 Google Sheets 설정을 넣어야 한다.
"""

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

KST = ZoneInfo("Asia/Seoul")

SHEET_HEADER = ["date", "item_id", "checked", "checked_by", "updated_at"]
WORKSHEET_NAME = "checks"
LOCAL_FILE = "local_checks.json"


def now_kst_str() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M")


def _to_bool(value) -> bool:
    return str(value).strip().upper() in ("TRUE", "1", "YES", "Y")


# ──────────────────────────────────────────────────────────
# Google Sheets 저장소
# ──────────────────────────────────────────────────────────
class GoogleSheetsStore:
    """gspread 기반 공용 저장소."""

    name = "Google Sheets"
    is_shared = True

    def __init__(self):
        import gspread

        creds = dict(st.secrets["gcp_service_account"])
        gc = gspread.service_account_from_dict(creds)

        sheets_cfg = st.secrets.get("sheets", {})
        url = sheets_cfg.get("spreadsheet_url", "")
        key = sheets_cfg.get("spreadsheet_key", "")
        name = sheets_cfg.get("spreadsheet_name", "carrie-care")

        if url:
            sh = gc.open_by_url(url)
        elif key:
            sh = gc.open_by_key(key)
        else:
            sh = gc.open(name)

        try:
            self.ws = sh.worksheet(WORKSHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            self.ws = sh.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=10)
            self.ws.append_row(SHEET_HEADER)

        # 시트가 비어 있으면 헤더를 넣어 둔다.
        first_row = self.ws.row_values(1)
        if not first_row:
            self.ws.append_row(SHEET_HEADER)

    def load_all(self) -> dict:
        """모든 체크 기록을 {(date, item_id): record} 형태로 반환."""
        records = {}
        for row in self.ws.get_all_records(expected_headers=SHEET_HEADER):
            key = (str(row["date"]), str(row["item_id"]))
            records[key] = {
                "checked": _to_bool(row.get("checked", "")),
                "checked_by": str(row.get("checked_by", "")),
                "updated_at": str(row.get("updated_at", "")),
            }
        return records

    def set_check(self, date_str: str, item_id: str, checked: bool, checked_by: str):
        """(date, item_id) 행을 갱신하고, 없으면 새 행을 추가한다."""
        updated_at = now_kst_str()
        new_row = [
            date_str,
            item_id,
            "TRUE" if checked else "FALSE",
            checked_by,
            updated_at,
        ]

        # 전체 값을 훑어 해당 (date, item_id) 행 번호를 찾는다.
        # 가족 규모(하루 십수 건)에서는 이 단순한 방식으로 충분하다.
        all_values = self.ws.get_all_values()
        for idx, row in enumerate(all_values[1:], start=2):  # 1행은 헤더
            if len(row) >= 2 and row[0] == date_str and row[1] == item_id:
                self.ws.update(f"A{idx}:E{idx}", [new_row])
                return
        self.ws.append_row(new_row)


# ──────────────────────────────────────────────────────────
# 로컬 JSON 저장소 (개발/테스트용 대체)
# ──────────────────────────────────────────────────────────
class LocalJSONStore:
    """secrets가 없을 때 사용하는 로컬 파일 저장소 (배포용 아님)."""

    name = "로컬 JSON 파일 (테스트용)"
    is_shared = False

    def __init__(self, path: str = LOCAL_FILE):
        self.path = path
        if not os.path.exists(self.path):
            self._write({})

    def _read(self) -> dict:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_all(self) -> dict:
        data = self._read()
        records = {}
        for flat_key, rec in data.items():
            date_str, item_id = flat_key.split("|", 1)
            records[(date_str, item_id)] = rec
        return records

    def set_check(self, date_str: str, item_id: str, checked: bool, checked_by: str):
        data = self._read()
        data[f"{date_str}|{item_id}"] = {
            "checked": checked,
            "checked_by": checked_by,
            "updated_at": now_kst_str(),
        }
        self._write(data)


# ──────────────────────────────────────────────────────────
# 저장소 선택
# ──────────────────────────────────────────────────────────
def create_store():
    """secrets에 GCP 서비스 계정이 있으면 Google Sheets, 없으면 로컬 JSON."""
    try:
        has_creds = "gcp_service_account" in st.secrets
    except Exception:
        has_creds = False

    if has_creds:
        return GoogleSheetsStore()
    return LocalJSONStore()
