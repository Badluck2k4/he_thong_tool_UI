import streamlit as st
import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime

# --- CẤU HÌNH CỐ ĐỊNH ---
MIN_DURATION_SECONDS = 20
MIN_PUMP_PER_DAY = 5
MAX_GAP_DAYS = 2
MIN_SEASON_DURATION = 7

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Phân tích tưới nhỏ giọt", layout="wide")
st.title("💧 Hệ Thống Phân Tích Mùa Vụ Tối Ưu")

# Sidebar
st.sidebar.header("Dữ liệu đầu vào")
FILE_UPLOAD = st.sidebar.file_uploader("Chọn file 'Lich nho giotj.json'", type=['json'])
KHU_VUC_ID_INPUT = st.sidebar.number_input("ID Khu Vực cần phân tích", value=2)

def ve_bieu_do_don(vu_chon, stt_vu):
    """Vẽ biểu đồ cho duy nhất 1 vụ được chọn"""
    stats = vu_chon['daily_stats']
    dates = sorted(stats.keys())
    counts = [s['count'] for s in [stats[d] for d in dates]]
    
    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.bar(dates, counts, color='#2ca02c', edgecolor='white', alpha=0.85)
    ax.axhline(y=MIN_PUMP_PER_DAY, color='red', linestyle='--', alpha=0.4, label='Ngưỡng tối thiểu')

    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
    ax.set_title(f"BIỂU ĐỒ CHI TIẾT VỤ {stt_vu}", fontsize=14, fontweight='bold')
    ax.set_ylabel("Số lần tưới")
    ax.tick_params(axis='x', rotation=30)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.legend()

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1, f'{int(height)}',
                ha='center', va='bottom', fontsize=9)
    
    st.pyplot(fig)

def thuc_thi_tong_hop(data_lich):
    stt_chuoi = str(KHU_VUC_ID_INPUT)
    fmt = "%Y-%m-%d %H-%M-%S"

    # 1. Lọc và tính toán thời gian tưới
    du_lieu_khu = sorted([d for d in data_lich if d.get('STT') == stt_chuoi],
                        key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    
    lan_tuoi_hop_le = []
    # Lưu trữ chi tiết: { ngày: {'count': số lần, 'total_time': tổng giây} }
    daily_details = {} 

    for i in range(len(du_lieu_khu) - 1):
        h1, h2 = du_lieu_khu[i], du_lieu_khu[i+1]
        if h1.get('Trạng thái') == "Bật" and h2.get('Trạng thái') == "Tắt":
            t1 = datetime.strptime(h1['Thời gian'], fmt)
            t2 = datetime.strptime(h2['Thời gian'], fmt)
            duration = (t2 - t1).total_seconds()
            
            if duration >= MIN_DURATION_SECONDS:
                lan_tuoi_hop_le.append(t1)
                d_str = t1.strftime("%Y-%m-%d")
                
                if d_str not in daily_details:
                    daily_details[d_str] = {'count': 0, 'total_time': 0}
                daily_details[d_str]['count'] += 1
                daily_details[d_str]['total_time'] += duration

    # 2. Phân vụ
    ngay_hop_le = sorted([datetime.strptime(n, "%Y-%m-%d").date()
                         for n, info in daily_details.items() if info['count'] >= MIN_PUMP_PER_DAY])
    
    if not ngay_hop_le:
        st.warning(f"Không tìm thấy dữ liệu cho Khu {KHU_VUC_ID_INPUT}")
        return

    danh_sach_vu = []
    bat_dau = ngay_hop_le[0]
    truoc_do = ngay_hop_le[0]

    def get_vu_data(s, e):
        stats = {d: daily_details[d] for d in daily_details if s <= datetime.strptime(d, "%Y-%m-%d").date() <= e}
        total_pumps = sum(info['count'] for info in stats.values())
        return {'start': s, 'end': e, 'duration': (e-s).days + 1, 'total_pumps': total_pumps, 'daily_stats': stats}

    for i in range(1, len(ngay_hop_le)):
        if (ngay_hop_le[i] - truoc_do).days > MAX_GAP_DAYS:
            if (truoc_do - bat_dau).days + 1 >= MIN_SEASON_DURATION:
                danh_sach_vu.append(get_vu_data(bat_dau, truoc_do))
            bat_dau = ngay_hop_le[i]
        truoc_do = ngay_hop_le[i]

    if (truoc_do - bat_dau).days + 1 >= MIN_SEASON_DURATION:
        danh_sach_vu.append(get_vu_data(bat_dau, truoc_do))

    if not danh_sach_vu:
        st.warning("Không có mùa vụ nào đủ độ dài tối thiểu.")
        return

    # --- GIAO DIỆN CHỌN VỤ ---
    st.subheader("📁 Danh sách mùa vụ đã phát hiện")
    options = [f"Vụ {i+1}: từ {v['start']} đến {v['end']}" for i, v in enumerate(danh_sach_vu)]
    selection = st.selectbox("Chọn mùa vụ để xem chi tiết:", options)
    
    # Lấy index của vụ được chọn
    index_chon = options.index(selection)
    vu_hien_tai = danh_sach_vu[index_chon]

    # Hiển thị biểu đồ
    ve_bieu_do_don(vu_hien_tai, index_chon + 1)

    # Hiển thị bảng chi tiết ngày
    st.markdown(f"#### 📅 Chi tiết từng ngày - Vụ {index_chon + 1}")
    
    # Header của bảng chi tiết
    c1, c2, c3 = st.columns([2, 2, 3])
    c1.write("**Ngày**")
    c2.write("**Số lần tưới**")
    c3.write("**Tổng thời gian (phút:giây)**")
    st.divider()

    stats_selected = vu_hien_tai['daily_stats']
    for ngay in sorted(stats_selected.keys()):
        info = stats_selected[ngay]
        mins = int(info['total_time'] // 60)
        secs = int(info['total_time'] % 60)
        
        r1, r2, r3 = st.columns([2, 2, 3])
        r1.write(ngay)
        r2.write(str(info['count']))
        r3.write(f"{mins} phút {secs} giây")

# Chạy chương trình
if FILE_UPLOAD is not None:
    data = json.load(FILE_UPLOAD)
    thuc_thi_tong_hop(data)
else:
    st.info("👋 Hãy tải file JSON lên để bắt đầu.")
