import streamlit as st
import json
import matplotlib.pyplot as plt
from datetime import datetime

# --- CẤU HÌNH CỐ ĐỊNH ---
MIN_DURATION_SECONDS = 20
THOI_GIAN_TOI_DA_GIAY = 3600
MIN_PUMP_PER_DAY = 5       
SO_LAN_TOI_DA_NGAY = 50       
MAX_GAP_DAYS = 2           
MIN_SEASON_DURATION = 7    

# Cấu hình lọc giai đoạn
NGUONG_BIEN_DONG_TINH = 4     
NGAY_TOI_THIEU_GD = 3         
MAX_GIAI_DOAN = 15

st.set_page_config(page_title="Phân tích tưới chi tiết", layout="wide")
st.title("💧 Hệ Thống Phân Tích Mùa Vụ & Giai Đoạn")

# Sidebar
st.sidebar.header("📁 Quản lý dữ liệu")
FILES_UPLOAD = st.sidebar.file_uploader("Tải lên các file JSON", type=['json'], accept_multiple_files=True)

def ve_bieu_do_ngang(du_lieu_bieu_do, tieu_de):
    dates = sorted(du_lieu_bieu_do.keys(), reverse=True) 
    counts = [du_lieu_bieu_do[d]['count'] for d in dates]
    chart_height = max(5, len(dates) * 0.4)
    fig, ax = plt.subplots(figsize=(10, chart_height))
    bars = ax.barh(dates, counts, color='#2ca02c', alpha=0.85)
    ax.axvline(x=MIN_PUMP_PER_DAY, color='red', linestyle='--', alpha=0.6)
    ax.set_title(tieu_de, fontsize=12, fontweight='bold')
    st.pyplot(fig)

def thuc_thi_chia_giai_doan(ngay_sap_xep, daily_stats):
    """Hàm xử lý logic chia giai đoạn để tránh lỗi thụt lề"""
    danh_sach_gd = []
    if not ngay_sap_xep:
        return danh_sach_gd

    tap_hop_ngay = [ngay_sap_xep[0]]
    for i in range(1, len(ngay_sap_xep)):
        ngay_hien_tai = ngay_sap_xep[i]
        so_lan_hien_tai = daily_stats[ngay_hien_tai]['count']
        
        trung_binh_gd = sum(daily_stats[d]['count'] for d in tap_hop_ngay) / len(tap_hop_ngay)
        
        # Điều kiện ngắt: Lệch > ngưỡng VÀ đã đủ số ngày tối thiểu
        if abs(so_lan_hien_tai - trung_binh_gd) > NGUONG_BIEN_DONG_TINH and len(tap_hop_ngay) >= NGAY_TOI_THIEU_GD:
            danh_sach_gd.append(tap_hop_ngay)
            tap_hop_ngay = [ngay_hien_tai]
        else:
            tap_hop_ngay.append(ngay_hien_tai)
    
    if tap_hop_ngay:
        danh_sach_gd.append(tap_hop_ngay)

    # Gộp cưỡng bức nếu vượt quá MAX_GIAI_DOAN
    while len(danh_sach_gd) > MAX_GIAI_DOAN:
        index_ngan_nhat = 0
        min_len = len(danh_sach_gd[0])
        for idx, gd in enumerate(danh_sach_gd):
            if len(gd) < min_len:
                min_len = len(gd)
                index_ngan_nhat = idx
        
        # Gộp vào đoạn trước hoặc sau tùy vị trí
        if index_ngan_nhat > 0:
            danh_sach_gd[index_ngan_nhat-1].extend(danh_sach_gd.pop(index_ngan_nhat))
        else:
            danh_sach_gd[index_ngan_nhat].extend(danh_sach_gd.pop(index_ngan_nhat + 1))
            
    return danh_sach_gd

def thuc_thi_tong_hop(data_tong_hop, kv_input_id):
    stt_chuoi = str(kv_input_id)
    fmt = "%Y-%m-%d %H-%M-%S"

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
                if MIN_DURATION_SECONDS <= duration <= THOI_GIAN_TOI_DA_GIAY:
                    d_str = t1.strftime("%Y-%m-%d")
                    if d_str not in daily_details:
                        daily_details[d_str] = {'count': 0, 'total_time': 0}
                    daily_details[d_str]['count'] += 1
                    daily_details[d_str]['total_time'] += duration
            except: continue

    ngay_hop_le = sorted([datetime.strptime(n, "%Y-%m-%d").date() 
                         for n, info in daily_details.items() 
                         if MIN_PUMP_PER_DAY <= info['count'] <= SO_LAN_TOI_DA_NGAY])
    
    if not ngay_hop_le:
        st.warning(f"⚠️ Khu {kv_input_id} không đủ dữ liệu đạt chuẩn.")
        return

    danh_sach_vu = []
    bat_dau = ngay_hop_le[0]; truoc_do = ngay_hop_le[Bat_dau_idx := 0]

    def get_vu_data(s, e):
        stats = {d: daily_details[d] for d in daily_details if s <= datetime.strptime(d, "%Y-%m-%d").date() <= e}
        return {'start': s, 'end': e, 'duration': (e-s).days + 1, 
                'total_pumps': sum(i['count'] for i in stats.values()), 'daily_stats': stats}

    for i in range(1, len(ngay_hop_le)):
        if (ngay_hop_le[i] - ngay_hop_le[i-1]).days > MAX_GAP_DAYS:
            if (ngay_hop_le[i-1] - ngay_hop_le[Bat_dau_idx]).days + 1 >= MIN_SEASON_DURATION:
                danh_sach_vu.append(get_vu_data(ngay_hop_le[Bat_dau_idx], ngay_hop_le[i-1]))
            Bat_dau_idx = i

    if (ngay_hop_le[-1] - ngay_hop_le[Bat_dau_idx]).days + 1 >= MIN_SEASON_DURATION:
        danh_sach_vu.append(get_vu_data(ngay_hop_le[Bat_dau_idx], ngay_hop_le[-1]))

    if not danh_sach_vu:
        st.warning("⚠️ Không tìm thấy mùa vụ nào đủ điều kiện.")
        return

    options_vu = [f"Vụ {i+1}: {v['start']} -> {v['end']} ({v['duration']} ngày)" for i, v in enumerate(danh_sach_vu)]
    chon_vu = st.selectbox("Chọn mùa vụ cần xem:", options_vu)
    index_vu = options_vu.index(chon_vu)
    vu_hien_tai = danh_sach_vu[index_vu]

    # Chia giai đoạn
    ngay_sap_xep_vu = sorted(vu_hien_tai['daily_stats'].keys())
    danh_sach_gd = thuc_thi_chia_giai_doan(ngay_sap_xep_vu, vu_hien_tai['daily_stats'])

    # Giao diện chọn xem
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Chế độ xem")
    che_do_xem = ["Toàn mùa vụ"] + [f"Giai đoạn {i+1}" for i in range(len(danh_sach_gd))]
    lua_chon_xem = st.sidebar.radio("Chọn phạm vi dữ liệu:", che_do_xem)

    if lua_chon_xem == "Toàn mùa vụ":
        du_lieu_hien_thi = vu_hien_tai['daily_stats']
        tieu_de_bc = f"BÁO CÁO TOÀN VỤ {index_vu + 1}"
    else:
        idx_gd = int(lua_chon_xem.split()[-1]) - 1
        ngay_trong_gd = danh_sach_gd[idx_gd]
        du_lieu_hien_thi = {d: vu_hien_tai['daily_stats'][d] for d in ngay_trong_gd}
        tieu_de_bc = f"BÁO CÁO {lua_chon_xem.upper()} ({ngay_trong_gd[0]} -> {ngay_trong_gd[-1]})"

    # Hiển thị
    st.subheader(tieu_de_bc)
    ve_bieu_do_ngang(du_lieu_hien_thi, tieu_de_bc)
    st.info(f"📋 **TỔNG KẾT:** {len(du_lieu_hien_thi)} ngày hoạt động | {sum(i['count'] for i in du_lieu_hien_thi.values())} lần tưới đạt chuẩn")

    c1, c2, c3 = st.columns([2, 2, 3])
    c1.write("**Ngày**"); c2.write("**Số lần tưới**"); c3.write("**Tổng thời gian**")
    st.divider()
    for ngay in sorted(du_lieu_hien_thi.keys()):
        info = du_lieu_hien_thi[ngay]
        r1, r2, r3 = st.columns([2, 2, 3])
        r1.write(ngay); r2.write(f"✅ {info['count']} lần"); r3.write(f"⏱️ {int(info['total_time']//60)}p {int(info['total_time']%60)}s")

# --- XỬ LÝ FILE ---
if FILES_UPLOAD:
    selected_files = [f for f in FILES_UPLOAD if st.sidebar.checkbox(f.name, value=True, key=f.name)]
    data_tong_hop = []
    for f in selected_files:
        content = json.load(f)
        if isinstance(content, list): data_tong_hop.extend(content)
    if data_tong_hop:
        khu_thuc_te = {}
        data_sorted = sorted(data_tong_hop, key=lambda x: x.get('Thời gian', ''))
        fmt = "%Y-%m-%d %H-%M-%S"
        for i in range(len(data_sorted) - 1):
            h1, h2 = data_sorted[i], data_sorted[i+1]
            if h1.get('STT') == h2.get('STT') and h1.get('Trạng thái') == "Bật" and h2.get('Trạng thái') == "Tắt":
                try:
                    dur = (datetime.strptime(h2['Thời gian'], fmt) - datetime.strptime(h1['Thời gian'], fmt)).total_seconds()
                    if MIN_DURATION_SECONDS <= dur <= THOI_GIAN_TOI_DA_GIAY:
                        khu_thuc_te[h1.get('STT')] = khu_thuc_te.get(h1.get('STT'), 0) + 1
                except: continue
        if khu_thuc_te:
            ds_khu = sorted(khu_thuc_te.keys(), key=lambda x: int(x) if x.isdigit() else x)
            khu_chon = st.sidebar.selectbox("Chọn Khu vực:", ds_khu)
            thuc_thi_tong_hop(data_tong_hop, khu_chon)
else:
    st.info("👋 Vui lòng tải file JSON lên.")
