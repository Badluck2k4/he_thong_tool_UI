import streamlit as st
import json
import matplotlib.pyplot as plt
from datetime import datetime

# --- 1. CẤU HÌNH HẰNG SỐ ---
MIN_DURATION_SECONDS = 20
THOI_GIAN_TOI_DA_GIAY = 3600
MIN_PUMP_PER_DAY = 5       
SO_LAN_TOI_DA_NGAY = 50       
MAX_GAP_DAYS = 2           
MIN_SEASON_DURATION = 7    

NGUONG_BIEN_DONG_TINH = 4     
NGAY_TOI_THIEU_GD = 3         
MAX_GIAI_DOAN = 15

st.set_page_config(page_title="Dashboard Phân Tích Tưới", layout="wide")

# --- 2. CSS TỐI ƯU (ĐÃ LOẠI BỎ CÁC TÙY CHỈNH GÂY LỖI MÀU CHỮ) ---
st.markdown("""
    <style>
    /* Chỉ bo góc và tạo viền nhẹ cho ô chỉ số, không can thiệp màu chữ */
    div[data-testid="stMetric"] {
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 10px;
        border-radius: 10px;
        background-color: rgba(255, 255, 255, 0.05);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💧 Hệ Thống Phân Tích Mùa Vụ & Giai Đoạn")

# Sidebar
st.sidebar.header("📁 Quản lý dữ liệu")
FILES_UPLOAD = st.sidebar.file_uploader("Tải lên các file JSON", type=['json'], accept_multiple_files=True)

def ve_bieu_do_ngang(du_lieu_bieu_do, tieu_de):
    dates = sorted(du_lieu_bieu_do.keys(), reverse=True) 
    counts = [du_lieu_bieu_do[d]['count'] for d in dates]
    
    chart_height = min(10, max(4, len(dates) * 0.35))
    fig, ax = plt.subplots(figsize=(8, chart_height))
    
    # Giữ nguyên màu xanh lá và đường đỏ như cũ
    ax.barh(dates, counts, color='#4CAF50', alpha=0.9)
    ax.axvline(x=MIN_PUMP_PER_DAY, color='#FF5252', linestyle='--', alpha=0.7)
    
    # Tự động điều chỉnh màu chữ nhãn theo giao diện
    is_dark = st.get_option("theme.base") == "dark"
    label_color = 'white' if is_dark else 'black'
    
    ax.set_title(tieu_de, fontsize=10, fontweight='bold', color=label_color)
    ax.tick_params(axis='both', which='major', labelsize=9, colors=label_color)
    
    # Làm trong suốt nền để không bị các ô trắng đè lên
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    
    for spine in ax.spines.values():
        spine.set_edgecolor(label_color)
        spine.set_alpha(0.3)
        
    plt.tight_layout()
    st.pyplot(fig)

def thuc_thi_chia_giai_doan(ngay_sap_xep, daily_stats):
    danh_sach_gd = []
    if not ngay_sap_xep: return danh_sach_gd
    tap_hop_ngay = [ngay_sap_xep[0]]
    for i in range(1, len(ngay_sap_xep)):
        ngay_hien_tai = ngay_sap_xep[i]
        so_lan_hien_tai = daily_stats[ngay_hien_tai]['count']
        trung_binh_gd = sum(daily_stats[d]['count'] for d in tap_hop_ngay) / len(tap_hop_ngay)
        if abs(so_lan_hien_tai - trung_binh_gd) > NGUONG_BIEN_DONG_TINH and len(tap_hop_ngay) >= NGAY_TOI_THIEU_GD:
            danh_sach_gd.append(tap_hop_ngay)
            tap_hop_ngay = [ngay_hien_tai]
        else: tap_hop_ngay.append(ngay_hien_tai)
    if tap_hop_ngay: danh_sach_gd.append(tap_hop_ngay)
    while len(danh_sach_gd) > MAX_GIAI_DOAN:
        idx_min = 0
        m_len = len(danh_sach_gd[0])
        for idx, g in enumerate(danh_sach_gd):
            if len(g) < m_len: m_len = len(g); idx_min = idx
        if idx_min > 0: danh_sach_gd[idx_min-1].extend(danh_sach_gd.pop(idx_min))
        else: danh_sach_gd[idx_min].extend(danh_sach_gd.pop(idx_min + 1))
    return danh_sach_gd

def hien_thi_bang_du_lieu(du_lieu_hien_thi):
    st.markdown("### 📅 Chi tiết từng ngày")
    st.write("---")
    for ngay in sorted(du_lieu_hien_thi.keys(), reverse=True):
        info = du_lieu_hien_thi[ngay]
        r = st.columns([1.5, 1, 1.5])
        r[0].write(f"`{ngay}`")
        r[1].write(f"✅ {info['count']}")
        r[2].write(f"⏱️ {int(info['total_time']//60)}p {int(info['total_time']%60)}s")

def thuc_thi_tong_hop(data_tong_hop, kv_input_id):
    stt_chuoi = str(kv_input_id)
    fmt = "%Y-%m-%d %H-%M-%S"
    daily_details = {} 
    du_lieu_khu = sorted([d for d in data_tong_hop if d.get('STT') == stt_chuoi],
                        key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    for i in range(len(du_lieu_khu) - 1):
        h1, h2 = du_lieu_khu[i], du_lieu_khu[i+1]
        if h1.get('Trạng thái') == "Bật" and h2.get('Trạng thái') == "Tắt":
            try:
                t1, t2 = datetime.strptime(h1['Thời gian'], fmt), datetime.strptime(h2['Thời gian'], fmt)
                dur = (t2 - t1).total_seconds()
                if MIN_DURATION_SECONDS <= dur <= THOI_GIAN_TOI_DA_GIAY:
                    d_str = t1.strftime("%Y-%m-%d")
                    if d_str not in daily_details: daily_details[d_str] = {'count': 0, 'total_time': 0}
                    daily_details[d_str]['count'] += 1
                    daily_details[d_str]['total_time'] += dur
            except: continue
    ngay_hop_le = sorted([datetime.strptime(n, "%Y-%m-%d").date() for n, info in daily_details.items() 
                         if MIN_PUMP_PER_DAY <= info['count'] <= SO_LAN_TOI_DA_NGAY])
    if not ngay_hop_le:
        st.warning("Không có dữ liệu hợp lệ."); return
    danh_sach_vu = []
    b_idx = 0
    for i in range(1, len(ngay_hop_le)):
        if (ngay_hop_le[i] - ngay_hop_le[i-1]).days > MAX_GAP_DAYS:
            if (ngay_hop_le[i-1] - ngay_hop_le[b_idx]).days + 1 >= MIN_SEASON_DURATION:
                stats = {n.strftime("%Y-%m-%d"): daily_details[n.strftime("%Y-%m-%d")] for n in ngay_hop_le[b_idx:i]}
                danh_sach_vu.append({'start': ngay_hop_le[b_idx], 'end': ngay_hop_le[i-1], 'duration': (ngay_hop_le[i-1]-ngay_hop_le[b_idx]).days+1, 'daily_stats': stats})
            b_idx = i
    if (ngay_hop_le[-1] - ngay_hop_le[b_idx]).days + 1 >= MIN_SEASON_DURATION:
        stats = {n.strftime("%Y-%m-%d"): daily_details[n.strftime("%Y-%m-%d")] for n in ngay_hop_le[b_idx:]}
        danh_sach_vu.append({'start': ngay_hop_le[b_idx], 'end': ngay_hop_le[-1], 'duration': (ngay_hop_le[-1]-ngay_hop_le[b_idx]).days+1, 'daily_stats': stats})

    opt_vu = [f"Vụ {i+1}: {v['start']} -> {v['end']}" for i, v in enumerate(danh_sach_vu)]
    chon_vu_label = st.selectbox("📅 Chọn mùa vụ:", opt_vu)
    v_idx = opt_vu.index(chon_vu_label)
    vu_ht = danh_sach_vu[v_idx]
    ds_gd = thuc_thi_chia_giai_doan(sorted(vu_ht['daily_stats'].keys()), vu_ht['daily_stats'])

    st.sidebar.markdown("---")
    chế_độ = ["Toàn mùa vụ"] + [f"Giai đoạn {i+1}" for i in range(len(ds_gd))]
    lua_chon = st.sidebar.radio("🔍 Chọn phạm vi xem:", chế_độ)

    if lua_chon == "Toàn mùa vụ":
        du_lieu = vu_ht['daily_stats']
        tieu_de = f"BÁO CÁO VỤ {v_idx + 1}"
    else:
        g_idx = int(lua_chon.split()[-1]) - 1
        du_lieu = {d: vu_ht['daily_stats'][d] for d in ds_gd[g_idx]}
        tieu_de = f"BÁO CÁO GIAI ĐOẠN {g_idx + 1}"

    # --- BỐ CỤC DASHBOARD ---
    col_trai, col_phai = st.columns([6, 4], gap="large")

    with col_trai:
        st.subheader(tieu_de)
        # 2 Ô CHỈ SỐ: Đã sửa để nhìn được chữ
        m1, m2 = st.columns(2)
        m1.metric("Số ngày trong kỳ", f"{len(du_lieu)} ngày")
        m2.metric("Tổng lần tưới", f"{sum(i['count'] for i in du_lieu.values())} lần")
        
        # BIỂU ĐỒ: Giữ nguyên như cũ
        ve_bieu_do_ngang(du_lieu, "Phân bố tần suất tưới")

    with col_phai:
        hien_thi_bang_du_lieu(du_lieu)

# --- XỬ LÝ FILE ---
if FILES_UPLOAD:
    selected_files = [f for f in FILES_UPLOAD if st.sidebar.checkbox(f.name, value=True, key=f.name)]
    data_tong_hop = []
    for f in selected_files:
        content = json.load(f)
        if isinstance(content, list): data_tong_hop.extend(content)
    if data_tong_hop:
        khu_tt = {}
        data_s = sorted(data_tong_hop, key=lambda x: x.get('Thời gian', ''))
        fmt = "%Y-%m-%d %H-%M-%S"
        for i in range(len(data_s) - 1):
            h1, h2 = data_s[i], data_s[i+1]
            if h1.get('STT') == h2.get('STT') and h1.get('Trạng thái')=="Bật" and h2.get('Trạng thái')=="Tắt":
                try:
                    dur = (datetime.strptime(h2['Thời gian'], fmt) - datetime.strptime(h1['Thời gian'], fmt)).total_seconds()
                    if MIN_DURATION_SECONDS <= dur <= THOI_GIAN_TOI_DA_GIAY:
                        khu_tt[h1.get('STT')] = khu_tt.get(h1.get('STT'), 0) + 1
                except: continue
        if khu_tt:
            ds_k = sorted(khu_tt.keys(), key=lambda x: int(x) if x.isdigit() else x)
            khu_c = st.sidebar.selectbox("🎯 Chọn Khu vực:", ds_k)
            thuc_thi_tong_hop(data_tong_hop, khu_c)
else:
    st.info("👋 Vui lòng tải file JSON để bắt đầu.")
