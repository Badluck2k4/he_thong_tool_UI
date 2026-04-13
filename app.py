import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, date

# =================================================================
# KHUNG 1: CẤU HÌNH CÁC THÔNG SỐ GỐC (CONSTANTS)
# =================================================================
GIATRI_GOC = {
    "LAN_TUOI": 2.5, "TBEC": 8.0, "EC_REQ": 5.0,
    "GIAY_MIN": 20, "GIAY_MAX": 3600, "LAN_MIN_NGAY": 5,
    "GAP_NGAY": 2, "MIN_VU": 7
}

st.set_page_config(page_title="Phân tích Mùa vụ v3.3", layout="wide")

# =================================================================
# KHUNG 2: CÁC THUẬT TOÁN LOGIC TÍNH TOÁN (CORE LOGIC)
# Các hàm xử lý số liệu và phân chia giai đoạn
# =================================================================

def chuyen_doi_so_thuc(du_lieu, danh_sach_khoa):
    """Chuyển đổi các giá trị số từ chuỗi hoặc định dạng VN sang số thực"""
    for khoa in danh_sach_khoa:
        gia_tri = du_lieu.get(khoa)
        if gia_tri is not None:
            try: return float(str(gia_tri).replace(',', '.'))
            except: continue
    return None

def chia_giai_doan_tu_dong(danh_sach_ngay, du_lieu_ngay, khoa_chi_so, nguong_sai_so):
    """Thuật toán gom nhóm các ngày có chỉ số tương đồng vào một giai đoạn"""
    danh_sach_cac_gd = []
    if not danh_sach_ngay: return danh_sach_cac_gd
    nhom_hien_tai = [danh_sach_ngay[0]]
    for i in range(1, len(danh_sach_ngay)):
        ngay_dang_xet = danh_sach_ngay[i]
        gia_tri_ngay = du_lieu_ngay[ngay_dang_xet][khoa_chi_so]
        trung_binh_nhom = np.mean([du_lieu_ngay[d][khoa_chi_so] for d in nhom_hien_tai])
        sai_so = abs(gia_tri_ngay - trung_binh_nhom)
        if (sai_so > nguong_sai_so and len(nhom_hien_tai) >= 3) or (sai_so > nguong_sai_so * 3):
            danh_sach_cac_gd.append(nhom_hien_tai)
            nhom_hien_tai = [ngay_dang_xet]
        else: nhom_hien_tai.append(ngay_dang_xet)
    danh_sach_cac_gd.append(nhom_hien_tai)
    return danh_sach_cac_gd

# =================================================================
# KHUNG 3: LOGIC TRỰC QUAN HÓA (VISUALIZATION LOGIC)
# Hàm xử lý đồ họa biểu đồ
# =================================================================

def ve_bieu_do_doc(du_lieu_bieu_do, danh_sach_gd, tieu_de, khoa_gia_tri):
    """Vẽ biểu đồ cột dọc dựa trên STT và tô màu theo giai đoạn"""
    cac_ngay = sorted(du_lieu_bieu_do.keys())
    so_thu_tu = list(range(1, len(cac_ngay) + 1))
    gia_tri_hien_thi = [du_lieu_bieu_do[n].get('gia_tri_ao', du_lieu_bieu_do[n][khoa_gia_tri]) for n in cac_ngay]
    
    bang_mau = ['#2E7D32', '#1565C0', '#C62828', '#AD1457', '#6A1B9A', '#00838F', '#283593']
    mau_cot = []
    for ngay in cac_ngay:
        mau_chon = bang_mau[0]
        for idx, gd in enumerate(danh_sach_gd):
            if ngay in gd:
                mau_chon = bang_mau[idx % len(bang_mau)]
                break
        mau_cot.append(mau_chon)

    chieu_rong = max(10, len(cac_ngay) * 0.25)
    fig, ax = plt.subplots(figsize=(chieu_rong, 5))
    ax.bar(so_thu_tu, gia_tri_hien_thi, color=mau_cot, alpha=0.8)
    ax.set_title(tieu_de, fontweight='bold', fontsize=14, pad=20)
    ax.set_xlabel("Số thứ tự ngày (STT)", fontsize=10)
    ax.set_xticks(so_thu_tu)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    st.pyplot(fig)

# =================================================================
# KHUNG 4: LOGIC HIỆU CHỈNH GIAO DIỆN (UI INTERFACE & INPUTS)
# Phần xử lý Sidebar và Mainbody hiển thị
# =================================================================

# --- Giao diện 1: Sidebar Control ---
with st.sidebar:
    st.header("📂 Dữ liệu & Cấu hình")
    tep_nho_giot = st.file_uploader("Tải file Nhỏ giọt", type=['json'], accept_multiple_files=True)
    tep_cham_phan = st.file_uploader("Tải file Châm phân", type=['json'], accept_multiple_files=True)
    
    st.divider()
    st.subheader("🔍 Lọc thời gian")
    ngay_bat_dau = st.date_input("Từ ngày", value=None)
    ngay_ket_thuc = st.date_input("Đến ngày", value=None)

    st.divider()
    st.subheader("🛠 Cách hiển thị")
    chon_c1 = st.checkbox("Cách 1: Lần tưới", value=True)
    chon_c2 = st.checkbox("Cách 2: TBEC")
    chon_c3 = st.checkbox("Cách 3: EC Req")

    st.divider()
    with st.expander("⚙️ Chỉnh sai số"):
        if st.button("Reset"):
            st.session_state.ss_c1 = GIATRI_GOC["LAN_TUOI"]
            st.session_state.ss_c2 = GIATRI_GOC["TBEC"]
            st.session_state.ss_c3 = GIATRI_GOC["EC_REQ"]
        ss_c1 = st.number_input("Lần tưới", value=st.session_state.get('ss_c1', GIATRI_GOC["LAN_TUOI"]), step=0.1)
        ss_c2 = st.number_input("TBEC", value=st.session_state.get('ss_c2', GIATRI_GOC["TBEC"]), step=0.1)
        ss_c3 = st.number_input("EC Req", value=st.session_state.get('ss_c3', GIATRI_GOC["EC_REQ"]), step=0.1)

# --- Giao diện 2: Mainbody Display ---
if tep_nho_giot:
    # --- Logic phân tích Nhỏ giọt ---
    du_lieu_tho_ng = []
    for t in tep_nho_giot:
        try: du_lieu_tho_ng.extend(json.load(t))
        except: continue
    
    stt_list = sorted(list(set(str(d.get('STT')) for d in du_lieu_tho_ng if d.get('STT'))))
    khu_vuc = st.sidebar.selectbox("🎯 Khu vực", stt_list)

    thong_ke_ngay = {}
    thoi_gian_ngay = {}
    
    data_kv = sorted([d for d in du_lieu_tho_ng if str(d.get('STT')) == khu_vuc], key=lambda x: x['Thời gian'])
    for i in range(len(data_kv)-1):
        if data_kv[i].get('Trạng thái') == "Bật" and data_kv[i+1].get('Trạng thái') == "Tắt":
            try:
                t1 = datetime.strptime(data_kv[i]['Thời gian
