"""GitHub Actions에서 실행되는 알림 체크 스크립트"""
import sys
import os

# Streamlit 없이 실행 시 secrets 대신 환경변수 사용
# github_manager, notifier 내부에서 os.environ fallback 처리됨

sys.path.insert(0, os.path.dirname(__file__))

from src.notifier import check_and_notify

if __name__ == "__main__":
    print("🔍 구독 만료 알림 체크 시작...")
    check_and_notify()
    print("✅ 완료")