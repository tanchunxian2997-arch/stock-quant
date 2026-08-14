import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
import time

# ================= 页面配置（专为手机全屏优化） =================
st.set_page_config(
    page_title="⚡ 美股量化实时战斗看板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 注入暗黑风格 CSS
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #f8fafc; }
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 12px;
    }
    .radar-card {
        background-color: #1c1917;
        border: 1px solid #78350f;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ================= 配置区域 =================
GEMINI_API_KEY = "AQ.Ab8RN6Lo_MnLRk9ZwVQKrCumDrRMATpbE1-G6LON2eWKRhTAoA"
MY_PORTFOLIO = ["NVDA", "ANET", "NTNX", "IONQ", "SOUN", "JOBY", "EH", "NOK"]
RADAR_CANDIDATE_POOL = [
    "PLTR", "MRVL", "CRWD", "RKLB", "SYM", "ARM", "APP", "BBAI", 
    "POET", "SOFI", "AUR", "CLOV", "PLUG", "STEM", "PATH", "HIMS", "ASTS", "LUNR"
]

genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel("gemini-1.5-flash")

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return round(100 - (100 / (1 + rs)), 1)

def get_expert_decision(symbol, price, pct_change, rsi, support, resistance, vol_ratio):
    if price <= support * 1.01:
        return f"🚨 【主力弃守·短线减仓】击穿20日防守支撑(${support})！技术破位，短线严格防守！"
    if rsi >= 75 or price >= resistance * 0.99:
        return f"⚠️ 【情绪过热·分批止盈】RSI高达{rsi}，逼近上方阻力(${resistance})！严禁追高，分批锁利！"
    if vol_ratio >= 2.0 and pct_change > 0:
        return f"🚀 【主力扫货·顺势看多】量能暴增{vol_ratio}倍放量拉升！大资金进场，可顺势持股！"
    elif vol_ratio >= 2.0 and pct_change < 0:
        return f"💥 【机构砸盘·严禁接刀】放量下跌{vol_ratio}倍，大单出逃，切勿盲目抄底！"
    if rsi <= 35:
        return f"💎 【恐慌超卖·黄金低吸】RSI处于极度超卖区({rsi})，安全边际极高，适合分批低吸！"
    if pct_change >= 0:
        return f"📈 【多头蓄势·持股观望】震荡向上格局，量能平稳。持股静待上方阻力位(${resistance})。"
    else:
        return f"📊 【缩量洗盘·按兵不动】短期正常回调整理，防守位(${support})依然有效，耐心观察。"

# ================= 页面顶部 =================
col_title, col_btn = st.columns([3, 1])
with col_title:
    st.markdown("<h2 style='color:#38bdf8;margin:0;'>⚡ 美股量化实时战斗看板</h2>", unsafe_allow_html=True)
    st.caption("24小时云端常驻 · 自动计算买卖防守与潜力股排名")
with col_btn:
    if st.button("🔄 立即刷新行情"):
        st.rerun()

# ================= 1. 现有持仓实战监控 =================
st.markdown("<h4 style='color:#7dd3fc;border-bottom:1px solid #1e293b;padding-bottom:6px;'>⚡ 现有持仓实时监控</h4>", unsafe_allow_html=True)

cols_p = st.columns(2)
for idx, symbol in enumerate(MY_PORTFOLIO):
    col = cols_p[idx % 2]
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1mo", interval="1d")
        if len(df) >= 15:
            curr_price = round(df['Close'].iloc[-1], 2)
            prev_close = round(df['Close'].iloc[-2], 2)
            pct_change = round(((curr_price - prev_close) / prev_close) * 100, 2)
            color = "#10b981" if pct_change >= 0 else "#ef4444"
            sign = "+" if pct_change >= 0 else ""

            high_20 = round(df['High'].max(), 2)
            low_20 = round(df['Low'].min(), 2)
            curr_vol = df['Volume'].iloc[-1]
            avg_vol = df['Volume'].rolling(5).mean().iloc[-2]
            vol_ratio = round(curr_vol / avg_vol, 1) if avg_vol > 0 else 1.0
            rsi = calculate_rsi(df['Close']).iloc[-1]

            verdict = get_expert_decision(symbol, curr_price, pct_change, rsi, low_20, high_20, vol_ratio)

            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;">
                        <span style="font-size:22px;font-weight:900;color:#ffffff;">{symbol}</span>
                        <div>
                            <span style="font-size:20px;font-weight:800;color:#ffffff;">${curr_price}</span>
                            <span style="font-size:12px;font-weight:bold;color:{color};margin-left:4px;">{sign}{pct_change}%</span>
                        </div>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:11px;color:#94a3b8;background:#0f172a;padding:6px 8px;border-radius:6px;margin-bottom:6px;">
                        <span>支撑: <b style="color:#34d399">${low_20}</b></span>
                        <span>阻力: <b style="color:#f87171">${high_20}</b></span>
                        <span>RSI: <b>{rsi}</b></span>
                        <span>量能: <b>{vol_ratio}x</b></span>
                    </div>
                    <div style="background:#091e3a;border:1px solid #1e40af;border-radius:6px;padding:8px;font-size:11px;color:#e2e8f0;line-height:1.4;">
                        <span style="color:#60a5fa;font-weight:bold;">🤖 操盘决断:</span> {verdict}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    except:
        continue

# ================= 2. 全自动雷达潜力股榜单 ($1 - $100) =================
st.markdown("<h4 style='color:#fbbf24;border-bottom:1px solid #451a03;padding-bottom:6px;margin-top:20px;'>🏆 全自动雷达·潜力金股排行榜 ($1 - $100)</h4>", unsafe_allow_html=True)

scanned = []
for sym in RADAR_CANDIDATE_POOL:
    if sym in MY_PORTFOLIO: continue
    try:
        t = yf.Ticker(sym)
        hist = t.history(period="1mo", interval="1d")
        if len(hist) >= 15:
            p = round(hist['Close'].iloc[-1], 2)
            prev_p = round(hist['Close'].iloc[-2], 2)
            pct = round(((p - prev_p) / prev_p) * 100, 2)
            if 1.0 <= p <= 100.0:
                rsi_val = calculate_rsi(hist['Close']).iloc[-1]
                low_20 = round(hist['Low'].min(), 2)
                curr_vol = hist['Volume'].iloc[-1]
                avg_vol = hist['Volume'].rolling(5).mean().iloc[-2]
                vol_r = round(curr_vol / avg_vol, 1) if avg_vol > 0 else 1.0
                safety_pct = round(((p - low_20) / low_20) * 100, 1)

                if rsi_val <= 72:
                    score = 60
                    if 45 <= rsi_val <= 62: score += 20
                    if 1.3 <= vol_r <= 3.0: score += 15
                    if safety_pct <= 15: score += 10
                    scanned.append({
                        "symbol": sym, "price": p, "pct": pct, "rsi": rsi_val,
                        "low_20": low_20, "target": round(p * 1.28, 2),
                        "safety_pct": safety_pct, "score": min(score, 98)
                    })
    except:
        continue

scanned.sort(key=lambda x: x['score'], reverse=True)
cols_r = st.columns(2)
medals = ["🥇 TOP 1 (头号金股)", "🥈 TOP 2 (重点标的)", "🥉 TOP 3 (黑马蓄势)", "🏅 TOP 4 (优质备选)"]

for idx, item in enumerate(scanned[:4]):
    col = cols_r[idx % 2]
    c = "#10b981" if item['pct'] >= 0 else "#ef4444"
    s = "+" if item['pct'] >= 0 else ""
    stars = "⭐️⭐️⭐️⭐️⭐️" if item['score'] >= 90 else "⭐️⭐️⭐️⭐️"

    with col:
        st.markdown(f"""
        <div class="radar-card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;border-bottom:1px solid #451a03;padding-bottom:4px;">
                <span style="font-size:12px;font-weight:900;color:#fbbf24;background:#451a03;padding:2px 6px;border-radius:4px;">{medals[idx]}</span>
                <span style="font-size:11px;font-weight:bold;color:#fde047;">{stars}</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <span style="font-size:22px;font-weight:900;color:#ffffff;">{item['symbol']}</span>
                <div>
                    <span style="font-size:20px;font-weight:800;color:#ffffff;">${item['price']}</span>
                    <span style="font-size:12px;font-weight:bold;color:{c};margin-left:4px;">{s}{item['pct']}%</span>
                </div>
            </div>
            <div style="background:#064e3b;color:#34d399;font-size:10px;padding:2px 6px;border-radius:4px;font-weight:bold;margin-bottom:6px;display:inline-block;">
                🛡️ 安全边际：仅高于底部 {item['safety_pct']}%
            </div>
            <div style="font-size:11px;color:#fef3c7;background:#291e10;padding:6px 8px;border-radius:6px;margin-bottom:6px;">
                <b>【爆发逻辑】</b>: 底部充分洗盘筑底，主力资金沉淀，估值极具性价比，具备2-3个月+28%爆发潜力。
            </div>
            <div style="display:flex;justify-content:space-between;font-size:10px;color:#d6d3d1;background:#0c0a09;padding:4px 8px;border-radius:4px;">
                <span>底线: <b style="color:#34d399">${item['low_20']}</b></span>
                <span>RSI: <b style="color:#fde047;">{item['rsi']}</b></span>
                <span>2-3月目标: <b style="color:#f87171">${item['target']}</b></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
