# TASK.md
# 구독 서비스 관리 웹페이지 v2.0

## 진행 상태
- `[ ]` 미시작  `[~]` 진행 중  `[x]` 완료

---

## Phase 1. 프로젝트 초기 설정

- [ ] **T-01** GitHub 저장소 생성
- [ ] **T-02** 로컬 개발환경 세팅 (PyCharm, Python 3.11, venv)
- [ ] **T-03** `requirements.txt` 작성 (streamlit, pyyaml, requests, pandas, bcrypt)
- [ ] **T-04** 프로젝트 디렉토리 구조 생성
- [ ] **T-05** `.gitignore` 작성 (secrets.toml, .env, __pycache__ 등)
- [ ] **T-06** `.streamlit/secrets.toml` 로컬 시크릿 파일 생성

---

## Phase 2. 초기 데이터 파일 생성

- [ ] **T-07** `data/users.yaml` 초기 파일 생성
  - [ ] 스키마 정의 (id, password_hash, telegram_chat_id, telegram_username, created_at)
  - [ ] 빈 users 리스트로 초기화 후 GitHub 커밋
- [ ] **T-08** `data/subscriptions.yaml` 초기 파일 생성
  - [ ] 스키마 정의 (user_id를 key로 하는 딕셔너리 구조)
  - [ ] 빈 subscriptions 딕셔너리로 초기화 후 GitHub 커밋

---

## Phase 3. GitHub API 레이어 구현

- [ ] **T-09** GitHub Personal Access Token 발급 (repo 스코프)
- [ ] **T-10** `src/github_manager.py` 구현
  - [ ] `get_file(file_path)` → content_str, sha 반환
  - [ ] `update_file(file_path, content_str, sha, commit_message)` → bool 반환
  - [ ] 시크릿에서 token, owner, repo 로드 로직
  - [ ] 에러 핸들링 (422 SHA 불일치, 네트워크 오류 등)
- [ ] **T-11** GitHub API 동작 단위 테스트 (로컬)

---

## Phase 4. 인증 모듈 구현

- [ ] **T-12** `src/utils.py` 구현
  - [ ] `hash_password(password)` - bcrypt 해싱
  - [ ] `verify_password(password, hash)` - bcrypt 검증
  - [ ] `days_until_expiry(end_date)` - 만료까지 남은 일수
  - [ ] `calc_monthly_price(total, cycle)` - 월 환산 가격
  - [ ] `get_status_badge(days)` - D-day 뱃지 텍스트
- [ ] **T-13** `src/auth_manager.py` 구현
  - [ ] `register_user(user_id, password, telegram_chat_id)` 구현
    - [ ] users.yaml 중복 확인
    - [ ] bcrypt 해싱
    - [ ] users.yaml GitHub 커밋
    - [ ] subscriptions.yaml에 빈 키 생성 커밋
  - [ ] `login(user_id, password)` 구현
  - [ ] `update_user(user_id, new_password, telegram_chat_id)` 구현
- [ ] **T-14** 인증 로직 로컬 테스트

---

## Phase 5. 구독 데이터 모듈 구현

- [ ] **T-15** `src/data_manager.py` 구현
  - [ ] `load_subscriptions(user_id)` - 해당 유저 구독 목록 반환
  - [ ] `add_subscription(user_id, item)` - UUID 자동 생성 포함
  - [ ] `update_subscription(user_id, item_id, item)` - 만료일 변경 시 notify_sent 초기화
  - [ ] `delete_subscription(user_id, item_id)`
- [ ] **T-16** 구독 CRUD 로컬 테스트

---

## Phase 6. Streamlit UI 구현

- [ ] **T-17** `app.py` 세션 관리 구조 구현
  - [ ] `st.session_state["user_id"]` 기반 로그인 상태 관리
  - [ ] 미로그인 시 로그인/회원가입 화면, 로그인 시 메인 화면 분기
- [ ] **T-18** 로그인 / 회원가입 UI 구현
  - [ ] 탭으로 로그인 / 회원가입 구분
  - [ ] 회원가입: 아이디, 비밀번호, 텔레그램 Chat ID 입력 + 안내 문구
  - [ ] 로그인: 아이디, 비밀번호 입력
  - [ ] 에러 메시지 처리 (중복 아이디, 비밀번호 불일치 등)
- [ ] **T-19** 메인 페이지 구현
  - [ ] 요약 섹션 (활성 구독 수, 월간 총액, 연간 총액)
  - [ ] 구독 테이블 (st.dataframe + 만료 임박 하이라이트)
  - [ ] 결제일 컬럼 포함 확인
  - [ ] 관련 링크 클릭 가능 처리
  - [ ] `st.cache_data(ttl=60)` 적용
- [ ] **T-20** 구독 추가 폼 구현
  - [ ] 서비스명, 시작일, 만료일, 결제일, 구독기간, 총 가격, 공유 인원, URL, 설명, 비고
  - [ ] 월 환산 가격 자동 계산 표시
  - [ ] 저장 시 GitHub 커밋 + 캐시 무효화
- [ ] **T-21** 구독 수정 폼 구현
  - [ ] 항목 선택 → 기존 값 pre-fill → 수정 저장
  - [ ] 만료일 변경 시 notify_sent 초기화 안내
- [ ] **T-22** 구독 삭제 구현
  - [ ] 삭제 확인 다이얼로그
- [ ] **T-23** 내 정보 수정 페이지 구현
  - [ ] 현재 텔레그램 Chat ID 표시 및 수정
  - [ ] 비밀번호 변경 (현재 비밀번호 확인 후 변경)
  - [ ] Chat ID 확인 방법 안내 (BotFather 링크)
- [ ] **T-24** 로그아웃 버튼 구현

---

## Phase 7. 텔레그램 알림 구현

- [ ] **T-25** 텔레그램 Bot 생성 및 Token 발급 (BotFather)
- [ ] **T-26** Chat ID 확인 방법 테스트
- [ ] **T-27** `src/notifier.py` 구현
  - [ ] `send_telegram(chat_id, message)` 구현
  - [ ] `check_and_notify()` 구현
    - [ ] users.yaml 전체 로드
    - [ ] telegram_chat_id 있는 사용자만 처리
    - [ ] 각 사용자 구독 항목 D-30/7/1/0 체크
    - [ ] notify_sent 중복 방지
    - [ ] 발송 후 subscriptions.yaml 커밋 (결제일 포함 메시지)
- [ ] **T-28** `notify_check.py` 진입점 스크립트 작성
- [ ] **T-29** 로컬 환경에서 텔레그램 알림 테스트

---

## Phase 8. GitHub Actions 스케줄러 설정

- [ ] **T-30** `.github/workflows/notify.yml` 작성
  - [ ] cron: `0 0 * * *` (KST 09:00)
  - [ ] workflow_dispatch 추가
  - [ ] 환경변수: TELEGRAM_TOKEN, GH_PAT, GH_OWNER, GH_REPO
- [ ] **T-31** GitHub Actions Secrets 등록
  - [ ] TELEGRAM_TOKEN
  - [ ] GH_PAT
  - [ ] GH_OWNER
  - [ ] GH_REPO
- [ ] **T-32** workflow_dispatch로 수동 실행 테스트

---

## Phase 9. 배포

- [ ] **T-33** Streamlit Cloud 저장소 연결 (메인 파일: app.py)
- [ ] **T-34** Streamlit Cloud Secrets 등록 (telegram.token, github.token/owner/repo)
- [ ] **T-35** 배포 후 전체 동작 확인
  - [ ] 회원가입 → 로그인 → 구독 추가 → GitHub 커밋 확인
  - [ ] 텔레그램 알림 수동 트리거 테스트

---

## Phase 10. 마무리

- [ ] **T-36** `README.md` 작성
  - [ ] 프로젝트 소개 및 기능 목록
  - [ ] 로컬 실행 방법
  - [ ] Streamlit Cloud 배포 방법
  - [ ] 텔레그램 Bot 설정 방법 (Chat ID 확인 포함)
  - [ ] GitHub PAT 발급 방법
- [ ] **T-37** 전체 QA
  - [ ] 멀티유저 시나리오 (사용자 A, B 각각 가입 후 데이터 격리 확인)
  - [ ] 비밀번호 변경 후 재로그인 확인
  - [ ] 알림 중복 발송 방지 확인
  - [ ] 앱 재배포 후 데이터 유지 확인

---

## 참고 링크

| 항목 | URL |
|---|---|
| Telegram BotFather | https://t.me/BotFather |
| Chat ID 확인 | https://api.telegram.org/bot{TOKEN}/getUpdates |
| Streamlit Cloud | https://share.streamlit.io |
| Streamlit Secrets 문서 | https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management |
| GitHub PAT 발급 | https://github.com/settings/tokens |
| bcrypt 문서 | https://pypi.org/project/bcrypt |