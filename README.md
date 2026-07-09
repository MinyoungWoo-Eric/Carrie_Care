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

## 2️⃣ 로컬 실행 방법

```bash
# 1. 코드 받기
git clone https://github.com/<내계정>/carrie-care.git
cd carrie-care

# 2. (선택) 가상환경
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. 패키지 설치
pip install -r requirements.txt

# 4. 실행
streamlit run app.py
```

브라우저에서 http://localhost:8501 이 열립니다.

> 💡 `secrets.toml` 없이 실행하면 **로컬 테스트 모드**(JSON 파일 저장)로 동작합니다.
> 화면 구성만 확인할 때 편리하지만, 이 모드는 가족 간 공유가 되지 않습니다.

---

## 3️⃣ 배포 방법 (GitHub + Streamlit Community Cloud, 무료)

1. 이 폴더 전체를 GitHub 저장소에 올립니다.
   ```bash
   git init
   git add .
   git commit -m "캐리 케어 체크리스트"
   git branch -M main
   git remote add origin https://github.com/<내계정>/carrie-care.git
   git push -u origin main
   ```
   (`.gitignore` 덕분에 `secrets.toml` 은 자동으로 제외됩니다)

2. https://share.streamlit.io 접속 → GitHub 계정으로 로그인
3. **Create app** → 저장소 `carrie-care`, 브랜치 `main`, 메인 파일 `app.py` 선택
4. **Advanced settings → Secrets** 칸에 로컬 `secrets.toml` 내용을 **그대로 붙여넣기**
5. **Deploy** 클릭 → 잠시 후 `https://xxxx.streamlit.app` 링크가 생깁니다
6. 이 링크를 가족 카톡방에 공유하면 끝! 🎉

### 배포 후 사용 방법
- 각자 링크로 접속 → 상단에서 **내 이름(아빠/엄마/언니)** 선택
- 오늘 날짜의 체크리스트에서 완료한 항목 체크 → 자동 저장
- 다른 가족이 체크한 내용은 **🔄 새로고침** 버튼(또는 페이지 새로고침)으로 반영
- 체크 현황은 스프레드시트에서도 직접 볼 수 있습니다

---

## ⚠️ 주의사항

- **`secrets.toml` 은 절대 GitHub에 올리지 마세요.** 서비스 계정 키가 노출되면
  누구나 시트에 접근할 수 있습니다. (실수로 올렸다면 Google Cloud에서 키를 삭제 후 재발급)
- Streamlit Cloud 무료 앱은 한동안 접속이 없으면 잠들 수 있습니다.
  다시 접속하면 자동으로 깨어나며, **데이터는 시트에 있으므로 사라지지 않습니다.**
- 동시에 같은 항목을 체크하는 극단적인 경우 마지막 저장이 남습니다(가족 규모에선 문제 없음).
- 스프레드시트의 `checks` 시트를 직접 수정해도 앱에 반영됩니다.
  (열 순서: date, item_id, checked, checked_by, updated_at)

## 💡 확장 아이디어

- 체크 항목 추가/수정: `core/content.py` 의 `CHECKLIST_ITEMS` 만 고치면 됩니다
  (`id` 는 기존과 겹치지 않게, `days` 로 특정 요일만 표시 가능)
- 기간 변경: `core/content.py` 의 `START_DATE`, `END_DATE`
- 사진 기록, 메모란, 주간 통계 그래프 등도 같은 시트 구조에 열을 추가해 확장 가능
- 알림 기능이 나중에 필요해지면 `storage.set_check()` 호출 직후에
  발송 로직을 한 군데만 끼워 넣으면 되는 구조입니다 (현재 프로젝트에서는 미사용)
