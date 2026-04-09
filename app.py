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
st.title("💧 Hệ Thống Phân Tích Mùa Vụ")

# Sidebar
st.sidebar.header("📁 Quản lý dữ liệu")
FILES_UPLOAD = st.sidebar.file_uploader("Tải lên các file JSON", type=['json'], accept_multiple_files=True)
KHU_VUC_ID_INPUT = st.sidebar.number_input("ID Khu Vực cần phân tích", value=2)

def ve_bieu_do_don(vu_chon, stt_vu):
    """Vẽ biểu đồ cho vụ được chọn"""
    stats = vu_chon['daily_stats']
    dates = sorted(stats.keys())
    counts = [stats[d]['count'] for d in dates]
    
    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.bar(dates, counts, color='#2ca02c', edgecolor='white', alpha=0.85)
    ax.axhline(y=MIN_PUMP_PER_DAY, color='red', linestyle='--', alpha=0.4, label='Ngưỡng tối thiểu')

    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
    ax.set_title(f"BIỂU ĐỒ SỐ LẦN TƯỚI HOÀN CHỈNH - VỤ {stt_vu}", fontsize=14, fontweight='bold')
    ax.set_ylabel("Số lần tưới (>=20s)")
    ax.tick_params(axis='x', rotation=30)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.legend()

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1, f'{int(height)}',
                ha='center', va='bottom', fontsize=9)
    
    st.pyplot(fig)

def thuc_thi_tong_hop(data_tong_hop):
    stt_chuoi = str(KHU_VUC_ID_INPUT)
    fmt = "%Y-%m-%d %H-%M-%S"

    # 1. Lọc và làm sạch dữ liệu
    du_lieu_khu = sorted([d for d in data_tong_hop if d.get('STT') == stt_chuoi],
                        key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    
    daily_details = {} 

    for i in range(len(du_lieu_khu) - 1):
        h1, h2 = du_lieu_khu[i], du_lieu_khu[i+1]
        if h1.get('Trạng thái') == "Bật" and h2.get('Trạng thái') == "Tắt":
            t1 = datetime.strptime(h1['Thời gian'], fmt)
            t2 = datetime.strptime(h2['Thời gian'], fmt)
            duration = (t2 - t1).total_seconds()
            
            if duration >= MIN_DURATION_SECONDS:
                d_str = t1.strftime("%Y-%m-%d")
                if d_str not in daily_details:
                    daily_details[d_str] = {'count': 0, 'total_time': 0}
                daily_details[d_str]['count'] += 1
                daily_details[d_str]['total_time'] += duration

    # 2. Phân vụ
    ngay_hop_le = sorted([datetime.strptime(n, "%Y-%m-%d").date()
                         for n, info in daily_details.items() if info['count'] >= MIN_PUMP_PER_DAY])
    
    if not ngay_hop_le:
        st.warning(f"⚠️ Không tìm thấy dữ liệu đạt chuẩn cho Khu {KHU_VUC_ID_INPUT}")
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
        st.warning("⚠️ Không có vụ nào đủ độ dài tối thiểu 7 ngày.")
        return

    # --- GIAO DIỆN CHỌN VỤ ---
    st.subheader(f"📊 Kết quả phân tích Khu {KHU_VUC_ID_INPUT}")
    options = [f"Vụ {i+1}: {v['start']} -> {v['end']}" for i, v in enumerate(danh_sach_vu)]
    selection = st.selectbox("Chọn mùa vụ để xem chi tiết:", options)
    
    index_chon = options.index(selection)
    vu_hien_tai = danh_sach_vu[index_chon]

    ve_bieu_do_don(vu_hien_tai, index_chon + 1)

    st.markdown(f"#### 📅 Bảng kê chi tiết - Vụ {index_chon + 1}")
    st.info(f"📋 **TỔNG KẾT VỤ:** Kéo dài **{vu_hien_tai['duration']} ngày** | Tổng cộng **{vu_hien_tai['total_pumps']} lần tưới** hoàn chỉnh (>=20s)")

    c1, c2, c3 = st.columns([2, 2, 3])
    c1.write("**Ngày**")
    c2.write("**Số lần tưới**")
    c3.write("**Tổng thời gian**")
    st.divider()

    stats_selected = vu_hien_tai['daily_stats']
    for ngay in sorted(stats_selected.keys()):
        info = stats_selected[ngay]
        mins = int(info['total_time'] // 60)
        secs = int(info['total_time'] % 60)
        
        r1, r2, r3 = st.columns([2, 2, 3])
        r1.write(ngay)
        r2.write(f"✅ {info['count']} lần")
        r3.write(f"⏱️ {mins} phút {secs} giây")

# --- XỬ LÝ NHIỀU FILE VÀ BỘ CHỌN THỦ CÔNG ---
if FILES_UPLOAD:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Chọn file để quét")
    
    selected_files_data = []
    # Hiển thị checkbox cho từng file đã upload
    for f in FILES_UPLOAD:
        is_selected = st.sidebar.checkbox(f"Sử dụng: {f.name}", value=True, key=f.name)
        if is_selected:
            selected_files_data.append(f)
    
    data_tong_hop = []
    for uploaded_file in selected_files_data:
        # Load dữ liệu từng file được chọn
        content = json.load(uploaded_file)
        if isinstance(content, list):
            data_tong_hop.extend(content)
            
    if data_tong_hop:
        thuc_thi_tong_hop(data_tong_hop)
    else:
        st.warning("Vui lòng tích chọn ít nhất một file ở thanh bên để bắt đầu phân tích.")
else:
    st.info("👋 Chào mừng! Hãy tải các file JSON lên và chọn file cần quét ở thanh bên trái.")
