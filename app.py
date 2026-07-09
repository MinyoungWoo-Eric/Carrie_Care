# -*- coding: utf-8 -*-
"""
🐶 캐리 케어 매뉴얼 / 가족 체크리스트 앱 (메인 파일)

실행:  streamlit run app.py
"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

from content import (
    START_DATE,
    END_DATE,
    ROLES,
    ROLE_DETAILS,
    WEEKDAY_KO,
    MANUAL_TEXT,
    items_for_date,
    items_by_role,
)
from storage import create_store

KST = ZoneInfo("Asia/Seoul")

# ──────────────────────────────────────────────────────────
# 기본 설정
# ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="캐리 케어 체크리스트",
    page_icon="🐶",
    layout="centered",  # 모바일에서 보기 좋은 좁은 레이아웃
    initial_sidebar_state="collapsed",
)

# 모바일 가독성을 위한 소소한 스타일 조정
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; padding-bottom: 3rem; }
      div[data-testid="stCheckbox"] label p { font-size: 1.02rem; }
      .role-header { font-size: 1.15rem; font-weight: 700; margin: 0.2rem 0 0.1rem 0; }
      .check-meta { color: #7a736a; font-size: 0.82rem; margin: -0.35rem 0 0.4rem 1.9rem; }
      .item-note { color: #8a8378; font-size: 0.8rem; margin: -0.45rem 0 0.5rem 1.9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ──────────────────────────────────────────────────────────
# 저장소 초기화 (모든 세션이 공유하는 Google Sheets)
# ──────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="저장소에 연결하는 중...")
def get_store():
    return create_store()


@st.cache_data(ttl=10, show_spinner=False)
def load_all_checks(_store, version: int) -> dict:
    """체크 기록 전체를 읽는다.
    - ttl=10초: 다른 가족이 체크한 내용도 최대 10초 안에 반영
    - version: 내가 체크하면 즉시 캐시를 무효화하기 위한 값
    """
    return _store.load_all()


try:
    store = get_store()
except Exception as e:
    st.error(
        "저장소(Google Sheets) 연결에 실패했어요. "
        "README의 설정 방법을 확인해 주세요.\n\n"
        f"오류: {e}"
    )
    st.stop()

if "data_version" not in st.session_state:
    st.session_state.data_version = 0


def bump_version():
    st.session_state.data_version += 1


# ──────────────────────────────────────────────────────────
# 상단: 제목 · 사용자 선택 · 날짜 선택
# ──────────────────────────────────────────────────────────
st.title("🐶 캐리 케어 체크리스트")
st.caption("2026년 7월 12일 ~ 7월 31일 · 가족 모두가 함께 쓰는 체크리스트")

if not store.is_shared:
    st.warning(
        "지금은 **로컬 테스트 모드**(JSON 파일)로 실행 중이에요. "
        "가족과 체크 상태를 공유하려면 README를 보고 Google Sheets를 연결해 주세요.",
        icon="⚠️",
    )

user = st.selectbox(
    "🙋 나는 누구인가요?",
    options=[role for role, _ in ROLES if role != "모두에게"],
    index=None,
    placeholder="이름(역할)을 선택해 주세요",
    key="user",
)

today = datetime.now(KST).date()
# 기간 밖이면 가장 가까운 날짜를 기본값으로
default_date = min(max(today, START_DATE), END_DATE)

if "selected_date" not in st.session_state:
    st.session_state.selected_date = default_date


def goto_today():
    """'오늘로' 버튼 콜백 — 위젯 생성 전에 실행되므로 안전하게 값 변경 가능."""
    st.session_state.selected_date = default_date


col_date, col_today = st.columns([3, 1])
with col_date:
    selected_date = st.date_input(
        "📅 날짜 선택",
        min_value=START_DATE,
        max_value=END_DATE,
        format="YYYY-MM-DD",
        key="selected_date",
    )
with col_today:
    st.write("")  # 버튼 높이 맞춤
    st.button("오늘로", use_container_width=True, on_click=goto_today)

date_str = selected_date.strftime("%Y-%m-%d")
weekday_label = WEEKDAY_KO[selected_date.weekday()]
is_today = selected_date == today

# 체크 기록 읽기
records = load_all_checks(store, st.session_state.data_version)
day_items = items_for_date(selected_date)
grouped = items_by_role(day_items)

done_count = sum(
    1 for item in day_items if records.get((date_str, item["id"]), {}).get("checked")
)
total_count = len(day_items)

st.subheader(
    f"{selected_date.month}월 {selected_date.day}일 ({weekday_label})"
    + (" · 오늘" if is_today else "")
)
st.progress(
    done_count / total_count if total_count else 0.0,
    text=f"완료 {done_count} / {total_count}",
)

if st.button("🔄 새로고침 (다른 가족의 체크 반영)", use_container_width=True):
    bump_version()
    st.rerun()

# ──────────────────────────────────────────────────────────
# 탭 구성
# ──────────────────────────────────────────────────────────
tab_check, tab_status, tab_roles, tab_manual = st.tabs(
    ["✅ 체크리스트", "📊 날짜별 현황", "👨‍👩‍👧 역할 안내", "📖 전체 매뉴얼"]
)


# ── 탭 1: 체크리스트 ─────────────────────────────────────
def on_toggle(item_id: str, d_str: str):
    """체크박스가 바뀌면 즉시 공용 저장소에 기록."""
    key = f"chk_{d_str}_{item_id}"
    checked = st.session_state.get(key, False)
    who = st.session_state.get("user") or "가족"
    try:
        store.set_check(d_str, item_id, checked, who)
    except Exception as e:
        st.session_state["_save_error"] = str(e)
    bump_version()


with tab_check:
    if user is None:
        st.info("먼저 위에서 **이름(역할)** 을 선택하면 체크할 수 있어요. 👆", icon="🙋")

    if st.session_state.pop("_save_error", None):
        st.error("저장 중 오류가 발생했어요. 새로고침 후 다시 시도해 주세요.")

    for role, icon in ROLES:
        items = grouped.get(role, [])
        if not items:
            continue
        st.markdown(f'<p class="role-header">{icon} {role}</p>', unsafe_allow_html=True)
        for item in items:
            rec = records.get((date_str, item["id"]), {})
            checked = bool(rec.get("checked", False))
            key = f"chk_{date_str}_{item['id']}"

            st.checkbox(
                item["label"],
                value=checked,
                key=key,
                disabled=(user is None),
                on_change=on_toggle,
                args=(item["id"], date_str),
            )
            if item.get("note"):
                st.markdown(
                    f'<p class="item-note">💡 {item["note"]}</p>',
                    unsafe_allow_html=True,
                )
            if checked and rec.get("checked_by"):
                st.markdown(
                    f'<p class="check-meta">✔ {rec["checked_by"]} · {rec.get("updated_at", "")}</p>',
                    unsafe_allow_html=True,
                )
        st.divider()

    st.caption(
        "체크하면 자동으로 저장되고, 가족 누구나 같은 링크로 들어오면 "
        "동일한 체크 상태를 볼 수 있어요. (다른 가족의 체크는 새로고침 시 반영)"
    )


# ── 탭 2: 날짜별 현황 ────────────────────────────────────
with tab_status:
    st.markdown("#### 📊 기간 전체 체크 현황")
    st.caption("날짜를 눌러 그날의 세부 체크 내역을 볼 수 있어요.")

    d = START_DATE
    while d <= END_DATE:
        d_str = d.strftime("%Y-%m-%d")
        d_items = items_for_date(d)
        d_total = len(d_items)
        d_done = sum(
            1 for item in d_items if records.get((d_str, item["id"]), {}).get("checked")
        )
        pct = d_done / d_total if d_total else 0.0

        if d_done == d_total and d_total > 0:
            badge = "🌕 완료!"
        elif d_done > 0:
            badge = "🌗 진행 중"
        elif d < today:
            badge = "🌑 미기록"
        else:
            badge = "⬜ 예정"

        label = (
            f"{d.month}/{d.day} ({WEEKDAY_KO[d.weekday()]})"
            + (" · 오늘" if d == today else "")
            + f" — {d_done}/{d_total} {badge}"
        )
        with st.expander(label, expanded=(d == selected_date)):
            st.progress(pct)
            for item in d_items:
                rec = records.get((d_str, item["id"]), {})
                if rec.get("checked"):
                    st.markdown(
                        f"- ✅ **{item['label']}** — {rec.get('checked_by','')} · {rec.get('updated_at','')}"
                    )
                else:
                    st.markdown(f"- ⬜ {item['label']} · _{item['role']}_")
        d += timedelta(days=1)


# ── 탭 3: 역할 안내 ──────────────────────────────────────
with tab_roles:
    st.markdown("#### 👨‍👩‍👧 역할 분담 한눈에 보기")
    for role, icon in ROLES:
        with st.container(border=True):
            st.markdown(f"**{icon} {role}**")
            for line in ROLE_DETAILS[role]:
                st.markdown(f"- {line}")
    st.info(
        "매일 공통 케어: **거즈 양치 · 무조건 산책 · 발 소독 · "
        "화식 먹고 입 주변 지저분하면 수건에 간식 넣어 자연스럽게 닦아주기**",
        icon="🩺",
    )
    st.error(
        "🚨 조금이라도 이상하면 혼자 고민하지 말고 **바로 유진이에게 연락하기!** "
        "(자세한 응급 기준은 '전체 매뉴얼' 탭 맨 아래)",
        icon="📞",
    )


# ── 탭 4: 전체 매뉴얼 (원문 그대로) ──────────────────────
with tab_manual:
    st.markdown("#### 📖 캐리 케어 매뉴얼 원문 전체")
    st.caption("원문을 한 줄도 빠짐없이 그대로 담았어요.")
    st.text(MANUAL_TEXT)
