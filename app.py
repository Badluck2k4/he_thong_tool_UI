import streamlit as st
import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime

# --- 1. CẤU HÌNH GIAO DIỆN WEB ---
st.set_page_config(page_title="Hệ thống Phân tích Tưới", layout="wide")

# CSS để giao diện trông hiện đại hơn
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-title { color: #2ca02c; text-align: center; font-weight: bold; border-bottom: 2px solid #2ca02c; padding-bottom: 10px; margin-bottom: 20px; }
    .stMetric { background-color: white; border-radius: 10px; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM XỬ LÝ LOGIC (KHÔNG DÙNG PANDAS) ---
def analyze_irrigation(data, khu_id, min_sec, min_freq):
    stt_str = str(khu_id)
    fmt = "%Y-%m-%d %H-%M-%S"
    
    # Lọc dữ liệu theo Khu vực và sắp xếp thời gian
    du_lieu_khu = sorted([d for d in data if str(d.get('STT')) == stt_str], 
                        key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    
    lan_tuoi_hop_le = []
    daily_raw = {} 
    
    for i in range(len(du_lieu_khu) - 1):
        h1, h2 = du_lieu_khu[i], du_lieu_khu[i+1]
        if h1.get('Trạng thái') == "Bật" and h2.get('Trạng thái') == "Tắt":
            try:
                t1 = datetime.strptime(h1['Thời gian'], fmt)
                t2 = datetime.strptime(h2['Thời gian'], fmt)
                duration = (t2 - t1).total_seconds()
                
                if duration >= min_sec:
                    lan_tuoi_hop_le.append(t1)
                    d_str = t1.strftime("%Y-%m-%d")
                    daily_raw[d_str] = daily_raw.get(d_str, 0) + 1
            except:
                continue

    # Phân vụ dựa trên mật độ tưới
    ngay_hop_le = sorted([datetime.strptime(n, "%Y-%m-%d").date() for n, c in daily_raw.items() if c >= min_freq])
    if not ngay_hop_le: return []

    seasons = []
    start_date = prev_date = ngay_hop_le[0]
    
    for i in range(1, len(ngay_hop_le)):
        # Nếu nghỉ quá 2 ngày thì coi như ngắt vụ
        if (ngay_hop_le[i] - prev_date).days > 2:
            if (prev_date - start_date).days + 1 >= 7:
                total = sum(1 for d in lan_tuoi_hop_le if start_date <= d.date() <= prev_date)
                seasons.append({
                    'start': start_date, 'end': prev_date, 
                    'days': (prev_date - start_date).days + 1, 'total': total, 
                    'stats': {d: daily_raw[d] for d in daily_raw if start_date <= datetime.strptime(d, "%Y-%m-%d").date() <= prev_date}
                })
            start_date = ngay_hop_le[i]
        prev_date = ngay_hop_le[i]
    
    # Xử lý vụ cuối cùng
    if (prev_date - start_date).days + 1 >= 7:
        total = sum(1 for d in lan_tuoi_hop_le if start_date <= d.date() <= prev_date)
        seasons.append({
            'start': start_date, 'end': prev_date, 
            'days': (prev_date - start_date).days + 1, 'total': total, 
            'stats': {d: daily_raw[d] for d in daily_raw if start_date <= datetime.strptime(d, "%Y-%m-%d").date() <= prev_date}
        })
    return seasons

# --- 3. GIAO DIỆN HIỂN THỊ TRÊN WEB ---
st.markdown("<h1 class='main-title'>DASHBOARD PHÂN TÍCH TƯỚI NHO GIỌT</h1>", unsafe_allow_html=True)

# Thanh bên điều khiển
st.sidebar.header("📁 Dữ liệu đầu vào")
uploaded_file = st.sidebar.file_uploader("Tải file Lich nho giotj.json", type=["json"])

if uploaded_file is not None:
    # Đọc file JSON trực tiếp từ trình duyệt
    data = json.load(uploaded_file)
    
    with st.sidebar:
        st.divider()
        st.header("⚙️ Cấu hình bộ lọc")
        khu_list = sorted(list(set(str(d['STT']) for d in data)))
        khu_val = st.selectbox("Chọn Khu vực (STT)", khu_list, index=0)
        sec_val = st.slider("Thời gian tưới tối thiểu (giây)", 5, 120, 20)
        freq_val = st.slider("Số lần tưới tối thiểu/ngày", 1, 15, 5)

    # Thực hiện phân tích
    results = analyze_irrigation(data, khu_val, sec_val, freq_val)

    if results:
        # Hiển thị tóm tắt các vụ (Stat Cards)
        st.subheader("📌 Tóm tắt các mùa vụ")
        cols = st.columns(len(results))
        for idx, v in enumerate(results):
            with cols[idx]:
                # Hiển thị tóm tắt các vụ (Stat Cards)
        st.subheader("📌 Tóm tắt các mùa vụ")
        cols = st.columns(len(results))
        for idx, v in enumerate(results):
            with cols[idx]:
                # Đảm bảo đóng đủ dấu ngoặc đơn ) ở cuối dòng này
                st.metric(label=f"VỤ {idx+1}", value=f"{v['total']} lần", delta=f"{v['days']} ngày")
                st.caption(f"Từ {v['start']} đến {v['end']}")
