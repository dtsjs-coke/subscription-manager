# TRD (Technical Requirements Document)
# 구독 서비스 관리 웹페이지 v2.0

## 1. 기술 스택

| 구분 | 기술 | 용도 |
|---|---|---|
| Language | Python 3.11 | 전체 백엔드 |
| Web Framework | Streamlit | UI 렌더링 |
| 인증 | streamlit-authenticator | 세션 기반 로그인 |
| 비밀번호 해싱 | bcrypt | 패스워드 단방향 암호화 |
| 데이터 포맷 | YAML | 사용자 계정 + 구독 데이터 저장 |
| 데이터 쓰기 | GitHub Contents API | Streamlit Cloud 파일시스템 우회 |
| 알림 | Telegram Bot API | 만료 알림 발송 |
| CI/CD | GitHub Actions | 알림 스케줄러 |
| 배포 | Streamlit Cloud | 호스팅 |

---

## 2. 아키텍처 개요
```
[Streamlit Cloud - 웹 UI]
  ├─ 로그인/회원가입 (streamlit-authenticator)
  ├─ 구독 목록 조회 (GitHub API READ)
  └─ CRUD (GitHub Contents API WRITE → 저장소 커밋)
                          │
              [GitHub Repository]
          ├─ data/users.yaml        ← 사용자 계정 정보
          └─ data/subscriptions.yaml ← 사용자별 구독 데이터
                          │
              [GitHub Actions - cron KST 09:00]
                          │
              [Telegram Bot API - 사용자별 개별 발송]
```

---

## 3. 프로젝트 구조
```
subscription-manager/
├── .github/
│   └── workflows/
│       └── notify.yml
├── .streamlit/
│   └── secrets.toml            # 로컬 개발용 (gitignore)
├── data/
│   ├── users.yaml              # 사용자 계정 정보
│   └── subscriptions.yaml      # 사용자별 구독 데이터
├── src/
│   ├── github_manager.py       # GitHub Contents API 읽기/쓰기
│   ├── auth_manager.py         # 회원가입/로그인/내정보 수정
│   ├── data_manager.py         # 구독 데이터 CRUD
│   ├── notifier.py             # 텔레그램 알림
│   └── utils.py                # 공통 유틸
├── app.py                      # Streamlit 메인 앱
├── notify_check.py             # GitHub Actions 진입점
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 4. 데이터 설계

### 4.1 사용자 계정 (`data/users.yaml`)
```yaml
users:
  - id: "alice"
    password_hash: "$2b$12$..."        # bcrypt 해시
    telegram_chat_id: "123456789"      # 텔레그램 Chat ID (선택)
    telegram_username: "@alice"        # 텔레그램 @username (선택, 참고용)
    created_at: "2025-01-01"
```

- `telegram_chat_id` 우선 사용, 없으면 발송 생략
- 비밀번호는 반드시 bcrypt 해시로만 저장 (평문 저장 금지)

### 4.2 구독 데이터 (`data/subscriptions.yaml`)
```yaml
subscriptions:
  alice:                              # 사용자 id를 key로 사용
    - id: "550e8400-..."
      name: "Netflix"
      start_date: "2024-01-15"
      end_date: "2025-01-15"
      payment_date: "15"              # 결제일 (매월 N일, 또는 특정 날짜 YYYY-MM-DD)
      billing_cycle: "연간"           # 월간 / 연간 / 기타
      total_price: 190000
      monthly_price: 15833
      shared_members: 4
      url: "https://netflix.com"
      description: "패밀리 플랜"
      note: ""
      status: "active"               # active / expired / paused
      notify_sent:
        - "30d"
        - "7d"
  bob:
    - id: "..."
      name: "Spotify"
      ...
```

### 4.3 데이터 처리 규칙
- 회원가입 시 `subscriptions.yaml`에 해당 user_id key 생성 (빈 리스트)
- `payment_date`: 숫자(매월 N일) 또는 날짜 문자열 모두 허용
- `monthly_price`: billing_cycle 연간이면 `total_price / 12`, 월간이면 `total_price`
- `notify_sent`: 만료일 변경 시 초기화

---

## 5. 모듈 설계

### 5.1 `src/github_manager.py`
```
- get_file(file_path) -> (content_str, sha)
    GET /repos/{owner}/{repo}/contents/{path}
    base64 디코딩된 파일 내용과 SHA 반환

- update_file(file_path, content_str, sha, commit_message) -> bool
    PUT /repos/{owner}/{repo}/contents/{path}
    base64 인코딩 후 커밋
```

필요 시크릿: `github.token`, `github.owner`, `github.repo`

### 5.2 `src/auth_manager.py`
```
- register_user(user_id, password, telegram_chat_id) -> (bool, str)
    아이디 중복 확인
    bcrypt로 비밀번호 해싱
    users.yaml에 신규 유저 추가 (GitHub API 커밋)
    subscriptions.yaml에 해당 user_id 빈 키 생성

- login(user_id, password) -> (bool, dict)
    users.yaml 로드 후 bcrypt 검증
    성공 시 사용자 정보 반환 (비밀번호 해시 제외)

- update_user(user_id, new_password, telegram_chat_id) -> bool
    비밀번호 변경 또는 텔레그램 정보 수정
    users.yaml GitHub API 커밋
```

### 5.3 `src/data_manager.py`
```
- load_subscriptions(user_id) -> list[dict]
    subscriptions.yaml에서 해당 user_id 항목만 반환

- add_subscription(user_id, item) -> bool
- update_subscription(user_id, item_id, item) -> bool
    만료일 변경 시 notify_sent 초기화
- delete_subscription(user_id, item_id) -> bool
```

### 5.4 `src/notifier.py`
```
- send_telegram(chat_id, message) -> bool
    Bot API로 특정 chat_id에 메시지 발송

- check_and_notify()
    users.yaml 로드 → telegram_chat_id 있는 사용자만 처리
    각 사용자의 구독 항목 만료 체크 (D-30 / D-7 / D-1 / D-0)
    notify_sent 중복 방지 확인
    발송 후 notify_sent 업데이트 및 subscriptions.yaml 커밋
```

### 5.5 `src/utils.py`
```
- days_until_expiry(end_date) -> int
- calc_monthly_price(total, cycle) -> int
- get_status_badge(days) -> str   # "D-30", "D-7", "D-1", "D-Day", "만료"
- hash_password(password) -> str
- verify_password(password, hash) -> bool
```

### 5.6 `app.py` 페이지 구성
```
[미로그인 상태]
  ├─ 로그인 탭
  └─ 회원가입 탭

[로그인 상태]
  ├─ 요약 섹션 (활성 구독 수 / 월간 총액 / 연간 총액)
  ├─ 구독 테이블 (만료 임박 하이라이트)
  ├─ 구독 추가 / 수정 / 삭제 폼
  ├─ 내 정보 수정 (비밀번호 / 텔레그램 Chat ID)
  └─ 로그아웃 버튼

세션 관리: st.session_state["user_id"] 로 로그인 상태 유지
캐싱: st.cache_data(ttl=60), CRUD 후 st.cache_data.clear()
```

---

## 6. 인증 흐름
```
[회원가입]
입력(id, pw, telegram_chat_id)
  → 중복 확인
  → bcrypt 해싱
  → users.yaml 커밋 (GitHub API)
  → subscriptions.yaml에 빈 키 생성 커밋
  → 자동 로그인

[로그인]
입력(id, pw)
  → users.yaml 로드
  → bcrypt.checkpw() 검증
  → 성공: st.session_state["user_id"] = id
  → 실패: 에러 메시지

[로그아웃]
  → st.session_state 초기화
  → 로그인 화면으로 이동
```

---

## 7. GitHub Contents API

### 파일 읽기 (GET)
```
GET https://api.github.com/repos/{owner}/{repo}/contents/{path}
Headers: Authorization: Bearer {token}
Response: content(base64), sha
```

### 파일 쓰기 (PUT)
```
PUT https://api.github.com/repos/{owner}/{repo}/contents/{path}
Body: { message, content(base64), sha }
```

주의사항:
- SHA 불일치 시 422 에러 → 항상 최신 SHA 사용
- 동시 쓰기 경합 가능성 있음 (소규모 사용에서는 무시 가능)
- GitHub Actions 기본 `GITHUB_TOKEN`은 쓰기 제한 → 별도 PAT (`GH_PAT`) 필요

---

## 8. 텔레그램 알림

### 알림 조건

| 조건 | notify_sent 키 |
|---|---|
| D-30 | "30d" |
| D-7 | "7d" |
| D-1 | "1d" |
| D-0 | "0d" |

### 메시지 포맷
```
🔔 구독 만료 알림

📦 서비스: Netflix
📅 만료일: 2025-01-15 (D-7)
💳 결제일: 매월 15일
💰 총 가격: 190,000원
📆 월 환산: 15,833원
```

### GitHub Actions (`notify.yml`)
```yaml
name: Subscription Notify
on:
  schedule:
    - cron: '0 0 * * *'    # KST 09:00
  workflow_dispatch:
jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python notify_check.py
        env:
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          GH_PAT: ${{ secrets.GH_PAT }}
          GH_OWNER: ${{ secrets.GH_OWNER }}
          GH_REPO: ${{ secrets.GH_REPO }}
```

---

## 9. 시크릿 관리

### `.streamlit/secrets.toml` (로컬, gitignore)
```toml
[telegram]
token = "YOUR_BOT_TOKEN"

[github]
token = "YOUR_PAT"
owner = "YOUR_USERNAME"
repo = "subscription-manager"
```

### Streamlit Cloud Secrets
위와 동일 내용을 App Settings > Secrets에 등록

### GitHub Actions Secrets
| 이름 | 내용 |
|---|---|
| TELEGRAM_TOKEN | 텔레그램 Bot Token |
| GH_PAT | GitHub Personal Access Token (repo 스코프) |
| GH_OWNER | GitHub 사용자명 |
| GH_REPO | 저장소 이름 |

---

## 10. 의존성 (`requirements.txt`)
```
streamlit>=1.32.0
pyyaml>=6.0
requests>=2.31.0
pandas>=2.0.0
bcrypt>=4.0.0
```

---

## 11. 배포 절차
1. GitHub 저장소 생성 및 코드 push
2. `data/users.yaml`, `data/subscriptions.yaml` 초기 파일 커밋
3. GitHub PAT 발급 (repo 스코프)
4. GitHub Actions Secrets 등록 (9장 참고)
5. Streamlit Cloud에서 저장소 연결, 메인 파일 `app.py` 지정
6. Streamlit Cloud Secrets 등록 (9장 참고)
7. `workflow_dispatch`로 알림 수동 실행 테스트