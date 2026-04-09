import streamlit as st
import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime

# --- 1. CẤU HÌNH GIAO DIỆN WEB ---
st.set_page_config(page_title="Hệ thống Phân tích Tưới", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-title { color: #2ca02c; text-align: center; font-weight: bold; border-bottom: 2px solid #2ca02c; padding-bottom: 10px; margin-bottom: 20px; }
    .stMetric { background-color: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
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
                t2 = datetime.strptime(h2['Thời gian'], fmt)
                duration = (t2 - t1).total_seconds()
                if duration >= min_sec:
                    lan_tuoi_hop_le.append(t1)
                    d_str = t1.strftime("%Y-%m-%d")
                    daily_raw[d_str] = daily_raw.get(d_str, 0) + 1
            except: continue

    ngay_hop_le = sorted([datetime.strptime(n, "%Y-%m-%d").date() for n, c in daily_raw.items() if c >= min_freq])
    if not ngay_hop_le: return []

    seasons = []
    start_date = prev_date = ngay_hop_le[0]
    for i in range(1, len(ngay_hop_le)):
        if (ngay_hop_le[i] - prev_date).days > 2:
            if (prev_date - start_date).days + 1 >= 7:
                total = sum(1 for d in lan_tuoi_hop_le if start_date <= d.date() <= prev_date)
                seasons.append({'start': start_date, 'end': prev_date, 'days': (prev_date - start_date).days + 1, 'total': total, 
                                'stats': {d: daily_raw[d] for d in daily_raw if start_date <= datetime.strptime(d, "%Y-%m-%d").date() <= prev_date}})
            start_date = ngay_hop_le[i]
        prev_date = ngay_hop_le[i]
    
    if (prev_date - start_date).days + 1 >= 7:
        total = sum(1 for d in lan_tuoi_hop_le if start_date <= d.date() <= prev_date)
        seasons.append({'start': start_date, 'end': prev_date, 'days': (prev_date - start_date).days + 1, 'total': total, 
                        'stats': {d: daily_raw[d] for d in daily_raw if start_date <= datetime.strptime(d, "%Y-%m-%d").date() <= prev_date}})
    return seasons

# --- 3. GIAO DIỆN HIỂN THỊ ---
st.markdown("<h1 class='main-title'>DASHBOARD PHÂN TÍCH TƯỚI NHO GIỌT</h1>", unsafe_allow_html=True)

st.sidebar.header("📁 Dữ liệu đầu vào")
uploaded_file = st.sidebar.file_uploader("Tải file JSON dữ liệu", type=["json"])

if uploaded_file is not None:
    data = json.load(uploaded_file)
    with st.sidebar:
        st.divider()
        st.header("⚙️ Cấu hình bộ lọc")
        khu_list = sorted(list(set(str(d['STT']) for d in data)))
        khu_val = st.selectbox("Chọn Khu vực (STT)", khu_list)
        sec_val = st.slider("Thời gian tưới tối thiểu (giây)", 5, 120, 20)
        freq_val = st.slider("Số lần tưới tối thiểu/ngày", 1, 15, 5)

    results = analyze_irrigation(data, khu_val, sec_val, freq_val)

    if results:
        st.subheader("📌 Tóm tắt các mùa vụ")
        cols = st.columns(len(results))
        for idx, v in enumerate(results):
            with cols[idx]:
                st.metric(label=f"VỤ {idx+1}", value=f"{v['total']} lần", delta=f"{v['days']} ngày")
                st.caption(f"Từ {v['start']} đến {v['end']}")

        st.divider()
        for idx, v in enumerate(results):
            st.write(f"### 📈 Biểu đồ tần suất Vụ {idx+1}")
            dates = sorted(v['stats'].keys())
            counts = [v['stats'][d] for d in dates]
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.bar(dates, counts, color='#2ca02c')
            ax.axhline(y=freq_val, color='red', linestyle='--', alpha=0.3)
            ax.xaxis.set_major_locator(ticker.MaxNLocator(12))
            plt.xticks(rotation=30)
            st.pyplot(fig)
    else:
        st.warning("Không tìm thấy vụ nào đạt tiêu chuẩn lọc.")
else:
    st.info("Vui lòng tải file dữ liệu JSON ở thanh bên trái để bắt đầu.")
