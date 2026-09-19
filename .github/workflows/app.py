"""app.py

Streamlit 網頁儀表板主程式
執行方式：streamlit run app.py
"""

from apscheduler.schedulers.background import BackgroundScheduler
import monitor_engine as engine
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="半導體評價領先指標週報 | Buy-Side Monitor",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------
# 初始化背景定時排程（每週六上午 08:00 自動執行）
# -------------------------------------------------------------


@st.cache_resource
def start_scheduler():
  scheduler = BackgroundScheduler(timezone="Asia/Taipei")

  def scheduled_job():
    rec = engine.evaluate_indicators()
    engine.save_record(rec)

  # 每週六早上 08:00 執行
  scheduler.add_job(scheduled_job, "cron", day_of_week="sat", hour=8, minute=0)
  scheduler.start()
  return scheduler


start_scheduler()

# -------------------------------------------------------------
# 頁面標題與控制列
# -------------------------------------------------------------
st.markdown("""
    <style>
        .metric-card {
            border-radius: 10px;
            padding: 16px;
            background-color: #1E222D;
            border: 1px solid #2A2E39;
        }
        .status-badge {
            font-size: 20px;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 6px;
            display: inline-block;
        }
        .status-GREEN { background-color: #137333; color: #E6F4EA; }
        .status-YELLOW { background-color: #B06000; color: #FEF7E0; }
        .status-RED { background-color: #C5221F; color: #FCE8E6; }
    </style>
""", unsafe_allow_html=True)

history_data = engine.load_history()
latest = history_data[-1]

col_title, col_btn = st.columns([4, 1])
with col_title:
  st.title("🏛️ 美國 CSP 資本支出與半導體本益比領先監控儀表板")
  st.caption(
      f"每週六自動更新機制 | 追蹤週期：2026~2027 ROIC 關鍵探底期 |"
      f" 最新更新日期：{latest['date']}"
  )

with col_btn:
  st.write("")
  if st.button("🔄 手動觸發更新資料", use_container_width=True):
    new_rec = engine.evaluate_indicators()
    engine.save_record(new_rec)
    st.success("最新數據已重新計算並入庫！")
    st.rerun()

st.divider()

# -------------------------------------------------------------
# 1. 頂部總結：當週綜合評級與操作指引
# -------------------------------------------------------------
status_class = f"status-{latest['overall']}"
banner_html = f"""
<div class="metric-card" style="margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="font-size: 16px; color: #9AA0A6;">當週買方總合評級：</span>
            <span class="status-badge {status_class}">{latest['overall']} ALERT</span>
        </div>
        <div style="font-size: 14px; color: #9AA0A6;">
            目標調倉策略：<strong style="color: #FFFFFF;">{latest['action']}</strong>
        </div>
    </div>
</div>
"""
st.markdown(banner_html, unsafe_allow_html=True)

# -------------------------------------------------------------
# 2. 三大領先指標當週狀態卡片
# -------------------------------------------------------------
st.subheader("📊 三大核心指標每週監控檢驗")
c1, c2, c3 = st.columns(3)

with c1:
  st.markdown(f"""
    <div class="metric-card">
        <h4 style="color: #8AB4F8; margin-bottom: 8px;">1. 先進封裝 (CoWoS) 交期</h4>
        <h2 style="margin: 0;">{latest['cowos_weeks']} <span style="font-size: 18px; color: #9AA0A6;">週</span></h2>
        <p style="margin-top: 8px; color: #DADCE0; font-size: 13px;">{latest['cowos_desc']}</p>
        <span class="status-badge status-{latest['cowos_status']}" style="font-size: 12px; padding: 2px 8px;">{latest['cowos_status']}</span>
    </div>
    """, unsafe_allow_html=True)

with c2:
  st.markdown(f"""
    <div class="metric-card">
        <h4 style="color: #8AB4F8; margin-bottom: 8px;">2. CSP 資本沉澱剪刀差</h4>
        <h2 style="margin: 0;">+{latest['scissor_pct']} <span style="font-size: 18px; color: #9AA0A6;">%</span></h2>
        <p style="margin-top: 8px; color: #DADCE0; font-size: 13px;">{latest['scissor_desc']}</p>
        <span class="status-badge status-{latest['scissor_status']}" style="font-size: 12px; padding: 2px 8px;">{latest['scissor_status']}</span>
    </div>
    """, unsafe_allow_html=True)

with c3:
  st.markdown(f"""
    <div class="metric-card">
        <h4 style="color: #8AB4F8; margin-bottom: 8px;">3. GPU 現貨租金 (B200/hr)</h4>
        <h2 style="margin: 0;">${latest['gpu_rent']} <span style="font-size: 18px; color: #9AA0A6;">/hr</span></h2>
        <p style="margin-top: 8px; color: #DADCE0; font-size: 13px;">{latest['gpu_desc']}</p>
        <span class="status-badge status-{latest['gpu_status']}" style="font-size: 12px; padding: 2px 8px;">{latest['gpu_status']}</span>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# -------------------------------------------------------------
# 3. 本益比目標估值矩陣
# -------------------------------------------------------------
st.subheader("🎯 次週目標本益比 (Target Forward P/E) 矩陣")
col_pe1, col_pe2, col_pe_desc = st.columns([1.5, 1.5, 3])

with col_pe1:
  st.metric(label="台積電 (2330.TW) 目標 P/E", value=latest["pe_tsmc"])
with col_pe2:
  st.metric(label="NVIDIA (NVDA) 目標 P/E", value=latest["pe_nvda"])
with col_pe_desc:
  st.info(f"""
    **調倉執行指引：**  
    當前狀態為 **[{latest['overall']}]**。  
    - 若持股本益比高於上述目標區間上限，建議啟動階段性獲利了結或布局避險空單。  
    - 若全數指標落於綠燈，可維持上限評價並全額持倉先進製程代工與伺服器主板龍頭。
    """)

st.divider()

# -------------------------------------------------------------
# 4. 歷史軌跡圖表分析
# -------------------------------------------------------------
st.subheader("📈 領先指標歷史趨勢折線圖")

df = pd.DataFrame(history_data)

tab1, tab2 = st.tabs(["在建資產 vs 雲端營收剪刀差走勢", "CoWoS 交期與算力租金走勢"])

with tab1:
  fig_scissor = px.line(
      df,
      x="date",
      y="scissor_pct",
      title="CSP 資本沉澱剪刀差走勢 (CIP 成長率 - 雲端營收成長率 %)",
      markers=True,
      labels={"date": "追蹤日期", "scissor_pct": "剪刀差 (%)"},
  )
  # 添加警戒線
  fig_scissor.add_hline(
      y=10.0,
      line_dash="dot",
      line_color="#F9AB00",
      annotation_text="黃燈警戒線 (10%)",
  )
  fig_scissor.add_hline(
      y=20.0,
      line_dash="dash",
      line_color="#EA4335",
      annotation_text="紅燈危險線 (20%)",
  )
  fig_scissor.update_layout(template="plotly_dark", height=380)
  st.plotly_chart(fig_scissor, use_container_width=True)

with tab2:
  fig_combo = go.Figure()
  fig_combo.add_trace(
      go.Scatter(
          x=df["date"],
          y=df["cowos_weeks"],
          name="CoWoS 交期 (週)",
          line=dict(color="#8AB4F8", width=3),
      )
  )
  fig_combo.add_trace(
      go.Scatter(
          x=df["date"],
          y=df["gpu_rent"],
          name="GPU 批發租金 ($/hr)",
          yaxis="y2",
          line=dict(color="#81C995", width=3),
      )
  )

  fig_combo.update_layout(
      title="先進封裝交期 vs GPU 現貨租金歷史連動",
      xaxis=dict(title="日期"),
      yaxis=dict(title="CoWoS 交期 (週)"),
      yaxis2=dict(title="租金 ($/hr)", overlaying="y", side="right"),
      template="plotly_dark",
      height=380,
  )
  st.plotly_chart(fig_combo, use_container_width=True)