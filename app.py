import streamlit as st
import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Hệ thống Phân tích Tưới & Phân", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    .main-title { color: #1a5c1a !important; text-align: center; font-weight: bold; border-bottom: 2px solid #2ca02c; padding-bottom: 10px; margin-bottom: 20px; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #333333 !important; font-size: 1rem !important; }
    [data-testid="metric-container"] {
        background-color: #f0f2f6 !important;
        border-radius: 10px !important;
        padding: 10px !important;
        border: 1px solid #ddd !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC PHÂN TÍCH ---
def analyze_data(data, khu_id, cham_phan_id, min_sec, min_freq):
    fmt = "%Y-%m-%d %H-%M-%S"
    
    # Lọc dữ liệu tưới
    du_lieu_tuoi = sorted([d for d in data if str(d.get('STT')) == str(khu_id)], 
                         key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    
    # Lọc dữ liệu châm phân (để lấy EC/pH)
    du_lieu_cp = [d for d in data if str(d.get('STT')) == str(cham_phan_id)]
    
    lan_tuoi_hop_le = []
    daily_stats = {} 
    
    # Xử lý lịch tưới
    for i in range(len(du_lieu_tuoi) - 1):
        h1, h2 = du_lieu_tuoi[i], du_lieu_tuoi[i+1]
        if h1.get('Trạng thái') == "Bật" and h2.get('Trạng thái') == "Tắt":
            try:
                t1, t2 = datetime.strptime(h1['Thời gian'], fmt), datetime.strptime(h2['Thời gian'], fmt)
                if (t2 - t1).total_seconds() >= min_sec:
                    lan_tuoi_hop_le.append(t1)
                    d_str = t1.strftime("%Y-%m-%d")
                    daily_stats[d_str] = daily_stats.get(d_str, 0) + 1
            except: continue

    ngay_hop_le = sorted([datetime.strptime(n, "%Y-%m-%d").date() for n, c in daily_stats.items() if c >= min_freq])
    if not ngay_hop_le: return []

    seasons = []
    if not ngay_hop_le: return seasons
    
    start_date = prev_date = ngay_hop_le[0]
    for i in range(1, len(ngay_hop_le)):
        if (ngay_hop_le[i] - prev_date).days > 2:
            if (prev_date - start_date).days + 1 >= 7:
                # Tính EC/pH trung bình trong khoảng thời gian vụ này
                ec_vals = [float(d['EC']) for d in du_lieu_cp if 'EC' in d and start_date <= datetime.strptime(d['Thời gian'], fmt).date() <= prev_date]
                ph_vals = [float(d['pH']) for d in du_lieu_cp if 'pH' in d and start_date <= datetime.strptime(d['Thời gian'], fmt).date() <= prev_date]
                
                seasons.append({
                    'start': start_date, 'end': prev_date, 'days': (prev_date - start_date).days + 1,
                    'total': sum(1 for d in lan_tuoi_hop_le if start_date <= d.date() <= prev_date),
                    'tbec': round(sum(ec_vals)/len(ec_vals), 2) if ec_vals else 0,
                    'tbph': round(sum(ph_vals)/len(ph_vals), 2) if ph_vals else 0,
                    'stats': {d: daily_stats[d] for d in daily_stats if start_date <= datetime.strptime(d, "%Y-%m-%d").date() <= prev_date}
                })
            start_date = ngay_hop_le[i]
        prev_date = ngay_hop_le[i]
    
    # Vụ cuối
    ec_vals = [float(d['EC']) for d in du_lieu_cp if 'EC' in d and start_date <= datetime.strptime(d['Thời gian'], fmt).date() <= prev_date]
    ph_vals = [float(d['pH']) for d in du_lieu_cp if 'pH' in d and start_date <= datetime.strptime(d['Thời gian'], fmt).date() <= prev_date]
    seasons.append({
        'start': start_date, 'end': prev_date, 'days': (prev_date - start_date).days + 1,
        'total': sum(1 for d in lan_tuoi_hop_le if start_date <= d.date() <= prev_date),
        'tbec': round(sum(ec_vals)/len(ec_vals), 2) if ec_vals else 0,
        'tbph': round(sum(ph_vals)/len(ph_vals), 2) if ph_vals else 0,
        'stats': {d: daily_stats[d] for d in daily_stats if start_date <= datetime.strptime(d, "%Y-%m-%d").date() <= prev_date}
    })
    return seasons

# --- 3. GIAO DIỆN ---
st.markdown("<h1 class='main-title'>DASHBOARD QUẢN LÝ TƯỚI & CHÂM PHÂN</h1>", unsafe_allow_html=True)

st.sidebar.header("📁 Cấu hình hệ thống")
uploaded_file = st.sidebar.file_uploader("Tải file dữ liệu tổng (.json)", type=["json"])

if uploaded_file:
    data = json.load(uploaded_file)
    with st.sidebar:
        st.divider()
        all_stt = sorted(list(set(str(d['STT']) for d in data)))
        khu_val = st.selectbox("STT Khu vực tưới", all_stt, index=0)
        cp_val = st.selectbox("STT Máy châm phân", all_stt, index=min(1, len(all_stt)-1))
        st.divider()
        sec_val = st.slider("Giây tưới tối thiểu", 5, 120, 20)
        freq_val = st.slider("Lần tưới tối thiểu/ngày", 1, 15, 5)

    results = analyze_data(data, khu_val, cp_val, sec_val, freq_val)

    if results:
        for idx, v in enumerate(results):
            st.write(f"### 🌿 CHI TIẾT VỤ {idx+1} ({v['start']} đến {v['end']})")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tổng lần tưới", f"{v['total']} lần")
            c2.metric("Thời gian vụ", f"{v['days']} ngày")
            c3.metric("TB EC", f"{v['tbec']} mS/cm")
            c4.metric("TB pH", f"{v['tbph']}")
            
            dates = sorted(v['stats'].keys())
            counts = [v['stats'][d] for d in dates]
            fig, ax = plt.subplots(figsize=(12, 3))
            ax.bar(dates, counts, color='#2ca02c', alpha=0.7)
            ax.set_ylabel("Số lần tưới/ngày")
            ax.xaxis.set_major_locator(ticker.MaxNLocator(10))
            plt.xticks(rotation=25)
            st.pyplot(fig)
            st.divider()
    else:
        st.warning("Không tìm thấy dữ liệu phù hợp.")
else:
    st.info("Vui lòng tải file JSON để xem báo cáo EC/pH và lịch tưới.")
