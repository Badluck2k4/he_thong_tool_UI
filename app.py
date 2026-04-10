import streamlit as st
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# --- 1. CẤU HÌNH HẰNG SỐ TỐI ƯU ---
MIN_DURATION_SECONDS = 20
THOI_GIAN_TOI_DA_GIAY = 3600
MIN_PUMP_PER_DAY = 5       
SO_LAN_TOI_DA_NGAY = 50       
MAX_GAP_DAYS = 2           
MIN_SEASON_DURATION = 7    

# Ngưỡng biến động mới (2 đến 3 lần)
NGUONG_BIEN_DONG_TINH = 2.5   
NGAY_TOI_THIEU_GD = 3         
MAX_GIAI_DOAN = 15

st.set_page_config(page_title="Dashboard Phân Tích Tưới", layout="wide")

# CSS giữ nguyên để hiển thị Metric rõ nét
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #A0A0A0 !important; }
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 15px !important;
        border-radius: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC CHIA GIAI ĐOẠN VÀ LÀM MỊN (SMOOTHING) ---
def thuc_thi_chia_va_lam_min(ngay_sap_xep, daily_stats):
    danh_sach_gd = []
    if not ngay_sap_xep: return danh_sach_gd, daily_stats

    # Bước 1: Chia nhóm dựa trên ngưỡng biến động 2-3 lần
    tap_hop_ngay = [ngay_sap_xep[0]]
    for i in range(1, len(ngay_sap_xep)):
        ngay_hien_tai = ngay_sap_xep[i]
        so_lan_hien_tai = daily_stats[ngay_hien_tai]['count']
        trung_binh_nhom_tam = sum(daily_stats[d]['count'] for d in tap_hop_ngay) / len(tap_hop_ngay)
        
        if abs(so_lan_hien_tai - trung_binh_nhom_tam) > NGUONG_BIEN_DONG_TINH and len(tap_hop_ngay) >= NGAY_TOI_THIEU_GD:
            danh_sach_gd.append(tap_hop_ngay)
            tap_hop_ngay = [ngay_hien_tai]
        else:
            tap_hop_ngay.append(ngay_hien_tai)
    if tap_hop_ngay: danh_sach_gd.append(tap_hop_ngay)

    # Bước 2: San phẳng (Cắt ngang qua) dữ liệu bằng giá trị trung bình
    new_stats = daily_stats.copy()
    for gd in danh_sach_gd:
        avg_count = round(sum(daily_stats[d]['count'] for d in gd) / len(gd))
        for d in gd:
            new_stats[d]['count'] = avg_count # Gán số trung bình cho cả giai đoạn
            
    return danh_sach_gd, new_stats

# --- 3. HÀM VẼ BIỂU ĐỒ NỀN TRẮNG ĐA SẮC ---
def ve_bieu_do_ngang_da_sac(du_lieu_bieu_do, danh_sach_gd, tieu_de, is_toan_vu=True):
    dates = sorted(du_lieu_bieu_do.keys(), reverse=True) 
    counts = [du_lieu_bieu_do[d]['count'] for d in dates]
    
    palette = ['#2E7D32', '#1565C0', '#C62828', '#AD1457', '#6A1B9A', '#0277BD', '#00695C', '#EF6C00', '#4E342E']
    bar_colors = []
    if is_toan_vu:
        for d in dates:
            color_found = palette[0]
            for idx, gd in enumerate(danh_sach_gd):
                if d in gd:
                    color_found = palette[idx % len(palette)]
                    break
            bar_colors.append(color_found)
    else:
        bar_colors = [palette[0]] * len(dates)

    chart_height = min(12, max(5, len(dates) * 0.35))
    fig, ax = plt.subplots(figsize=(8, chart_height))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    ax.barh(dates, counts, color=bar_colors, alpha=0.8)
    ax.axvline(x=MIN_PUMP_PER_DAY, color='red', linestyle='--', alpha=0.6)
    
    ax.set_title(tieu_de, fontsize=10, fontweight='bold', color='black')
    ax.tick_params(axis='both', labelsize=9, colors='black')
    for spine in ax.spines.values(): spine.set_edgecolor('#333333')
    ax.grid(axis='x', linestyle=':', alpha=0.3, color='black')
    
    # Hiển thị số lần tưới ngay trên đầu cột để dễ nhìn
    for i, v in enumerate(counts):
        ax.text(v + 0.5, i, str(v), color='black', va='center', fontsize=8, fontweight='bold')

    plt.tight_layout()
    st.pyplot(fig)

# --- 4. LUỒNG XỬ LÝ CHÍNH ---
st.sidebar.header("📁 Quản lý dữ liệu")
FILES_UPLOAD = st.sidebar.file_uploader("Tải lên file JSON", type=['json'], accept_multiple_files=True)

def thuc_thi_tong_hop(data_tong_hop, kv_input_id):
    stt_chuoi = str(kv_input_id)
    fmt = "%Y-%m-%d %H-%M-%S"
    daily_details = {} 
    
    # Lọc và xử lý thô
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
    
    if not ngay_hop_le: return st.warning("Không có dữ liệu hợp lệ.")

    # Gom vụ
    danh_sach_vu = []
    b_idx = 0
    for i in range(1, len(ngay_hop_le)):
        if (ngay_hop_le[i] - ngay_hop_le[i-1]).days > MAX_GAP_DAYS:
            if (ngay_hop_le[i-1] - ngay_hop_le[b_idx]).days + 1 >= MIN_SEASON_DURATION:
                stats = {n.strftime("%Y-%m-%d"): daily_details[n.strftime("%Y-%m-%d")] for n in ngay_hop_le[b_idx:i]}
                danh_sach_vu.append({'start': ngay_hop_le[b_idx], 'end': ngay_hop_le[i-1], 'daily_stats': stats})
            b_idx = i
    # Thêm vụ cuối
    stats_end = {n.strftime("%Y-%m-%d"): daily_details[n.strftime("%Y-%m-%d")] for n in ngay_hop_le[b_idx:]}
    danh_sach_vu.append({'start': ngay_hop_le[b_idx], 'end': ngay_hop_le[-1], 'daily_stats': stats_end})

    opt_vu = [f"Vụ {i+1}: {v['start']} -> {v['end']}" for i, v in enumerate(danh_sach_vu)]
    chon_vu_label = st.selectbox("📅 Chọn mùa vụ:", opt_vu)
    vu_ht = danh_sach_vu[opt_vu.index(chon_vu_label)]
    
    # THỰC THI CHIA GIAI ĐOẠN VÀ LÀM MỊN
    ds_gd, stats_min = thuc_thi_chia_va_lam_min(sorted(vu_ht['daily_stats'].keys()), vu_ht['daily_stats'])

    st.sidebar.markdown("---")
    lua_chon = st.sidebar.radio("🔍 Chế độ xem:", ["Toàn mùa vụ"] + [f"Giai đoạn {i+1}" for i in range(len(ds_gd))])

    if lua_chon == "Toàn mùa vụ":
        du_lieu = stats_min
        is_toan_vu = True
    else:
        g_idx = int(lua_chon.split()[-1]) - 1
        du_lieu = {d: stats_min[d] for d in ds_gd[g_idx]}
        is_toan_vu = False

    # Dashboard 2 cột
    c1, c2 = st.columns([6, 4])
    with c1:
        st.subheader(f"📊 {lua_chon.upper()}")
        m1, m2 = st.columns(2)
        m1.metric("Số ngày", f"{len(du_lieu)} ngày")
        m2.metric("Tổng lần tưới", f"{sum(i['count'] for i in du_lieu.values())} lần")
        ve_bieu_do_ngang_da_sac(du_lieu, ds_gd, "Tần suất tưới đã làm mịn (Số lần trung bình/giai đoạn)", is_toan_vu)
    with c2:
        st.markdown("### 📅 Chi tiết (Dữ liệu gốc)")
        for n in sorted(du_lieu.keys(), reverse=True):
            info = vu_ht['daily_stats'][n] # Hiển thị số gốc ở bảng chi tiết để đối soát
            st.write(f"`{n}` | ✅ **{info['count']} lần** | ⏱️ {int(info['total_time']//60)}p")

if FILES_UPLOAD:
    data_tong_hop = []
    for f in FILES_UPLOAD:
        content = json.load(f)
        if isinstance(content, list): data_tong_hop.extend(content)
    if data_tong_hop:
        khu_c = st.sidebar.selectbox("🎯 Khu vực:", sorted(list(set(d.get('STT') for d in data_tong_hop))))
        thuc_thi_tong_hop(data_tong_hop, khu_c)
else:
    st.title("💧 Hệ Thống Phân Tích Tưới")
    st.info("Vui lòng tải file JSON.")
