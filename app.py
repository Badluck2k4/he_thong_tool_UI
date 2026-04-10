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
        r[2].write(f"
