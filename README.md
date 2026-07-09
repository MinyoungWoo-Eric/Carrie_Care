# 🐶 캐리 케어 매뉴얼 / 가족 체크리스트

가족(아빠 👨 · 엄마 👩 · 언니 👧)이 **같은 링크 하나로** 들어와서
2026년 7월 12일 ~ 7월 31일 동안 캐리의 케어 체크리스트를 함께 쓰는 Streamlit 앱입니다.

- ✅ 누가 체크하든 **모든 가족에게 똑같이 보입니다** (Google Sheets 공용 저장소)
- 📅 날짜 선택 / 오늘 바로가기
- 👨‍👩‍👧 역할별 담당 체크리스트 + "모두에게" 공통 항목
- 🕐 체크한 사람과 마지막 수정 시간 표시
- 📊 기간 전체 날짜별 체크 현황
- 📖 원문 케어 매뉴얼 전문을 앱 안에서 열람
- 📱 모바일 화면에 맞춘 레이아웃, 한국어 UI

---

## 📁 폴더 구조

```
carrie-care/
├── app.py                        # 메인 앱 (UI 전체)
├── core/
│   ├── content.py                # 체크리스트 항목 정의 + 매뉴얼 원문 전문
│   └── storage.py                # Google Sheets 공용 저장소 (없으면 로컬 JSON 대체)
├── requirements.txt              # 파이썬 패키지 목록
├── README.md                     # 이 문서
├── .gitignore                    # secrets 등 업로드 제외 목록
└── .streamlit/
    ├── config.toml               # 앱 테마 설정
    └── secrets.toml.example      # 비밀키 작성 예시 (실제 키는 secrets.toml에)
```

### 각 파일이 하는 일

| 파일 | 설명 |
|---|---|
| `app.py` | 화면 전체. 사용자 선택 → 날짜 선택 → 4개 탭(체크리스트/현황/역할/매뉴얼) |
| `core/content.py` | 체크 항목과 매뉴얼 텍스트. **내용을 바꾸고 싶으면 이 파일만 수정**하면 됩니다 |
| `core/storage.py` | 체크 상태를 Google Sheets에 읽고 쓰는 부분 |
| `.streamlit/secrets.toml` | Google 서비스 계정 키 (직접 만들어야 하며, GitHub에 올리지 않음) |

> 체크리스트/매뉴얼을 DB가 아닌 파이썬 파일(`content.py`)로 관리하는 이유:
> 내용이 자주 바뀌지 않고 양이 적어서, GitHub에서 수정 → 자동 재배포가 가장 간단하고
> 변경 이력도 커밋으로 남기 때문입니다. **체크 "상태"만** Google Sheets에 저장합니다.

---

## 1️⃣ Google Sheets 저장소 준비 (최초 1회, 약 10분)

가족이 체크 상태를 공유하려면 공용 저장소가 필요합니다. 순서대로 따라 하세요.

### ① 구글 스프레드시트 만들기
1. https://sheets.google.com 에서 새 스프레드시트 생성
2. 이름은 아무거나 (예: `carrie-care`)
3. 주소창의 URL을 복사해 두기 (나중에 secrets에 넣음)

### ② Google Cloud 서비스 계정 만들기
1. https://console.cloud.google.com 접속 → 새 프로젝트 생성 (이름 예: `carrie-care`)
2. 왼쪽 메뉴 **API 및 서비스 → 라이브러리**에서 아래 2개를 검색해 **사용 설정**
   - **Google Sheets API**
   - **Google Drive API**
3. **API 및 서비스 → 사용자 인증 정보 → 사용자 인증 정보 만들기 → 서비스 계정**
   - 이름 예: `carrie-care` → 만들기 (역할은 건너뛰어도 됨)
4. 만든 서비스 계정 클릭 → **키** 탭 → **키 추가 → 새 키 만들기 → JSON**
   - JSON 파일이 다운로드됩니다. **이 파일이 비밀키**입니다.

### ③ 시트를 서비스 계정과 공유하기 (가장 자주 빼먹는 단계!)
1. 다운로드한 JSON 안의 `client_email` 값 복사
   (예: `carrie-care@프로젝트ID.iam.gserviceaccount.com`)
2. ①에서 만든 스프레드시트 → 우측 상단 **공유** → 이 이메일을 **편집자**로 추가

### ④ secrets 작성
`.streamlit/secrets.toml.example` 을 복사해 `.streamlit/secrets.toml` 을 만들고,
JSON 파일의 값들을 그대로 옮겨 적은 뒤 `[sheets]` 의 `spreadsheet_url` 에 시트 주소를 넣습니다.

> `checks` 워크시트와 헤더는 앱이 처음 실행될 때 자동으로 만들어 줍니다.

---

## 💡 확장 아이디어

- 체크 항목 추가/수정: `core/content.py` 의 `CHECKLIST_ITEMS` 만 고치면 됩니다
  (`id` 는 기존과 겹치지 않게, `days` 로 특정 요일만 표시 가능)
- 기간 변경: `core/content.py` 의 `START_DATE`, `END_DATE`
- 사진 기록, 메모란, 주간 통계 그래프 등도 같은 시트 구조에 열을 추가해 확장 가능
