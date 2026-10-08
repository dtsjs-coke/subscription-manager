# subscription-manager
subscription-manager

## Butler API 토큰 설정

이 앱은 Butler API(S9 서버)를 `X-Butler-Token` 헤더로 호출합니다. 토큰 값은 저장소에 두지 않습니다(기본값도 없음).

- Streamlit Cloud: App settings > Secrets 에 `BUTLER_API_TOKEN` 등록
- GitHub Actions: Settings > Secrets and variables > Actions 에 `BUTLER_API_TOKEN` 등록
- 로컬 실행: `.streamlit/secrets.toml`(gitignore 됨) 또는 환경변수 `BUTLER_API_TOKEN`

`src/config.py` 는 S9 의 tunnel_manager 가 터널 URL 이 바뀔 때마다 자동으로 덮어쓰므로 URL 한 줄(`BUTLER_API_URL`)만 둡니다.
