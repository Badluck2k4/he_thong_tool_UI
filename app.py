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

st.set_page_config(page_title="Phân tích tưới nhỏ giọt", layout="wide")
st.title("💧 Hệ Thống Phân Tích Mùa Vụ")

# Sidebar
st.sidebar.header("📁 Quản lý dữ liệu")
FILES_UPLOAD = st.sidebar.file_uploader("Tải lên các file JSON", type=['json'], accept_multiple_files=True)

def ve_bieu_do_ngang(vu_chon, stt_vu):
    """Vẽ biểu đồ ngang để dễ đọc ngày tháng ở trục tung"""
    stats = vu_chon['daily_stats']
    # Sắp xếp ngày từ dưới lên trên để ngày mới nhất nằm dưới cùng hoặc ngược lại
    dates = sorted(stats.keys(), reverse=True) 
    counts = [stats[d]['count'] for d in dates]
    
    # Tính toán chiều cao biểu đồ dựa trên số lượng ngày
    chart_height = max(5, len(dates) * 0.4)
    fig, ax = plt.subplots(figsize=(10, chart_height))
    
    bars = ax.barh(dates, counts, color='#2ca02c', edgecolor='white', alpha=0.85)
    ax.axvline(x=MIN_PUMP_PER_DAY, color='red', linestyle='--', alpha=0.6, label=f'Ngưỡng {MIN_PUMP_PER_DAY} lần')

    ax.set_title(f"BIỂU ĐỒ VỤ {stt_vu}", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Số lần tưới (>=20s)")
    ax.set_ylabel("Ngày tháng")
    ax.grid(axis='x', linestyle='--', alpha=0.3)
    ax.legend()

    # Thêm số vào cuối mỗi thanh
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, f'{int(width)}', 
                va='center', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    st.pyplot(fig)

def thuc_thi_tong_hop(data_tong_hop, kv_input_id):
    stt_chuoi = str(kv_input_id)
    fmt = "%Y-%m-%d %H-%M-%S"

    # 1. Lọc và sắp xếp dữ liệu khu vực
    du_lieu_khu = sorted([d for d in data_tong_hop if d.get('STT') == stt_chuoi],
                        key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    
    daily_details = {} 
    for i in range(len(du_lieu_khu) - 1):
        h1, h2 = du_lieu_khu[i], du_lieu_khu[i+1]
        if h1.get('Trạng thái') == "Bật" and h2.get('Trạng thái') == "Tắt":
            try:
                t1 = datetime.strptime(h1['Thời gian'], fmt)
                t2 = datetime.strptime(h2['Thời gian'], fmt)
                duration = (t2 - t1).total_seconds()
                if duration >= MIN_DURATION_SECONDS:
                    d_str = t1.strftime("%Y-%m-%d")
                    if d_str not in daily_details:
                        daily_details[d_str] = {'count': 0, 'total_time': 0}
                    daily_details[d_str]['count'] += 1
                    daily_details[d_str]['total_time'] += duration
            except: continue

    # 2. Phân vụ
    ngay_hop_le = sorted([datetime.strptime(n, "%Y-%m-%d").date()
                         for n, info in daily_details.items() if info['count'] >= MIN_PUMP_PER_DAY])
    
    if not ngay_hop_le:
        st.warning(f"⚠️ Khu {kv_input_id} không có đủ dữ liệu đạt chuẩn.")
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
        st.warning(f"⚠️ Khu {kv_input_id} không tạo thành vụ nào đủ {MIN_SEASON_DURATION} ngày.")
        return

    st.subheader(f"📊 Phân tích mùa vụ Khu {kv_input_id}")
    options = [f"Vụ {i+1}: {v['start']} -> {v['end']}" for i, v in enumerate(danh_sach_vu)]
    selection = st.selectbox("Chọn mùa vụ để xem chi tiết:", options)
    index_chon = options.index(selection)
    vu_hien_tai = danh_sach_vu[index_chon]

    # Hiển thị biểu đồ ngang
    ve_bieu_do_ngang(vu_hien_tai, index_chon + 1)

    st.info(f"📋 **TỔNG KẾT VỤ:** Kéo dài **{vu_hien_tai['duration']} ngày** | Tổng cộng **{vu_hien_tai['total_pumps']} lần tưới**")
    
    # Bảng chi tiết
    c1, c2, c3 = st.columns([2, 2, 3])
    c1.write("**Ngày**"); c2.write("**Số lần tưới**"); c3.write("**Tổng thời gian**")
    for ngay in sorted(vu_hien_tai['daily_stats'].keys()):
        info = vu_hien_tai['daily_stats'][ngay]
        r1, r2, r3 = st.columns([2, 2, 3])
        r1.write(ngay); r2.write(f"✅ {info['count']} lần")
        r3.write(f"⏱️ {int(info['total_time']//60)}p {int(info['total_time']%60)}s")

# --- PHẦN QUÉT KHU VỰC THỰC TẾ ---
if FILES_UPLOAD:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Chọn file để quét")
    selected_files = [f for f in FILES_UPLOAD if st.sidebar.checkbox(f.name, value=True, key=f.name)]
    
    data_tong_hop = []
    for uploaded_file in selected_files:
        try:
            content = json.load(uploaded_file)
            if isinstance(content, list): data_tong_hop.extend(content)
        except: st.error(f"Lỗi đọc file {uploaded_file.name}")

    if data_tong_hop:
        fmt = "%Y-%m-%d %H-%M-%S"
        khu_thuc_te = {}
        
        # Sắp xếp toàn bộ dữ liệu theo thời gian để quét cặp Bật-Tắt chuẩn xác
        data_sorted = sorted(data_tong_hop, key=lambda x: x.get('Thời gian', ''))
        
        # QUY TRÌNH QUÉT KHU: Chỉ những khu có cặp Bật-Tắt >= 20s mới được ghi nhận
        for i in range(len(data_sorted) - 1):
            h1, h2 = data_sorted[i], data_sorted[i+1]
            # Phải cùng STT, h1 là Bật, h2 là Tắt
            if h1.get('STT') == h2.get('STT') and h1.get('Trạng thái') == "Bật" and h2.get('Trạng thái') == "Tắt":
                try:
                    t1 = datetime.strptime(h1['Thời gian'], fmt)
                    t2 = datetime.strptime(h2['Thời gian'], fmt)
                    if (t2 - t1).total_seconds() >= MIN_DURATION_SECONDS:
                        stt = h1.get('STT')
                        khu_thuc_te[stt] = khu_thuc_te.get(stt, 0) + 1
                except: continue

        st.subheader("🔍 Kết quả quét hệ thống")
        if khu_thuc_te:
            # Lọc danh sách ID khu thực tế (loại bỏ các ID nhiễu không có lần tưới đạt chuẩn)
            ds_khu_hop_le = sorted(khu_thuc_te.keys(), key=lambda x: int(x) if x.isdigit() else x)
            
            col_m1, col_m2 = st.columns([1, 3])
            col_m1.metric("Khu hoạt động thực tế", len(ds_khu_hop_le))
            
            txt_khu = ", ".join([f"Khu {k} ({khu_thuc_te[k]} lần đạt chuẩn)" for k in ds_khu_hop_le])
            st.write(f"**Danh sách các khu vực có dữ liệu tưới:** {txt_khu}")
            
            st.sidebar.markdown("---")
            khu_chon = st.sidebar.selectbox("Chọn Khu vực để xem báo cáo", ds_khu_hop_le)
            
            st.divider()
            thuc_thi_tong_hop(data_tong_hop, khu_chon)
        else:
            st.error(f"❌ Không tìm thấy dữ liệu tưới nào đạt chuẩn (>= {MIN_DURATION_SECONDS}s) trong các file đã chọn.")
else:
    st.info("👋 Vui lòng tải file JSON lên để bắt đầu.")
