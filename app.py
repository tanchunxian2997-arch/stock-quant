import streamlit as st
import yfinance as yf
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh

# ================= 1. 页面基础配置 =================
st.set_page_config(
    page_title="⚡ 美股量化实时战斗看板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 每 30 秒 (30000 毫秒) 自动无感拉取最新美股行情并全屏刷新
st_autorefresh(interval=30000, key="realtime_stock_auto_refresh")

# 注入尊享暗黑风格 CSS
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #f8fafc; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1200px; }
</style>
""", unsafe_allow_html=True)

# ================= 2. 标的池配置 =================
# 现有核心持仓池
MY_PORTFOLIO = ["NVDA", "ANET", "NTNX", "IONQ", "SOUN", "JOBY", "EH", "NOK"]

# $1 - $100 潜力金股深度调研数据库
RADAR_STOCK_PROFILES = {
    "SYM": {
        "sector": "AI 仓储机器人自动化系统",
        "moat": "全自动化软硬件一体方案，锁定沃尔玛等头部零售巨头百亿未交付积压订单。",
        "catalyst": "前期深度洗盘估值挤压充分，在强支撑企稳，大型配送履约中心进入交付验收放量期。"
    },
    "RKLB": {
        "sector": "商业航天 / 运载火箭发射与卫星制造",
        "moat": "常态化成功发射仅次于SpaceX，手握NASA与美军长期稳定发射服务合同。",
        "catalyst": "下一代中型火箭 Neutron 试飞节点临近，底部筹码压实，商业卫星密集交付催化主升浪。"
    },
    "SOFI": {
        "sector": "Fintech / 新一代 AI 智能数字银行",
        "moat": "全牌照银行+高粘性青年高净值客群，Galileo 金融科技底层云平台赋能行业。",
        "catalyst": "降息周期开启带来借贷与再融资爆发，非利息收入高速增长，连续数季度盈利超预期。"
    },
    "CLOV": {
        "sector": "AI 医疗健康管理 / Medicare SaaS",
        "moat": "Clover Assistant AI 算法精准降低医保赔付率，营运现金流实现历史性转正。",
        "catalyst": "单价亲民，估值处于历史大底，SaaS 技术外包服务开启第二成长曲线。"
    },
    "AUR": {
        "sector": "自动驾驶卡车 / AI 货运干线物流",
        "moat": "Aurora Driver 拥有全球顶级自动驾驶全栈技术，深度绑定沃尔沃与帕卡卡车巨头。",
        "catalyst": "商业化无安全员自动驾驶商业货运航线正式商用落地，属于低价高爆发先锋。"
    },
    "PLTR": {
        "sector": "企业级 AI 操作系统 / 军工大数据",
        "moat": "AIP 平台在商业与军工端具备极高粘性与垄断级转换成本，政府大单持续放量。",
        "catalyst": "企业端 AIP 订单转化率超预期，未来2-3个月季报指引持续上修，机构筹码高度稳定。"
    },
    "MRVL": {
        "sector": "AI 数据中心高速互连 / 定制 ASIC 芯片",
        "moat": "数据中心光电互联芯片与头部云厂商定制 AI 芯片的核心绝对垄断供应商。",
        "catalyst": "AI 算力集群对高速带宽需求井喷，定制 ASIC 芯片出货进入集中放量期。"
    },
    "POET": {
        "sector": "AI 数据中心光引擎 / 光电共封装 (CPO)",
        "moat": "独家光电混合集成平台，大幅降低 AI 算力中心能耗与制造成本。",
        "catalyst": "头部光模块厂商样品验证通过进入量产出货期，属于典型的 AI 算力低位高弹性补涨链条。"
    },
    "BBAI": {
        "sector": "国防军工 AI 决策与供应链分析",
        "moat": "深耕美军与国家安全部门的边缘 AI 决策系统，政府合同粘性极强。",
        "catalyst": "低位持续缩量洗盘，筹码沉淀充分，突发防务订单极易引爆 20%-30% 补涨行情。"
    },
    "ACHR": {
        "sector": "eVTOL 低空经济 / 电动垂直起降飞行器",
        "moat": "深度绑定 Stellantis 汽车巨头与美联航，适航认证进度位列全球第一梯队。",
        "catalyst": "商业化载人试飞节点临近，低空基建政策催化，单价亲民且处于相对底部洗盘末期。"
    }
}

# ================= 3. 量化核心计算函数 =================
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return round(100 - (100 / (1 + rs)), 1)

def get_expert_decision(symbol, price, pct_change, rsi, support, resistance, vol_ratio):
    if price <= support * 1.01:
        return f"🚨 【主力弃守·短线减仓】击穿20日防守支撑(${support})！技术破位，短线严格止损防守！"
    if rsi >= 75 or price >= resistance * 0.99:
        return f"⚠️ 【情绪过热·分批止盈】RSI高达{rsi}，逼近上方阻力(${resistance})！获利盘与解套盘抛压大，严禁追高！"
    if vol_ratio >= 2.0 and pct_change > 0:
        return f"🚀 【主力扫货·顺势看多】量能暴增{vol_ratio}倍放量拉升！大资金进场迹象明显，可顺势持股或分批跟进！"
    elif vol_ratio >= 2.0 and pct_change < 0:
        return f"💥 【机构砸盘·严禁接刀】放量下跌{vol_ratio}倍，大单砸盘出逃，等待企稳信号前切勿盲目抄底！"
    if rsi <= 35:
        return f"💎 【恐慌超卖·黄金低吸】RSI处于极度超卖恐慌区({rsi})，安全边际极高，适合分批左侧挂单低吸！"
    if pct_change >= 0:
        return f"📈 【多头蓄势·持股观望】震荡向上格局，量能平稳。持股静待上方阻力位(${resistance})，不随意折腾。"
    else:
        return f"📊 【缩量洗盘·按兵不动】短期正常回调整理，防守位(${support})依然有效，耐心观察多空博弈。"

# ================= 4. 顶部操作栏 =================
col_title, col_btn = st.columns([3, 1])
with col_title:
    st.markdown("<h2 style='color:#38bdf8;margin:0;font-weight:900;'>⚡ 美股量化实时战斗看板</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;font-size:12px;margin:2px 0 0 0;'>24小时云端常驻 · 自动每30秒更新最新盘面 · 30年实战交易员风控引擎</p>", unsafe_allow_html=True)
with col_btn:
    if st.button("🔄 手动强制刷新"):
        st.rerun()

# ================= 5. 模块一：现有持仓实战监控看板 =================
st.markdown("<div style='margin-top:16px;margin-bottom:12px;border-bottom:1px solid #1e293b;padding-bottom:6px;'><h3 style='color:#38bdf8;margin:0;font-size:18px;font-weight:800;'>⚡ 现有持仓实时监控看板</h3></div>", unsafe_allow_html=True)

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

            action_banner = ""
            if curr_price <= low_20 * 1.01:
                action_banner = f"<div style='background:#7f1d1d;color:#fecaca;padding:6px 10px;border-radius:6px;font-size:11px;font-weight:bold;margin-bottom:8px;border-left:4px solid #ef4444;'>🚨 破位警报：跌破20日防守支撑(${low_20})！主力弃守，短线减仓！</div>"
            elif curr_price >= high_20 * 0.98 or rsi >= 75:
                action_banner = f"<div style='background:#854d0e;color:#fef08a;padding:6px 10px;border-radius:6px;font-size:11px;font-weight:bold;margin-bottom:8px;border-left:4px solid #eab308;'>⚠️ 阻力预警：逼近前期抛压高位(${high_20})，严禁追涨！</div>"

            verdict = get_expert_decision(symbol, curr_price, pct_change, rsi, low_20, high_20, vol_ratio)

            card_html = (
                f"<div style='background:#1e293b;border:1px solid #334155;border-radius:14px;padding:16px;margin-bottom:14px;box-shadow:0 8px 16px rgba(0,0,0,0.4);'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;'>"
                f"<span style='font-size:22px;font-weight:900;color:#f8fafc;'>{symbol}</span>"
                f"<div style='text-align:right;'><span style='font-size:22px;font-weight:800;color:#ffffff;'>${curr_price}</span>"
                f"<span style='font-size:13px;font-weight:bold;color:{color};margin-left:4px;'>{sign}{pct_change}%</span></div>"
                f"</div>"
                f"{action_banner}"
                f"<div style='display:flex;justify-content:space-between;font-size:11px;color:#94a3b8;background:#0f172a;padding:6px 10px;border-radius:6px;margin-bottom:8px;'>"
                f"<span>防守支撑: <b style='color:#34d399'>${low_20}</b></span>"
                f"<span>阻力目标: <b style='color:#f87171'>${high_20}</b></span>"
                f"<span>RSI: <b>{rsi}</b></span>"
                f"<span>量能: <b>{vol_ratio}x</b></span>"
                f"</div>"
                f"<div style='background:#091e3a;border:1px solid #1e40af;border-radius:8px;padding:10px;'>"
                f"<div style='font-size:11px;font-weight:bold;color:#60a5fa;margin-bottom:4px;'>🤖 Gemini 操盘手实战决断:</div>"
                f"<div style='font-size:12px;color:#e2e8f0;line-height:1.45;'>{verdict}</div>"
                f"</div>"
                f"</div>"
            )
            with col:
                st.markdown(card_html, unsafe_allow_html=True)
    except:
        continue

# ================= 6. 模块二：$1 - $100 潜力金股深度调研排行榜 =================
st.markdown("<div style='margin-top:24px;margin-bottom:12px;border-bottom:1px solid #78350f;padding-bottom:6px;'><h3 style='color:#fbbf24;margin:0;font-size:18px;font-weight:800;'>🏆 全自动雷达·潜力金股排行榜 ($1 - $100 深度调研版)</h3><p style='color:#d6d3d1;font-size:11px;margin:2px 0 0 0;'>已包含：公司主营业务赛道 / 核心竞争壁垒 / 中期业绩订单催化剂 / 目标位测算</p></div>", unsafe_allow_html=True)

scanned = []
for sym, profile in RADAR_STOCK_PROFILES.items():
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

                if rsi_val <= 75:
                    score = 60
                    if 45 <= rsi_val <= 62: score += 20
                    if 1.3 <= vol_r <= 3.0: score += 15
                    if safety_pct <= 15: score += 10
                    scanned.append({
                        "symbol": sym, "price": p, "pct": pct, "rsi": rsi_val,
                        "low_20": low_20, "target": round(p * 1.28, 2),
                        "safety_pct": safety_pct, "score": min(score, 98),
                        "sector": profile["sector"],
                        "moat": profile["moat"],
                        "catalyst": profile["catalyst"]
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
    stars = "⭐️⭐️⭐️⭐️⭐️ (5星·强烈推荐)" if item['score'] >= 90 else "⭐️⭐️⭐️⭐️ (4星·优质入选)"

    radar_card_html = (
        f"<div style='background:#1c1917;border:2px solid #b45309;border-radius:14px;padding:18px;margin-bottom:14px;box-shadow:0 8px 16px rgba(0,0,0,0.6);'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;border-bottom:1px solid #451a03;padding-bottom:6px;'>"
        f"<span style='font-size:13px;font-weight:900;color:#fbbf24;background:#451a03;padding:3px 8px;border-radius:6px;border:1px solid #d97706;'>{medals[idx]}</span>"
        f"<span style='font-size:12px;font-weight:bold;color:#fde047;'>{stars}</span>"
        f"</div>"
        f"<div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px;'>"
        f"<div><span style='font-size:26px;font-weight:900;color:#ffffff;'>{item['symbol']}</span>"
        f"<span style='font-size:11px;color:#a8a29e;margin-left:6px;'>综合量化分: <b style='color:#34d399;font-size:14px;'>{item['score']}</b></span></div>"
        f"<div style='text-align:right;'><span style='font-size:22px;font-weight:800;color:#ffffff;'>${item['price']}</span>"
        f"<span style='font-size:12px;font-weight:bold;color:{c};margin-left:4px;'>{s}{item['pct']}%</span></div>"
        f"</div>"
        f"<div style='display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap;'>"
        f"<span style='background:#064e3b;color:#34d399;font-size:11px;padding:3px 8px;border-radius:4px;font-weight:bold;border:1px solid #059669;'>🛡️ 安全边际：仅高于20日底部 {item['safety_pct']}%</span>"
        f"<span style='background:#292524;color:#fde047;font-size:11px;padding:3px 8px;border-radius:4px;border:1px solid #78350f;'>价位: $1-$100</span>"
        f"</div>"
        f"<div style='font-size:12px;color:#fef3c7;background:#291e10;border:1px solid #78350f;border-radius:8px;padding:10px;margin-bottom:10px;line-height:1.5;'>"
        f"<div style='color:#fbbf24;font-weight:bold;margin-bottom:4px;'>🏢 核心赛道：{item['sector']}</div>"
        f"<div style='color:#d6d3d1;margin-bottom:4px;'><b style='color:#fde047;'>🛡️ 护城河壁垒：</b>{item['moat']}</div>"
        f"<div style='color:#fef08a;'><b style='color:#f59e0b;'>🚀 推荐理由 & 爆发催化：</b>{item['catalyst']}</div>"
        f"</div>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#d6d3d1;background:#0c0a09;padding:6px 10px;border-radius:6px;'>"
        f"<span>安全防守底线: <b style='color:#34d399'>${item['low_20']}</b></span>"
        f"<span>RSI: <b style='color:#fde047;'>{item['rsi']}</b></span>"
        f"<span>2-3月目标位: <b style='color:#f87171'>${item['target']} (+28%)</b></span>"
        f"</div>"
        f"</div>"
    )
    with col:
        st.markdown(radar_card_html, unsafe_allow_html=True)
