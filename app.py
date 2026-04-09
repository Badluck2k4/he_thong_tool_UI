import streamlit as st
import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Phân tích Giai đoạn Tưới & Châm Phân", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    .main-title { color: #1a5c1a !important; text-align: center; font-weight: bold; border-bottom: 2px solid #2ca02c; padding-bottom: 10px; margin-bottom: 20px; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-weight: bold !important; }
    [data-testid="metric-container"] {
        background-color: #f8f9fa !important;
        border-radius: 12px !important;
        padding: 15px !important;
        border: 1px solid #e9ecef !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC PHÂN TÍCH ---
def analyze_full_data(data, khu_id, cp_id, min_sec, min_freq):
    fmt = "%Y-%m-%d %H-%M-%S"
    du_lieu_tuoi = sorted([d for d in data if str(d.get('STT')) == str(khu_id)], key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    du_lieu_cp = [d for d in data if str(d.get('STT')) == str(cp_id)]
    
    lan_tuoi_hop_le = []
    daily_counts = {} 
    for i in range(len(du_lieu_tuoi) - 1):
        h1, h2 = du_lieu_tuoi[i], du_lieu_tuoi[i+1]
        if h1.get('Trạng thái') == "Bật" and h2.get('Trạng thái') == "Tắt":
            try:
                t1, t2 = datetime.strptime(h1['Thời gian'], fmt), datetime.strptime(h2['Thời gian'], fmt)
                if (t2 - t1).total_seconds() >= min_sec:
                    lan_tuoi_hop_le.append(t1)
                    d_str = t1.strftime("%Y-%m-%d")
                    daily_counts[d_str] = daily_counts.get(d_str, 0) + 1
            except: continue

    ngay_chuan = sorted([datetime.strptime(n, "%Y-%m-%d").date() for n, c in daily_counts.items() if c >= min_freq])
    if not ngay_chuan: return []

    seasons = []
    start_date = prev_date = ngay_chuan[0]
    
    def extract_stats(s_d, e_d):
        daily_ec = {}
        daily_ph = {}
        for d in du_lieu_cp:
            try:
                dt = datetime.strptime(d['Thời gian'], fmt)
                if s_d <= dt.date() <= e_d:
                    ds = dt.strftime("%Y-%m-%d")
                    if 'EC' in d: daily_ec.setdefault(ds, []).append(float(d['EC']))
                    if 'pH' in d: daily_ph.setdefault(ds, []).append(float(d['pH']))
            except: continue
        
        # Tính trung bình mỗi ngày để vẽ biểu đồ đường
        avg_ec = {k: sum(v)/len(v) for k, v in daily_ec.items()}
        avg_ph = {k: sum(v)/len(v) for k, v in daily_ph.items()}
        
        all_ec = [v for l in daily_ec.values() for v in l]
        all_ph = [v for l in daily_ph.values() for v in l]

        return {
            'start': s_d, 'end': e_d, 'days': (e_d - s_d).days + 1,
            'total_irr': sum(1 for d in lan_tuoi_hop_le if s_d <= d.date() <= e_d),
            'tbec': round(sum(all_ec)/len(all_ec), 2) if all_ec else 0,
            'tbph': round(sum(all_ph)/len(all_ph), 2) if all_ph else 0,
            'daily_counts': {d: daily_counts[d] for d in daily_counts if s_d <= datetime.strptime(d, "%Y-%m-%d").date() <= e_d},
            'daily_ec': avg_ec, 'daily_ph': avg_ph
        }

    for i in range(1, len(ngay_chuan)):
        if (ngay_chuan[i] - prev_date).days > 2:
            if (prev_date - start_date).days + 1 >= 7:
                seasons.append(extract_stats(start_date, prev_date))
            start_date = ngay_chuan[i]
        prev_date = ngay_chuan[i]
    seasons.append(extract_stats(start_date, prev_date))
    return seasons

# --- 3. GIAO DIỆN ---
st.markdown("<h1 class='main-title'>PHÂN TÍCH GIAI ĐOẠN DINH DƯỠNG & TƯỚI</h1>", unsafe_allow_html=True)

st.sidebar.header("📁 Tải dữ liệu")
files = st.sidebar.file_uploader("Chọn các file JSON (Tưới + Châm phân)", type=["json"], accept_multiple_files=True)

if files:
    all_data = []
    for f in files:
        js = json.load(f)
        all_data.extend(js) if isinstance(js, list) else all_data.append(js)
            
    with st.sidebar:
        ids = sorted(list(set(str(d['STT']) for d in all_data if 'STT' in d)))
        khu_id = st.selectbox("STT Khu vực tưới", ids, index=0)
        cp_id = st.selectbox("STT Máy châm phân", ids, index=min(1, len(ids)-1))
        st.divider()
        sec_min = st.slider("Giây tưới tối thiểu", 5, 120, 20)
        freq_min = st.slider("Lần tưới/ngày tối thiểu", 1, 15, 5)

    results = analyze_full_data(all_data, khu_id, cp_id, sec_min, freq_min)

    for idx, v in enumerate(results):
        with st.expander(f"📊 GIAI ĐOẠN {idx+1}: Từ {v['start']} đến {v['end']}", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tổng lần tưới", f"{v['total_irr']} lần")
            c2.metric("Số ngày", f"{v['days']} ngày")
            c3.metric("TB EC", f"{v['tbec']} mS")
            c4.metric("TB pH", f"{v['tbph']}")
            
            # Biểu đồ kết hợp
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
            
            # Biểu đồ cột: Tần suất tưới
            dates = sorted(v['daily_counts'].keys())
            counts = [v['daily_counts'][d] for d in dates]
            ax1.bar(dates, counts, color='#2ca02c', alpha=0.3, label='Lần tưới/ngày')
            ax1.set_ylabel("Tần suất tưới")
            ax1.legend(loc='upper left')
            
            # Biểu đồ đường: EC và pH
            ec_dates = sorted(v['daily_ec'].keys())
            ax2.plot(ec_dates, [v['daily_ec'][d] for d in ec_dates], color='blue', marker='o', label='Biến động EC')
            ax2.set_ylabel("Chỉ số EC (mS/cm)", color='blue')
            
            ax3 = ax2.twinx()
            ph_dates = sorted(v['daily_ph'].keys())
            ax3.plot(ph_dates, [v['daily_ph'][d] for d in ph_dates], color='red', marker='s', linestyle='--', label='Biến động pH')
            ax3.set_ylabel("Chỉ số pH", color='red')
            
            plt.xticks(rotation=30)
            ax2.legend(loc='upper left')
            ax3.legend(loc='upper right')
            st.pyplot(fig)
else:
    st.info("💡 Vui lòng tải file để bắt đầu phân tích giai đoạn.")
