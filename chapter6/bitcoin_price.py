"""
=============================================================
  Bitcoin 实时行情显示应用
  ─────────────────────────────
  框架: Streamlit
  数据源: CoinGecko API (免费, 无需密钥)
  功能: 实时 BTC/USD 价格 + 24h 涨跌幅/涨跌额 + 手动刷新
=============================================================
"""

import streamlit as st
import requests
from datetime import datetime


# ==================== 页面基础配置 ====================
st.set_page_config(
    page_title="Bitcoin 实时行情",
    page_icon="₿",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ==================== 自定义 CSS 样式 ====================
CUSTOM_CSS = """
<style>
    /* ---------- 全局 ---------- */
    .block-container {
        padding-top: 3rem;
        max-width: 620px;
    }

    /* ---------- 价格卡片 ---------- */
    .price-card {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        padding: 2.8rem 2rem 2.2rem 2rem;
        border-radius: 1.2rem;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.35);
        text-align: center;
        margin: 1.5rem 0 1rem 0;
    }
    .coin-label {
        color: rgba(255, 255, 255, 0.55);
        font-size: 0.95rem;
        font-weight: 500;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }
    .price-value {
        font-size: 3.2rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -1px;
        margin: 0.3rem 0 0.8rem 0;
    }

    /* ---------- 涨跌徽章 ---------- */
    .change-badge {
        display: inline-block;
        padding: 0.45rem 1.2rem;
        border-radius: 2rem;
        font-size: 1.1rem;
        font-weight: 600;
    }
    .change-up {
        background: rgba(0, 200, 83, 0.15);
        color: #69F0AE;
    }
    .change-down {
        background: rgba(255, 23, 68, 0.15);
        color: #FF5252;
    }

    /* ---------- 底部信息 ---------- */
    .update-info {
        text-align: center;
        color: #888;
        font-size: 0.82rem;
        margin-top: 1.6rem;
    }
    .footer-line {
        text-align: center;
        color: #666;
        font-size: 0.75rem;
        margin-top: 0.5rem;
    }

    /* ---------- 标题装饰线 ---------- */
    .title-bar {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.6rem;
        margin-bottom: 0.5rem;
    }
    .title-bar span {
        font-size: 2rem;
        font-weight: 800;
    }
</style>
"""


# ==================== 数据获取层 ====================
@st.cache_data(ttl=60, show_spinner=False)
def fetch_bitcoin_data() -> dict:
    """
    调用 CoinGecko API 获取比特币实时数据。

    Returns:
        dict: {
            "price"       : float,  # 当前 USD 价格
            "change_abs"  : float,  # 24h 涨跌额 (USD)
            "change_pct"  : float,  # 24h 涨跌幅 (%)
            "timestamp"   : str,    # 获取时间字符串
        }

    Raises:
        requests.RequestException  – 网络层异常
        KeyError                   – 返回数据格式不符预期
    """
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }

    # 发起请求，10 秒超时保护
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()

    raw = resp.json()["bitcoin"]

    current_price = raw["usd"]
    change_pct = raw["usd_24h_change"]          # 已是百分比数值，如 2.53

    # 反推 24h 前价格 → 算出涨跌绝对额
    # current = prev × (1 + pct/100)  →  prev = current / (1 + pct/100)
    prev_price = current_price / (1 + change_pct / 100)
    change_abs = current_price - prev_price

    return {
        "price": current_price,
        "change_abs": change_abs,
        "change_pct": change_pct,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ==================== UI 渲染层 ====================
def render_price_card(data: dict) -> None:
    """将数据渲染为暗色渐变价格卡片。"""
    is_up = data["change_pct"] >= 0
    badge_cls = "change-up" if is_up else "change-down"
    arrow = "▲" if is_up else "▼"
    sign = "+" if is_up else ""

    st.markdown(
        f"""
        <div class="price-card">
            <div class="coin-label">BTC / USD</div>
            <div class="price-value">${data['price']:,.2f}</div>
            <div class="change-badge {badge_cls}">
                {arrow}&nbsp; {sign}{data['change_abs']:,.2f} USD
                &nbsp;({sign}{data['change_pct']:.2f}%)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_update_info(data: dict) -> None:
    """渲染底部更新时间与数据来源。"""
    st.markdown(
        f'<div class="update-info">'
        f"🕐 最后更新：{data['timestamp']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"数据来源：CoinGecko"
        f"</div>",
        unsafe_allow_html=True,
    )


# ==================== 异常处理层 ====================
def handle_error(exc: Exception) -> None:
    """根据异常类型输出用户友好的错误提示。"""
    if isinstance(exc, requests.exceptions.Timeout):
        st.error("⚠️ **请求超时** — 网络响应过慢，请检查连接后重试。")
    elif isinstance(exc, requests.exceptions.ConnectionError):
        st.error("⚠️ **网络连接失败** — 请检查您的网络设置。")
    elif isinstance(exc, requests.exceptions.HTTPError):
        code = exc.response.status_code
        if code == 429:
            st.error("⚠️ **API 限流** — 请求过于频繁，请等待 1 分钟后再试。")
        elif code >= 500:
            st.error("⚠️ **服务暂时不可用** — CoinGecko 服务器异常，请稍后再试。")
        else:
            st.error(f"⚠️ **请求失败** (HTTP {code})，请稍后再试。")
    elif isinstance(exc, KeyError):
        st.error("⚠️ **数据解析异常** — API 返回格式可能已变更，请联系开发者。")
    else:
        st.error("⚠️ **未知异常** — 请稍后再试或联系技术支持。")

    # 折叠展示技术细节，方便排查
    with st.expander("🔍 查看详细错误信息"):
        st.code(str(exc), language="plaintext")


# ==================== 主程序入口 ====================
def main() -> None:
    # 1) 注入样式
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # 2) 标题
    st.markdown(
        '<div class="title-bar"><span>₿</span><span>Bitcoin 实时行情</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # 3) 刷新按钮（居中布局）
    _left, center, _right = st.columns([2, 1, 2])
    with center:
        refresh_clicked = st.button("🔄  刷新数据", use_container_width=True, type="primary")

    # 点击刷新 → 清除缓存 → 下次调用重新请求
    if refresh_clicked:
        st.cache_data.clear()

    # 4) 获取数据 & 渲染
    try:
        with st.spinner("📡 正在获取最新行情数据..."):
            data = fetch_bitcoin_data()

        render_price_card(data)
        render_update_info(data)

    except Exception as exc:
        handle_error(exc)

    # 5) 页脚
    st.markdown("---")
    st.markdown(
        '<div class="footer-line">数据每分钟自动缓存更新 · 仅供参考，不构成投资建议</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()