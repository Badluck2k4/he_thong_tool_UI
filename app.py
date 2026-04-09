import streamlit as st
import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime

# --- CẤU HÌNH CỐ ĐỊNH (Giá trị mặc định bên trong code) ---
KHU_VUC_ID = 2
MIN_DURATION_SECONDS = 20
MIN_PUMP_PER_DAY = 5
MAX_GAP_DAYS = 2
MIN_SEASON_DURATION = 7

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Phân tích tưới nhỏ giọt", layout="wide")
st.title("💧 Hệ Thống Phân Tích Mùa Vụ")

# Sidebar chỉ giữ lại phần upload file và chọn ID khu vực
st.sidebar.header("Dữ liệu đầu vào")
FILE_UPLOAD = st.sidebar.file_uploader("Chọn file 'Lich nho giotj.json'", type=['json'])
KHU_VUC_ID_INPUT = st.sidebar.number_input("ID Khu Vực cần phân tích", value=KHU_VUC_ID)

def ve_bieu_do_thoang(danh_sach_vu):
    """Giữ nguyên hàm vẽ biểu đồ của bạn"""
    num_seasons = len(danh_sach_vu)
    if num_seasons == 0: return

    fig, axes = plt.subplots(num_seasons, 1, figsize=(15, 6 * num_seasons))
    if num_seasons == 1: axes = [axes]

    for i, vu in enumerate(danh_sach_vu):
        stats = vu['daily_stats']
        dates = sorted(stats.keys())
        counts = [stats[d] for d in dates]
        ax = axes[i]

        bars = ax.bar(dates, counts, color='#2ca02c', edgecolor='white', alpha=0.85)
        ax.axhline(y=MIN_PUMP_PER_DAY, color='red', linestyle='--', alpha=0.4, label='Ngưỡng tối thiểu')

        ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
        ax.set_title(f"BIỂU ĐỒ VỤ {i+1}: {vu['start']} ĐẾN {vu['end']}", fontsize=14, fontweight='bold', pad=20)
        ax.set_ylabel("Số lần tưới")
        ax.tick_params(axis='x', rotation=30)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        ax.legend()

        if len(dates) < 45:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.2, f'{int(height)}',
                        ha='center', va='bottom', fontsize=8, color='#444')

    plt.tight_layout(pad=4.0)
    st.pyplot(fig)

def thuc_thi_tong_hop(data_lich):
    """Sử dụng các thông số mặc định đã khai báo ở đầu code"""
    stt_chuoi = str(KHU_VUC_ID_INPUT)
    fmt = "%Y-%m-%d %H-%M-%S"

    # 1. Lọc lần tưới
    du_lieu_khu = sorted([d for d in data_lich if d.get('STT') == stt_chuoi],
                        key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    
    lan_tuoi_hop_le, daily_raw = [], {}

    for i in range(len(du_lieu_khu) - 1):
        h1, h2 = du_lieu_khu[i], du_lieu_khu[i+1]
        if h1.get('Trạng thái') == "Bật" and h2.get('Trạng thái') == "Tắt":
            t1 = datetime.strptime(h1['Thời gian'], fmt)
            t2 = datetime.strptime(h2['Thời gian'], fmt)
            if (t2 - t1).total_seconds() >= MIN_DURATION_SECONDS:
                lan_tuoi_hop_le.append(t1)
                d_str = t1.strftime("%Y-%m-%d")
                daily_raw[d_str] = daily_raw.get(d_str, 0) + 1

    # 2. Phân vụ
    ngay_hop_le = sorted([datetime.strptime(n, "%Y-%m-%d").date()
                         for n, count in daily_raw.items() if count >= MIN_PUMP_PER_DAY])
    
    if not ngay_hop_le:
        st.warning(f"Không tìm thấy dữ liệu cho Khu {KHU_VUC_ID_INPUT} thỏa mãn điều kiện.")
        return

    danh_sach_vu = []
    bat_dau = ngay_hop_le[0]
    truoc_do = ngay_hop_le[0]

    st.subheader(f"BÁO CÁO CHI TIẾT KHU {KHU_VUC_ID_INPUT}")
    
    # Bảng hiển thị kết quả
    cols = st.columns([1, 2, 2, 1, 2])
    cols[0].write("**STT**")
    cols[1].write("**Bắt đầu**")
    cols[2].write("**Kết thúc**")
    cols[3].write("**Ngày**")
    cols[4].write("**Tổng lần**")
    st.divider()

    def add_vu(stt, s, e):
        dur = (e - s).days + 1
        total = sum(1 for d in lan_tuoi_hop_le if s <= d.date() <= e)
        
        c = st.columns([1, 2, 2, 1, 2])
        c[0].write(stt)
        c[1].write(str(s))
        c[2].write(str(e))
        c[3].write(dur)
        c[4].write(total)
        
        stats = {d: daily_raw[d] for d in daily_raw if s <= datetime.strptime(d, "%Y-%m-%d").date() <= e}
        return {'start': s, 'end': e, 'daily_stats': stats}

    stt_vu = 1
    for i in range(1, len(ngay_hop_le)):
        if (ngay_hop_le[i] - truoc_do).days > MAX_GAP_DAYS:
            if (truoc_do - bat_dau).days + 1 >= MIN_SEASON_DURATION:
                danh_sach_vu.append(add_vu(stt_vu, bat_dau, truoc_do))
                stt_vu += 1
            bat_dau = ngay_hop_le[i]
        truoc_do = ngay_hop_le[i]

    if (truoc_do - bat_dau).days + 1 >= MIN_SEASON_DURATION:
        danh_sach_vu.append(add_vu(stt_vu, bat_dau, truoc_do))

    st.write("") 
    ve_bieu_do_thoang(danh_sach_vu)

# Chạy chương trình
if FILE_UPLOAD is not None:
    data = json.load(FILE_UPLOAD)
    thuc_thi_tong_hop(data)
else:
    st.info("👋 Hãy tải file JSON lên để xem báo cáo.")
