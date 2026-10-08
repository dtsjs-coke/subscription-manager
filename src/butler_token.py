"""Butler API 토큰 조회 헬퍼.

토큰은 코드/저장소에 두지 않는다 (기본값 없음).
조회 순서: 환경변수 BUTLER_API_TOKEN (GitHub Actions) -> st.secrets (Streamlit Cloud).
둘 다 없으면 빈 문자열을 돌려주며, 호출하는 쪽이 요청을 보내지 않고 오류를 보여 줘야 한다.
"""
import os

TOKEN_MISSING_MESSAGE = (
    "BUTLER_API_TOKEN 이 설정되지 않았습니다. "
    "Streamlit Cloud Secrets 또는 GitHub Actions Secrets 에 등록해 주세요."
)


def get_butler_token() -> str:
    token = os.environ.get("BUTLER_API_TOKEN", "")
    if token and token.strip():
        return token.strip()
    try:
        import streamlit as st
        token = st.secrets.get("BUTLER_API_TOKEN", "")
        if token and str(token).strip():
            return str(token).strip()
    except Exception:
        pass
    return ""
