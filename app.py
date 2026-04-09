import streamlit as st
import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime

# --- 1. CẤU HÌNH GIAO DIỆN WEB (FIX LỖI CHỮ MỜ) ---
st.set_page_config(page_title="Hệ thống Phân tích Tưới", layout="wide")

# Đoạn CSS này giúp chữ luôn đen và nền luôn sáng để dễ đọc trong Dark Mode
st.markdown("""
    <style>
    /* Nền chính của App */
    .stApp { background-color: #ffffff !important; }
    
    /* Tiêu đề chính */
    .main-title { color: #1a5c1a !important; text-align: center; font-weight: bold; border-bottom: 2px solid #2ca02c; padding-bottom: 10px; margin-bottom: 20px; }
    
    /* Ép buộc tất cả chữ trong các ô Metric phải là màu đen */
    [data-testid="stMetricValue"] { color: #000000 !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #333333 !important; font-size: 1.1rem !important; }
    [data-testid="stMetricDelta"] { font-weight: bold !important; }
    
    /* Bo góc và đổ bóng cho các ô chỉ số */
    [data-testid="metric-container"] {
        background-color: #f0f2f6 !important;
        border-radius: 10px !important;
        padding: 15px !important;
        border: 1px solid #ddd !important;
    }
    
    /* Fix chữ trong Sidebar */
    .css-1d391kg, .st-emotion-cache-16idsys p { color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM XỬ LÝ LOGIC ---
def analyze_irrigation(data, khu_id, min_sec, min_freq):
    stt_str = str(khu_id)
    fmt = "%Y-%m-%d %H-%M-%S"
    
    du_lieu_khu = sorted([d for d in data if str(d.get('STT')) == stt_str], 
                        key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    
    lan_tuoi_hop_le = []
    daily_raw = {} 
    
    for i in range(len(du_lieu_khu) - 1):
        h1, h2 = du_lieu_khu[i], du_lieu_khu[i+1]
        if h1.get('Trạng thái') == "Bật" and h2.get('Trạng thái') == "Tắt":
            try:
                t1 = datetime.strptime(h1['Thời gian'], fmt)
                t2 = datetime.strptime(h2['Thời gian'], fmt
