from datetime import date, datetime
import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def days_until_expiry(end_date_str: str) -> int:
    end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    return (end - date.today()).days


def calc_monthly_price(total_price: int, billing_cycle: str) -> int:
    if billing_cycle == "연간":
        return round(total_price / 12)
    return total_price


def get_status_badge(days: int, auto_renew: bool = False) -> str:
    if auto_renew:
        return "∞ 자동갱신"
    if days < 0:
        return "만료"
    elif days == 0:
        return "D-Day"
    elif days <= 7:
        return f"D-{days} 🔴"
    elif days <= 30:
        return f"D-{days} 🟠"
    else:
        return f"D-{days}"


def format_price(price: int) -> str:
    return f"{price:,}원"