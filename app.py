import streamlit as st
import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Hệ thống Phân tích Tưới & Châm Phân", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    .main-title { color: #1a5c1a !important; text-align: center; font-weight: bold; border-bottom: 2px solid #2ca02c; padding-bottom: 10px; margin-bottom: 20px; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-weight: bold !important; font-size: 1.8rem !important; }
    [data-testid="stMetricLabel"] { color: #333333 !important; font-size: 1.1rem !important; }
    [data-testid="metric-container"] {
        background-color: #f8f9fa !important;
        border-radius: 12px !important;
        padding: 20px !important;
        border: 1px solid #e9ecef !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC PHÂN TÍCH TỐI ƯU ---
def analyze_data(data, khu_id, cp_id, min_sec, min_freq):
    fmt = "%Y-%m-%d %H-%M-%S"
    
    # 1. Lọc dữ liệu tưới (chỉ lấy trạng thái Bật/Tắt của Khu vực)
    du_lieu_tuoi = sorted([d for d in data if str(d.get('STT')) == str(khu_id)], 
                         key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    
    # 2. Lọc dữ liệu châm phân (chỉ lấy EC và pH)
    du_lieu_cp = [d for d in data if str(d.get('STT')) == str(cp_id)]
    
    lan_tuoi_hop_le = []
    daily_counts = {} 
    
    # Xử lý logic bật/tắt để xác định các lần tưới
    for i in range(len(du_lieu_tuoi) - 1):
        h1, h2 = du_lieu_tuoi[i], du_lieu_tuoi[i+1]
        if h1.get('Trạng thái') == "Bật" and h2.get('Trạng thái') == "Tắt":
            try:
                t1, t2 = datetime
