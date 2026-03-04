import base64
import requests
import streamlit as st
import os


def _get_secret(secrets_section: str, secrets_key: str, env_key: str) -> str:
    """Streamlit Secrets 우선, 없으면 환경변수 fallback"""
    try:
        return st.secrets[secrets_section][secrets_key]
    except Exception:
        return os.environ.get(env_key, "")


def _get_headers():
    token = _get_secret("github", "token", "GH_PAT")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_repo_info():
    owner = _get_secret("github", "owner", "GH_OWNER")
    repo = _get_secret("github", "repo", "GH_REPO")
    return owner, repo


def get_file(file_path: str) -> tuple[str, str]:
    """GitHub에서 파일 내용과 SHA 반환"""
    owner, repo = _get_repo_info()
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    resp = requests.get(url, headers=_get_headers())
    resp.raise_for_status()
    data = resp.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


def update_file(file_path: str, content_str: str, sha: str, commit_message: str) -> bool:
    """GitHub에 파일 내용 커밋"""
    owner, repo = _get_repo_info()
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    encoded = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
    payload = {
        "message": commit_message,
        "content": encoded,
        "sha": sha,
    }
    resp = requests.put(url, headers=_get_headers(), json=payload)
    return resp.status_code in (200, 201)