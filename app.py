import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Thử nghiệm Chia Giai đoạn EC", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .main-title { color: #1a5c1a; text-align: center; font-weight: bold; border-bottom: 2px solid #2ca02c; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>HỆ THỐNG THỬ NGHIỆM CHIA GIAI ĐOẠN EC</h1>", unsafe_allow_html=True)

# --- 2. LOGIC PHÂN TÍCH ---
def process_data(data, mode, khu_id, cp_id, freq_threshold=3):
    fmt = "%Y-%m-%d %H-%M-%S"
    # Lọc dữ liệu máy châm phân
    cp = sorted([d for d in data if str(d.get('STT')) == str(cp_id)], 
                key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    
    if not cp: return []

    # Gom nhóm theo ngày để tính tần suất tưới
    daily_counts = {}
    for d in cp:
        dt = datetime.strptime(d['Thời gian'], fmt).date()
        daily_counts[dt] = daily_counts.get(dt, 0) + 1

    seasons = []
    current_group = [cp[0]]

    for i in range(1, len(cp)):
        prev, curr = cp[i-1], cp[i]
        t_prev = datetime.strptime(prev['Thời gian'], fmt)
        t_curr = datetime.strptime(curr['Thời gian'], fmt)
        is_break = False

        # --- CÁCH 1: BIẾN ĐỘNG TẦN SUẤT ---
        if mode == "Biến động Tần suất":
            c_prev = daily_counts.get(t_prev.date(), 0)
            c_curr = daily_counts.get(t_curr.date(), 0)
            if abs(c_curr - c_prev) >= freq_threshold or (t_curr - t_prev).days > 2:
                is_break = True

        # --- CÁCH 2: EC KẾ HOẠCH ---
        elif mode == "EC Kế hoạch":
            if curr.get("EC yêu cầu") != prev.get("EC yêu cầu"):
                is_break = True

        # --- CÁCH 3: EC THỰC TẾ ---
        elif mode == "EC Thực tế":
            if abs(float(curr.get("TBEC", 0)) - float(prev.get("TBEC", 0))) > 30:
                is_break = True

        if is_break:
            seasons.append(current_group)
            current_group = [curr]
        else:
            current_group.append(curr)
    
    seasons.append(current_group)
    return seasons

# --- 3. HIỂN THỊ ---
uploaded_files = st.sidebar.file_uploader("Tải file JSON", type=["json"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for f in uploaded_files:
        content = json.load(f)
        all_data.extend(content) if isinstance(content, list) else all_data.append(content)

    with st.sidebar:
        st.divider()
        mode = st.radio("Chọn logic chia giai đoạn:", ["Biến động Tần suất", "EC Kế hoạch", "EC Thực tế"])
        ids = sorted(list(set(str(d['STT']) for d in all_data if 'STT' in d)))
        cp_id = st.selectbox("Chọn STT Máy châm phân", ids, index=0)
        st.divider()
        st.caption("Cài đặt ngưỡng ngắt (cho Tần suất)")
        threshold = st.slider("Độ lệch lần tưới/ngày", 1, 10, 3)

    seasons_data = process_data(all_data, mode, None, cp_id, threshold)

    for idx, group in enumerate(seasons_data):
        start_t = group[0]['Thời gian']
        end_t = group[-1]['Thời gian']
        
        real_vals = [float(d.get('TBEC', 0)) for d in group]
        target_vals = [float(d.get('EC yêu cầu', 0)) for d in group]
        
        avg_r = sum(real_vals)/len(real_vals)
        avg_t = sum(target_vals)/len(
