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

# 每 30 秒自动无感自刷新
st_autorefresh(interval=30000, key="realtime_stock_auto_refresh")

# 注入极简暗黑交易风格与卡片圆角样式
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #f8fafc; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1200px; }
    
    /* 搜索框极简美化 */
    .stTextInput > div > div > input {
        background-color: #111827 !important;
        color: #f8fafc !important;
        border-radius: 12px !important;
        border: 1px solid #1f2937 !important;
        padding: 10px 14px !important;
        font-size: 14px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 1px #38bdf8 !important;
    }

    /* 快捷搜索标签按钮 */
    .quick-tag button {
        background-color: #1e293b !important;
        color: #94a3b8 !important;
        border: 1px solid #334155 !important;
        border-radius: 20px !important;
        padding: 2px 10px !important;
        font-size: 11px !important;
    }
    .quick-tag button:hover {
        color: #38bdf8 !important;
        border-color: #38bdf8 !important;
    }

    /* 移除胶囊按钮样式 */
    .remove-pill button {
        background-color: #1f2937 !important;
        color: #f87171 !important;
        border: 1px solid #374151 !important;
        border-radius: 20px !important;
        font-size: 12px !important;
        font-weight: bold !important;
        padding: 4px 12px !important;
    }
    .remove-pill button:hover {
        background-color: #7f1d1d !important;
        color: #ffffff !important;
        border-color: #ef4444 !important;
    }
</style>
""", unsafe_allow_html=True)

# ================= 2. 会话状态与初始持仓 =================
DEFAULT_PORTFOLIO = ["NVDA", "ANET", "NTNX", "IONQ", "SOUN", "JOBY", "EH", "NOK"]

if "my_portfolio" not in st.session_state:
    st.session_state["my_portfolio"] = DEFAULT_PORTFOLIO.copy()

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

# ================= 3. 量化核心函数 =================
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

# ================= 4. 顶部操作栏与大盘晴雨表 =================
col_title, col_btn = st.columns([3, 1])
with col_title:
    st.markdown("<h2 style='color:#38bdf8;margin:0;font-weight:900;font-size:22px;'>⚡ 美股量化实时战斗看板</h2>", unsafe_allow_html=True)
with col_btn:
    if st.button("🔄 刷新盘面", use_container_width=True):
        st.rerun()

try:
    macro_tickers = ["SPY", "QQQ", "^VIX"]
    macro_data = yf.download(macro_tickers, period="2d", interval="1d", progress=False)['Close']
    if len(macro_data) >= 2:
        spy_c, qqq_c, vix_c = macro_data['SPY'].iloc[-1], macro_data['QQQ'].iloc[-1], macro_data['^VIX'].iloc[-1]
        spy_p, qqq_p, vix_p = macro_data['SPY'].iloc[-2], macro_data['QQQ'].iloc[-2], macro_data['^VIX'].iloc[-2]
        spy_pct = round(((spy_c - spy_p) / spy_p) * 100, 2)
        qqq_pct = round(((qqq_c - qqq_p) / qqq_p) * 100, 2)
        vix_pct = round(((vix_c - vix_p) / vix_p) * 100, 2)

        st.markdown(f"""
        <div style="display:flex;gap:12px;background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:6px 12px;margin-top:8px;margin-bottom:12px;font-size:12px;overflow-x:auto;">
            <span>🏛️ <b>SPY</b>: ${round(spy_c, 2)} (<b style="color:{'#10b981' if spy_pct>=0 else '#ef4444'}">{'+' if spy_pct>=0 else ''}{spy_pct}%</b>)</span>
            <span>|</span>
            <span>💻 <b>QQQ</b>: ${round(qqq_c, 2)} (<b style="color:{'#10b981' if qqq_pct>=0 else '#ef4444'}">{'+' if qqq_pct>=0 else ''}{qqq_pct}%</b>)</span>
            <span>|</span>
            <span>⚠️ <b>VIX</b>: {round(vix_c, 2)} (<b style="color:{'#ef4444' if vix_pct>=0 else '#10b981'}">{'+' if vix_pct>=0 else ''}{vix_pct}%</b>)</span>
        </div>
        """, unsafe_allow_html=True)
except:
    pass

# ================= 5. 全新极简搜索栏 + 热门快捷点选 =================
search_col, _ = st.columns([1, 0.01])
with search_col:
    search_query = st.text_input("", placeholder="🔍 搜索美股代码快速体检与加仓 (如 TSLA, AMD, PLTR, AAPL)...", label_visibility="collapsed").strip().upper()

# 热门快捷标签
tag_cols = st.columns(6)
hot_symbols = ["TSLA", "AMD", "PLTR", "AAPL", "COIN", "MARA"]
for i, sym in enumerate(hot_symbols):
    with tag_cols[i]:
        st.markdown('<div class="quick-tag">', unsafe_allow_html=True)
        if st.button(f"+ {sym}", key=f"quick_tag_{sym}", use_container_width=True):
            if sym not in st.session_state["my_portfolio"]:
                st.session_state["my_portfolio"].append(sym)
                st.toast(f"已成功添加 {sym} 到盯盘池！", icon="✅")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# 搜索结果呈现
if search_query:
    try:
        s_ticker = yf.Ticker(search_query)
        s_df = s_ticker.history(period="1mo", interval="1d")
        if len(s_df) >= 15:
            s_price = round(s_df['Close'].iloc[-1], 2)
            s_prev = round(s_df['Close'].iloc[-2], 2)
            s_pct = round(((s_price - s_prev) / s_prev) * 100, 2)
            s_color = "#10b981" if s_pct >= 0 else "#ef4444"
            s_sign = "+" if s_pct >= 0 else ""
            s_high = round(s_df['High'].max(), 2)
            s_low = round(s_df['Low'].min(), 2)
            s_vol = s_df['Volume'].iloc[-1]
            s_avg_vol = s_df['Volume'].rolling(5).mean().iloc[-2]
            s_vol_r = round(s_vol / s_avg_vol, 1) if s_avg_vol > 0 else 1.0
            s_rsi = calculate_rsi(s_df['Close']).iloc[-1]
            s_verdict = get_expert_decision(search_query, s_price, s_pct, s_rsi, s_low, s_high, s_vol_r)

            col_res_card, col_res_btn = st.columns([3.5, 1])
            with col_res_card:
                st.markdown(f"""
                <div style="background:#172554;border:1px solid #3b82f6;border-radius:12px;padding:12px;margin-top:8px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-size:18px;font-weight:900;color:#ffffff;">{search_query} <span style="font-size:11px;color:#93c5fd;font-weight:normal;">(实时诊断)</span></span>
                        <div>
                            <span style="font-size:18px;font-weight:800;color:#ffffff;">${s_price}</span>
                            <span style="font-size:12px;font-weight:bold;color:{s_color};margin-left:4px;">{s_sign}{s_pct}%</span>
                        </div>
                    </div>
                    <div style="font-size:11px;color:#bfdbfe;margin-top:3px;">
                        支撑: <b>${s_low}</b> | 阻力: <b>${s_high}</b> | RSI: <b>{s_rsi}</b> | 量能: <b>{s_vol_r}x</b>
                    </div>
                    <div style="font-size:11px;color:#e0e7ff;margin-top:4px;background:#1e3a8a;padding:5px 8px;border-radius:6px;">
                        💡 {s_verdict}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_res_btn:
                st.write("")
                if search_query not in st.session_state["my_portfolio"]:
                    if st.button(f"➕ 立即盯盘", key=f"add_{search_query}", use_container_width=True):
                        st.session_state["my_portfolio"].append(search_query)
                        st.toast(f"已成功添加 {search_query} 到实时盯盘！", icon="✅")
                        st.rerun()
                else:
                    st.button("✅ 已在持仓中", disabled=True, use_container_width=True)
        else:
            st.warning(f"未能查询到 {search_query} 的行情数据。")
    except Exception as e:
        st.error(f"查询失败: {e}")

# ================= 6. 模块一：现有持仓实战监控看板（一体化无缝卡片） =================
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.markdown(f"<div style='margin-top:16px;margin-bottom:10px;'><h3 style='color:#38bdf8;margin:0;font-size:17px;font-weight:800;'>⚡ 现有持仓实时监控看板 ({len(st.session_state['my_portfolio'])} 只)</h3></div>", unsafe_allow_html=True)
with col_head2:
    pass

# 轻量盯盘池管理折叠抽屉
with st.expander("⚙️ 快速移除 / 管理盯盘股票", expanded=False):
    st.caption("点击下方任意股票胶囊，即可一键移出盯盘池：")
    pill_cols = st.columns(4)
    for p_idx, p_sym in enumerate(st.session_state["my_portfolio"]):
        with pill_cols[p_idx % 4]:
            st.markdown('<div class="remove-pill">', unsafe_allow_html=True)
            if st.button(f"✖ {p_sym}", key=f"remove_pill_{p_sym}", use_container_width=True):
                st.session_state["my_portfolio"].remove(p_sym)
                st.toast(f"已移除 {p_sym}", icon="🗑️")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

cols_p = st.columns(2)
for idx, symbol in enumerate(st.session_state["my_portfolio"]):
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

            with col:
                # 100% 完整一体化无缝卡片
                card_html = (
                    f"<div style='background:#1e293b;border:1px solid #334155;border-radius:14px;padding:16px;margin-bottom:14px;box-shadow:0 8px 16px rgba(0,0,0,0.35);'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>"
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
                st.markdown(card_html, unsafe_allow_html=True)
    except:
        continue

# ================= 7. 模块二：$1 - $100 潜力金股深度调研排行榜 =================
st.markdown("<div style='margin-top:20px;margin-bottom:10px;border-bottom:1px solid #78350f;padding-bottom:6px;'><h3 style='color:#fbbf24;margin:0;font-size:17px;font-weight:800;'>🏆 全自动雷达·潜力金股排行榜 ($1 - $100 深度调研版)</h3><p style='color:#d6d3d1;font-size:11px;margin:2px 0 0 0;'>已包含：公司主营业务赛道 / 核心竞争壁垒 / 中期业绩订单催化剂 / 目标位测算</p></div>", unsafe_allow_html=True)

scanned = []
for sym, profile in RADAR_STOCK_PROFILES.items():
    if sym in st.session_state["my_portfolio"]: continue
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

    with col:
        radar_card_html = (
            f"<div style='background:#1c1917;border:2px solid #b45309;border-radius:14px;padding:16px;margin-bottom:6px;box-shadow:0 8px 16px rgba(0,0,0,0.6);'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;border-bottom:1px solid #451a03;padding-bottom:6px;'>"
            f"<span style='font-size:13px;font-weight:900;color:#fbbf24;background:#451a03;padding:3px 8px;border-radius:6px;border:1px solid #d97706;'>{medals[idx]}</span>"
            f"<span style='font-size:12px;font-weight:bold;color:#fde047;'>{stars}</span>"
            f"</div>"
            f"<div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;'>"
            f"<div><span style='font-size:24px;font-weight:900;color:#ffffff;'>{item['symbol']}</span>"
            f"<span style='font-size:11px;color:#a8a29e;margin-left:6px;'>量化分: <b style='color:#34d399;font-size:14px;'>{item['score']}</b></span></div>"
            f"<div style='text-align:right;'><span style='font-size:20px;font-weight:800;color:#ffffff;'>${item['price']}</span>"
            f"<span style='font-size:12px;font-weight:bold;color:{c};margin-left:4px;'>{s}{item['pct']}%</span></div>"
            f"</div>"
            f"<div style='display:flex;gap:6px;margin-bottom:8px;flex-wrap:wrap;'>"
            f"<span style='background:#064e3b;color:#34d399;font-size:10px;padding:2px 6px;border-radius:4px;font-weight:bold;border:1px solid #059669;'>🛡️ 仅高于底部 {item['safety_pct']}%</span>"
            f"<span style='background:#292524;color:#fde047;font-size:10px;padding:2px 6px;border-radius:4px;border:1px solid #78350f;'>$1-$100 亲民</span>"
            f"</div>"
            f"<div style='font-size:11px;color:#fef3c7;background:#291e10;border:1px solid #78350f;border-radius:8px;padding:8px;margin-bottom:8px;line-height:1.45;'>"
            f"<div style='color:#fbbf24;font-weight:bold;margin-bottom:3px;'>🏢 赛道：{item['sector']}</div>"
            f"<div style='color:#d6d3d1;margin-bottom:3px;'><b style='color:#fde047;'>🛡️ 壁垒：</b>{item['moat']}</div>"
            f"<div style='color:#fef08a;'><b style='color:#f59e0b;'>🚀 催化：</b>{item['catalyst']}</div>"
            f"</div>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#d6d3d1;background:#0c0a09;padding:6px 10px;border-radius:6px;'>"
            f"<span>防守底线: <b style='color:#34d399'>${item['low_20']}</b></span>"
            f"<span>RSI: <b style='color:#fde047;'>{item['rsi']}</b></span>"
            f"<span>目标位: <b style='color:#f87171'>${item['target']} (+28%)</b></span>"
            f"</div>"
            f"</div>"
        )
        st.markdown(radar_card_html, unsafe_allow_html=True)
        
        if st.button(f"⚡ 关注并加入盯盘", key=f"quick_add_{item['symbol']}", use_container_width=True):
            st.session_state["my_portfolio"].append(item['symbol'])
            st.toast(f"已将金股 {item['symbol']} 加入盯盘池！", icon="🚀")
            st.rerun()
        st.write("")
