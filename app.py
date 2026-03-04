import streamlit as st
import pandas as pd
from datetime import date, datetime

from src.auth_manager import register_user, login, update_user, get_user
from src.data_manager import (
    load_subscriptions,
    add_subscription,
    update_subscription,
    delete_subscription,
)
from src.utils import days_until_expiry, calc_monthly_price, get_status_badge, format_price
from src.notifier import send_welcome

st.set_page_config(page_title="구독 관리", page_icon="📋", layout="wide")

# ── 세션 초기화 ──────────────────────────────────────────────
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "edit_item_id" not in st.session_state:
    st.session_state.edit_item_id = None
if "delete_item_id" not in st.session_state:
    st.session_state.delete_item_id = None


# ── 데이터 로드 (캐싱) ────────────────────────────────────────
@st.cache_data(ttl=60)
def cached_load(user_id: str):
    return load_subscriptions(user_id)


def refresh():
    st.cache_data.clear()
    st.rerun()


# ── 로그인/회원가입 화면 ──────────────────────────────────────
def show_auth_page():
    st.title("📋 구독 관리 서비스")
    st.markdown("---")
    tab_login, tab_register = st.tabs(["🔐 로그인", "✏️ 회원가입"])

    with tab_login:
        st.subheader("로그인")
        uid = st.text_input("아이디", key="login_id")
        pw = st.text_input("비밀번호", type="password", key="login_pw")
        if st.button("로그인", use_container_width=True, type="primary"):
            if not uid or not pw:
                st.error("아이디와 비밀번호를 입력해주세요.")
            else:
                ok, user_info = login(uid, pw)
                if ok:
                    st.session_state.user_id = uid
                    st.success("로그인 성공!")
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    with tab_register:
        st.subheader("회원가입")
        new_id = st.text_input("아이디 (영문/숫자)", key="reg_id")
        new_pw = st.text_input("비밀번호(생년월일 등 유출돼도 괜찮은걸로 입력하세요. 책임안짐)", type="password", key="reg_pw")
        new_pw2 = st.text_input("비밀번호 확인", type="password", key="reg_pw2")
        new_tg = st.text_input(
            "텔레그램 Chat ID (선택)",
            key="reg_tg",
            help="텔레그램 알림 수신을 원하시면 Chat ID를 입력하세요.\n"
                 "Chat ID 확인 방법: @userinfobot 에게 /start 메시지를 보내면 확인 가능합니다.",
        )
        st.caption("💡 Chat ID 확인: 텔레그램에서 [@userinfobot](https://t.me/userinfobot) 에게 /start 를 보내세요.")

        if st.button("회원가입", use_container_width=True, type="primary"):
            if not new_id or not new_pw:
                st.error("아이디와 비밀번호를 입력해주세요.")
            elif new_pw != new_pw2:
                st.error("비밀번호가 일치하지 않습니다.")
            elif len(new_pw) < 4:
                st.error("비밀번호는 4자 이상이어야 합니다.")
            else:
                ok, msg = register_user(new_id, new_pw, new_tg)
                if ok:
                    st.success(msg)
                    # 텔레그램 ID 입력한 경우 웰컴 메시지 발송
                    if new_tg.strip():
                        with st.spinner("텔레그램 연결 확인 중..."):
                            sent = send_welcome(new_tg.strip(), new_id)
                        if sent:
                            st.info("📱 텔레그램으로 환영 메시지를 발송했어요! 확인해보세요.")
                        else:
                            st.warning("⚠️ 텔레그램 발송에 실패했어요. Chat ID를 다시 확인해주세요.")
                    st.session_state.user_id = new_id
                    st.rerun()
                else:
                    st.error(msg)


# ── 구독 테이블 ───────────────────────────────────────────────
def show_subscription_table(items: list):
    if not items:
        st.info("등록된 구독 서비스가 없습니다. 아래에서 추가해보세요!")
        return

    rows = []
    for item in items:
        try:
            days = days_until_expiry(item.get("end_date", ""))
        except Exception:
            days = 999
        badge = get_status_badge(days)
        payment_date = item.get("payment_date", "-")
        if str(payment_date).isdigit():
            payment_date = f"매월 {payment_date}일"

        rows.append({
            "서비스명": item.get("name", ""),
            "구독 시작일": item.get("start_date", ""),
            "만료일": item.get("end_date", ""),
            "결제일": payment_date,
            "구독 기간": item.get("billing_cycle", ""),
            "총 가격": format_price(item.get("total_price", 0)),
            "월 환산": format_price(item.get("monthly_price", 0)),
            "공유 인원": item.get("shared_members", 1),
            "상태": badge,
            "링크": item.get("url", ""),
            "설명": item.get("description", ""),
            "비고": item.get("note", ""),
            "_id": item.get("id", ""),
            "_days": days,
        })

    df = pd.DataFrame(rows)

    def highlight_row(row):
        days = row["_days"]
        if days <= 7:
            return ["background-color: #ffe0e0; color: #333333"] * len(row)
        elif days <= 30:
            return ["background-color: #fff3e0; color: #333333"] * len(row)
        return [""] * len(row)

    display_cols = ["서비스명", "구독 시작일", "만료일", "결제일", "구독 기간",
                    "총 가격", "월 환산", "공유 인원", "상태", "링크", "설명", "비고"]
    styled = df[display_cols + ["_days"]].style.apply(highlight_row, axis=1)

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        column_config={
            "링크": st.column_config.LinkColumn("링크"),
            "_days": None,
        },
    )


# ── 구독 추가/수정 폼 ─────────────────────────────────────────
def show_subscription_form(user_id: str, edit_item: dict = None):
    is_edit = edit_item is not None
    title = "✏️ 구독 수정" if is_edit else "➕ 구독 추가"
    st.subheader(title)

    with st.form("sub_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("서비스명 *", value=edit_item.get("name", "") if is_edit else "")
            start_date = st.date_input(
                "구독 시작일 *",
                value=datetime.strptime(edit_item["start_date"], "%Y-%m-%d").date() if is_edit else date.today(),
            )
            end_date = st.date_input(
                "구독 만료일 *",
                value=datetime.strptime(edit_item["end_date"], "%Y-%m-%d").date() if is_edit else date.today(),
            )
            payment_date = st.text_input(
                "결제일 (예: 15 또는 2025-01-15)",
                value=str(edit_item.get("payment_date", "")) if is_edit else "",
                help="매월 특정 일자면 숫자만 입력 (예: 15), 특정 날짜면 YYYY-MM-DD 형식으로 입력",
            )
            billing_cycle = st.selectbox(
                "구독 기간",
                ["월간", "연간", "기타"],
                index=["월간", "연간", "기타"].index(edit_item.get("billing_cycle", "월간")) if is_edit else 0,
            )
        with col2:
            total_price = st.number_input(
                "총 가격 (원) *",
                min_value=0,
                value=int(edit_item.get("total_price", 0)) if is_edit else 0,
            )
            monthly_price_auto = calc_monthly_price(int(total_price), billing_cycle)
            st.metric("월 환산 가격 (자동)", format_price(monthly_price_auto))
            shared_members = st.number_input(
                "공유 인원 (본인 포함)",
                min_value=1,
                value=int(edit_item.get("shared_members", 1)) if is_edit else 1,
            )
            url = st.text_input("관련 링크", value=edit_item.get("url", "") if is_edit else "")
            status = st.selectbox(
                "상태",
                ["active", "paused", "expired"],
                index=["active", "paused", "expired"].index(edit_item.get("status", "active")) if is_edit else 0,
            )

        description = st.text_area("설명", value=edit_item.get("description", "") if is_edit else "")
        note = st.text_input("비고", value=edit_item.get("note", "") if is_edit else "")

        col_save, col_cancel = st.columns(2)
        submitted = col_save.form_submit_button("💾 저장", use_container_width=True, type="primary")
        cancelled = col_cancel.form_submit_button("취소", use_container_width=True)

    if cancelled:
        st.session_state.edit_item_id = None
        st.rerun()

    if submitted:
        if not name:
            st.error("서비스명은 필수입니다.")
            return
        item = {
            "name": name,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "payment_date": payment_date.strip(),
            "billing_cycle": billing_cycle,
            "total_price": int(total_price),
            "monthly_price": monthly_price_auto,
            "shared_members": int(shared_members),
            "url": url.strip(),
            "description": description.strip(),
            "note": note.strip(),
            "status": status,
        }
        with st.spinner("저장 중..."):
            if is_edit:
                ok = update_subscription(user_id, edit_item["id"], item)
            else:
                ok = add_subscription(user_id, item)

        if ok:
            st.success("저장되었습니다!")
            st.session_state.edit_item_id = None
            # 저장 후 목록 탭으로 이동
            st.session_state.active_tab = "list"
            refresh()
        else:
            st.error("저장에 실패했습니다. 잠시 후 다시 시도해주세요.")


# ── 내 정보 수정 ──────────────────────────────────────────────
def show_profile_page(user_id: str):
    st.subheader("👤 내 정보 수정")
    user = get_user(user_id)
    current_tg = user.get("telegram_chat_id", "")

    with st.expander("📱 텔레그램 알림 설정", expanded=True):
        new_tg = st.text_input(
            "텔레그램 Chat ID",
            value=current_tg,
            help="변경하려면 새 Chat ID를 입력하세요.",
        )
        st.caption("💡 Chat ID 확인: 텔레그램에서 [@userinfobot](https://t.me/userinfobot) 에게 /start 를 보내세요.")
        if st.button("텔레그램 정보 저장", type="primary"):
            ok, msg = update_user(user_id, telegram_chat_id=new_tg)
            if ok:
                st.success(msg)
                # 텔레그램 ID가 입력된 경우 확인 메시지 발송
                if new_tg.strip():
                    with st.spinner("텔레그램 연결 확인 중..."):
                        sent = send_welcome(new_tg.strip(), user_id)
                    if sent:
                        st.info("📱 텔레그램으로 연결 확인 메시지를 발송했어요!")
                    else:
                        st.warning("⚠️ 텔레그램 발송에 실패했어요. Chat ID를 다시 확인해주세요.")
            else:
                st.error(msg)

    with st.expander("🔑 비밀번호 변경"):
        cur_pw = st.text_input("현재 비밀번호", type="password", key="cur_pw")
        new_pw = st.text_input("새 비밀번호", type="password", key="new_pw")
        new_pw2 = st.text_input("새 비밀번호 확인", type="password", key="new_pw2")
        if st.button("비밀번호 변경", type="primary"):
            from src.auth_manager import login as auth_login
            ok_login, _ = auth_login(user_id, cur_pw)
            if not ok_login:
                st.error("현재 비밀번호가 올바르지 않습니다.")
            elif new_pw != new_pw2:
                st.error("새 비밀번호가 일치하지 않습니다.")
            elif len(new_pw) < 4:
                st.error("비밀번호는 4자 이상이어야 합니다.")
            else:
                ok, msg = update_user(user_id, new_password=new_pw)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)


# ── 메인 페이지 ───────────────────────────────────────────────
def show_main_page(user_id: str):
    # 상단 헤더
    col_title, col_logout = st.columns([8, 1])
    with col_title:
        st.title(f"📋 {user_id}님의 구독 관리")
    with col_logout:
        if st.button("로그아웃"):
            st.session_state.user_id = None
            st.session_state.edit_item_id = None
            st.cache_data.clear()
            st.rerun()

    items = cached_load(user_id)
    active_items = [i for i in items if i.get("status") == "active"]

    # 요약 섹션
    total_monthly = sum(i.get("monthly_price", 0) for i in active_items)
    total_annual = total_monthly * 12
    col1, col2, col3 = st.columns(3)
    col1.metric("활성 구독 수", f"{len(active_items)}개")
    col2.metric("월간 총액", format_price(total_monthly))
    col3.metric("연간 총액", format_price(total_annual))
    st.markdown("---")

    # 탭
    # 저장 후 목록 탭으로 돌아오기 위한 index 관리
    tab_index = 0
    if st.session_state.get("active_tab") == "add":
        tab_index = 1
    elif st.session_state.get("active_tab") == "profile":
        tab_index = 2
    # active_tab 소비 후 초기화
    st.session_state.active_tab = "list"

    tab_list, tab_add, tab_profile = st.tabs(["📊 구독 목록", "➕ 구독 추가", "👤 내 정보"])


    with tab_list:
        # 수정/삭제 버튼 영역
        if items:
            sel_options = {f"{i.get('name','')} ({i.get('end_date','')})": i["id"] for i in items}
            selected_label = st.selectbox("항목 선택 (수정/삭제용)", ["선택하세요"] + list(sel_options.keys()))

            if selected_label != "선택하세요":
                selected_id = sel_options[selected_label]
                col_edit, col_del = st.columns(2)
                if col_edit.button("✏️ 수정", use_container_width=True):
                    st.session_state.edit_item_id = selected_id
                if col_del.button("🗑️ 삭제", use_container_width=True):
                    st.session_state.delete_item_id = selected_id

            # 삭제 확인
            if st.session_state.delete_item_id:
                del_item = next((i for i in items if i["id"] == st.session_state.delete_item_id), None)
                if del_item:
                    st.warning(f"**{del_item.get('name')}** 을(를) 삭제하시겠습니까?")
                    col_yes, col_no = st.columns(2)
                    if col_yes.button("삭제 확인", type="primary"):
                        with st.spinner("삭제 중..."):
                            ok = delete_subscription(user_id, st.session_state.delete_item_id)
                        if ok:
                            st.success("삭제되었습니다.")
                            st.session_state.delete_item_id = None
                            refresh()
                        else:
                            st.error("삭제에 실패했습니다.")
                    if col_no.button("취소"):
                        st.session_state.delete_item_id = None
                        st.rerun()

        # 수정 폼 또는 테이블
        if st.session_state.edit_item_id:
            edit_item = next((i for i in items if i["id"] == st.session_state.edit_item_id), None)
            if edit_item:
                show_subscription_form(user_id, edit_item=edit_item)
        else:
            show_subscription_table(items)

    with tab_add:
        show_subscription_form(user_id)

    with tab_profile:
        show_profile_page(user_id)


# ── 앱 진입점 ─────────────────────────────────────────────────
if st.session_state.user_id:
    show_main_page(st.session_state.user_id)
else:
    show_auth_page()