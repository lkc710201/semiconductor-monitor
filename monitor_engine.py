"""monitor_engine.py

負責指標計算、評級判定與歷史資料讀寫
"""

from datetime import datetime
import json
import os
import numpy as np
import pandas as pd

HISTORY_FILE = "weekly_history.json"


def evaluate_indicators(lead_time=38.0, cip_growth=38.2, cloud_rev_growth=26.4, gpu_rent=5.20, gpu_mom=-2.1):
  """計算當週三大指標數值與燈號"""
  # 1. CoWoS 交期
  if lead_time >= 36:
    s1 = "GREEN"
    d1 = f"交期 {lead_time} 週（>=36週），先進封裝產能維持超額預定。"
  elif lead_time >= 20:
    s1 = "YELLOW"
    d1 = f"交期收斂至 {lead_time} 週，需警戒長約鬆動。"
  else:
    s1 = "RED"
    d1 = f"交期降至 {lead_time} 週（<20週），擴產產能出現過剩風險。"

  # 2. CSP 資本沉澱剪刀差
  scissor = round(cip_growth - cloud_rev_growth, 1)
  if scissor < 10.0:
    s2 = "GREEN"
    d2 = f"剪刀差 +{scissor}%（<10%），硬體通電變現順暢。"
  elif scissor <= 20.0:
    s2 = "YELLOW"
    d2 = f"剪刀差 +{scissor}%（10%~20%），北美電網併網遞延，機房待機堆積。"
  else:
    s2 = "RED"
    d2 = f"剪刀差 +{scissor}%（>20%），伺服器滯留庫存過高，ROIC 稀釋嚴重。"

  # 3. GPU 租金與定價權
  if gpu_rent >= 5.0 and gpu_mom > -5.0:
    s3 = "GREEN"
    d3 = f"租金 ${gpu_rent}/hr，月增率 {gpu_mom}%，晶片商具強烈定價溢價。"
  elif gpu_rent >= 3.5 or gpu_mom >= -15.0:
    s3 = "YELLOW"
    d3 = f"租金 ${gpu_rent}/hr，月變動 {gpu_mom}%，CSP 加速導入自研 ASIC。"
  else:
    s3 = "RED"
    d3 = f"租金跌破 ${gpu_rent}/hr（<$3.5），定價溢價歸零。"

  # 總合評定
  statuses = [s1, s2, s3]
  if "RED" in statuses:
    overall = "RED"
    action = "啟動逆戴維斯雙殺避險機制，調降持倉至 40%~50%，轉向高現金流防禦標的。"
    pe_tsmc, pe_nvda = "16x ~ 18x", "18x ~ 22x"
  elif "YELLOW" in statuses:
    overall = "YELLOW"
    action = "黃燈警戒：凍結部位加碼，維持 70%~80% 持股，增配高 TCO 優勢之 ASIC 族群。"
    pe_tsmc, pe_nvda = "20x ~ 24x", "25x ~ 30x"
  else:
    overall = "GREEN"
    action = "全面多頭：維持 95%~100% 持股水位，超額配置先進封裝與 GPU 族群。"
    pe_tsmc, pe_nvda = "26x ~ 30x", "35x ~ 40x"

  record = {
      "date": datetime.now().strftime("%Y-%m-%d"),
      "overall": overall,
      "action": action,
      "pe_tsmc": pe_tsmc,
      "pe_nvda": pe_nvda,
      "cowos_weeks": lead_time,
      "cowos_status": s1,
      "cowos_desc": d1,
      "scissor_pct": scissor,
      "scissor_status": s2,
      "scissor_desc": d2,
      "gpu_rent": gpu_rent,
      "gpu_status": s3,
      "gpu_desc": d3,
  }
  return record


def save_record(record):
  """儲存當週資料至歷史 JSON"""
  history = load_history()
  # 避免同一天重複存入
  history = [h for h in history if h["date"] != record["date"]]
  history.append(record)
  with open(HISTORY_FILE, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)


def load_history():
  """讀取歷史資料；若無資料則初始化一組基礎模擬資料"""
  if not os.path.exists(HISTORY_FILE):
    # 預載過去 8 週模擬歷史
    mock_dates = pd.date_range(end=datetime.now(), periods=8, freq="W-SAT")
    mock_data = []
    for d in mock_dates:
      d_str = d.strftime("%Y-%m-%d")
      mock_data.append({
          "date": d_str,
          "overall": "YELLOW" if d == mock_dates[-1] else "GREEN",
          "action": (
              "黃燈警戒：凍結部位加碼，維持 70%~80% 持股。"
              if d == mock_dates[-1]
              else "全面多頭：維持 95%~100% 持股水位。"
          ),
          "pe_tsmc": "20x ~ 24x" if d == mock_dates[-1] else "26x ~ 30x",
          "pe_nvda": "25x ~ 30x" if d == mock_dates[-1] else "35x ~ 40x",
          "cowos_weeks": 40.0 if d != mock_dates[-1] else 38.0,
          "cowos_status": "GREEN",
          "cowos_desc": "產能滿載",
          "scissor_pct": 7.5 if d != mock_dates[-1] else 11.8,
          "scissor_status": "GREEN" if d != mock_dates[-1] else "YELLOW",
          "scissor_desc": "剪刀差正常",
          "gpu_rent": 5.30 if d != mock_dates[-1] else 5.20,
          "gpu_status": "GREEN",
          "gpu_desc": "租金穩定",
      })
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
      json.dump(mock_data, f, ensure_ascii=False, indent=2)
    return mock_data

  with open(HISTORY_FILE, "r", encoding="utf-8") as f:
    return json.load(f)
