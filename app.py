import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# =================================================================
# KHUNG 1: CẤU HÌNH CÁC THÔNG SỐ GỐC
# =================================================================
GIATRI_GOC = {
    "LAN_TUOI": 2.5, "TBEC": 8.0, "EC_REQ": 5.0,
    "GIAY_MIN": 20, "GIAY_MAX": 3600, "LAN_MIN_NGAY": 5,
    "GAP_NGAY": 2, "MIN_VU": 7
}

st.set_page_config(page_title="Phân tích Mùa vụ v3.9", layout="wide")

# MẸO CSS: Ép tạo thanh cuộn ngang cho biểu đồ
st.markdown("""
    <style>
    .stPlotlyChart, .css-1n76uvr, .stImage {
        overflow-x: auto !important;
    }
    .plot-container {
        overflow-x: auto;
        white-space: nowrap;
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# KHUNG 2: BỘ NÃO TÍNH TOÁN
# =================================================================

def chuyen_doi_so_thuc(du_lieu, danh_sach_khoa):
    for khoa in danh_sach_khoa:
        gia_tri = du_lieu.get(khoa)
        if gia_tri is not None:
            try: return float(str(gia_tri).replace(',', '.'))
            except: continue
    return None

def xac_dinh_vi_tri_vu(ngay_dang_xet_str, danh_sach_vu):
    ngay_dt = datetime.strptime(ngay_dang_xet_str, "%Y-%m-%d").date()
    for i, (start, end) in enumerate(danh_sach_vu):
        if start <= ngay_dt <= end:
            return f"Vụ {i+1}", (ngay_dt - start).days + 1
    return "Khoảng nghỉ", "-"

def chia_giai_doan_tu_dong(danh_sach_ngay, du_lieu_ngay, khoa_chi_so, nguong_sai_so):
    danh_sach_cac_gd = []
    ngay_thuc = [n for n in danh_sach_ngay if du_lieu_ngay[n] is not None]
    if not ngay_thuc: return []
    nhom_hien_tai = [ngay_thuc[0]]
    for i in range(1, len(ngay_thuc)):
        ngay_dang_xet = ngay_thuc[i]
        gia_tri_ngay = du_lieu_ngay[ngay_dang_xet][khoa_chi_so]
        trung_binh_nhom = np.mean([du_lieu_ngay[d][khoa_chi_so] for d in nhom_hien_tai])
        if abs(gia_tri_ngay - trung_binh_nhom) > nguong_sai_so:
            danh_sach_cac_gd.append(nhom_hien_tai); nhom_hien_tai = [ngay_dang_xet]
        else: nhom_hien_tai.append(ngay_dang_xet)
    danh_sach_cac_gd.append(nhom_hien_tai)
    return danh_sach_cac_gd

# =================================================================
# KHUNG 3: TRỰC QUAN HÓA (CHỐNG CO GIÃN)
# =================================================================

def ve_bieu_do_doc(du_lieu_bieu_do, danh_sach_gd, tieu_de, khoa_gia_tri):
    cac_ngay = list(du_lieu_bieu_do.keys())
    gia_tri_ve = []
    mau_ve = []
    bang_mau = ['#2E7D32', '#1565C0', '#C62828', '#AD1457', '#6A1B9A', '#00838F', '#283593']
    
    for ngay in cac_ngay:
        if du_lieu_bieu_do[ngay] is None:
            gia_tri_ve.append(0); mau_ve.append('white')
        else:
            val = du_lieu_bieu_do[ngay].get('gia_tri_ao', du_lieu_bieu_do[ngay][khoa_gia_tri])
            gia_tri_ve.append(val)
            mau_chon = bang_mau[0]
            for idx, gd in enumerate(danh_sach_gd):
                if ngay in gd:
                    mau_chon = bang_mau[idx % len(bang_mau)]; break
            mau_ve.append(mau_chon)

    # ĐIỀU CHỈNH QUAN TRỌNG: 
    # Tính toán chiều rộng theo pixel (DPI) để ép Streamlit không co ảnh
    do_rong_moi_ngay = 60 # 60 pixel cho mỗi ngày
    chieu_rong_px = max(1000, len(cac_ngay) * do_rong_moi_ngay)
    
    # Chuyển pixel sang inch cho Matplotlib (mặc định 100 DPI)
    fig_w = chieu_rong_px / 100
    fig, ax = plt.subplots(figsize=(fig_w, 5), dpi=100)
    
    x_truc = range(len(cac_ngay))
    ax.bar(x_truc, gia_tri_ve, color=mau_ve, width=0.6)
    
    ax.set_title(tieu_de, fontweight='bold', fontsize=16)
    ax.set_xticks(x_truc)
    labels = [cac_ngay[i][-5:] if gia_tri_ve[i] > 0 else "" for i in range(len(cac_ngay))]
    ax.set_xticklabels(labels, rotation=45, fontsize=8)
    
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    
    # Hiển thị biểu đồ và TẮT hoàn toàn việc tự co giãn theo container
    st.pyplot(fig, use_container_width=False)

# =================================================================
# KHUNG 4: GIAO DIỆN VÀ XỬ LÝ
# =================================================================

with st.sidebar:
    st.header("📂 Dữ liệu")
    tep_nho_giot = st.file_uploader("Tải file Nhỏ giọt", type=['json'], accept_multiple_files=True)
    tep_cham_phan = st.file_uploader("Tải file Châm phân", type=['json'], accept_multiple_files=True)
    ngay_bat_dau = st.date_input("Từ ngày", value=None)
    ngay_ket_thuc = st.date_input("Đến ngày", value=None)
    chon_c1 = st.checkbox("Lần tưới", value=True)
    ss_c1 = st.number_input("Sai số giai đoạn", value=GIATRI_GOC["LAN_TUOI"])

if tep_nho_giot:
    du_lieu_tho = []
    for t in tep_nho_giot: du_lieu_tho.extend(json.load(t))
    
    stt_list = sorted(list(set(str(d.get('STT')) for d in du_lieu_tho if d.get('STT'))))
    khu_vuc = st.sidebar.selectbox("🎯 Khu vực", stt_list)

    # Phân tích vụ gốc
    thong_ke_full = {}; thoi_gian_full = {}
    data_kv = sorted([d for d in du_lieu_tho if str(d.get('STT')) == khu_vuc], key=lambda x: x['Thời gian'])
    
    for i in range(len(data_kv)-1):
        if data_kv[i].get('Trạng thái') == "Bật" and data_kv[i+1].get('Trạng thái') == "Tắt":
            try:
                t1 = datetime.strptime(data_kv[i]['Thời gian'], "%Y-%m-%d %H-%M-%S")
                t2 = datetime.strptime(data_kv[i+1]['Thời gian'], "%Y-%m-%d %H-%M-%S")
                dur = (t2-t1).total_seconds()
                if GIATRI_GOC["GIAY_MIN"] <= dur <= GIATRI_GOC["GIAY_MAX"]:
                    d_str = t1.strftime("%Y-%m-%d")
                    thong_ke_full[d_str] = thong_ke_full.get(d_str, 0) + 1
                    thoi_gian_full[d_str] = thoi_gian_full.get(d_str, 0) + dur
            except: continue

    ngay_hl = sorted([datetime.strptime(n, "%Y-%m-%d").date() for n, c in thong_ke_full.items() if c >= GIATRI_GOC["LAN_MIN_NGAY"]])
    danh_sach_vu = []
    if ngay_hl:
        start = ngay_hl[0]
        for i in range(1, len(ngay_hl)):
            if (ngay_hl[i] - ngay_hl[i-1]).days > GIATRI_GOC["GAP_NGAY"]:
                danh_sach_vu.append((start, ngay_hl[i-1])); start = ngay_hl[i]
        danh_sach_vu.append((start, ngay_hl[-1]))

    # Tạo dữ liệu hiển thị liên tục
    all_ngay = sorted(thong_ke_full.keys())
    if all_ngay:
        min_d = ngay_bat_dau if ngay_bat_dau else datetime.strptime(all_ngay[0], "%Y-%m-%d").date()
        max_d = ngay_ket_thuc if ngay_ket_thuc else datetime.strptime(all_ngay[-1], "%Y-%m-%d").date()
        
        data_view = {}
        curr = min_d
        while curr <= max_d:
            d_str = curr.strftime("%Y-%m-%d")
            data_view[d_str] = {'val': thong_ke_full[d_str], 'dur': thoi_gian_full[d_str]} if d_str in thong_ke_full else None
            curr += timedelta(days=1)

        if chon_c1:
            ngay_list = list(data_view.keys())
            ds_gd = chia_giai_doan_tu_dong(ngay_list, data_view, 'val', ss_c1)
            for gd in ds_gd:
                avg = round(np.mean([data_view[d]['val'] for d in gd]))
                for d in gd: data_view[d]['gia_tri_ao'] = avg
            
            # GỌI HÀM VẼ
            ve_bieu_do_doc(data_view, ds_gd, "BIỂU ĐỒ LẦN TƯỚI (Kéo thanh cuộn bên dưới để xem tiếp)", 'val')
            
            # Bảng dữ liệu
            res = []
            for n in ngay_list:
                if data_view[n]:
                    v, nt = xac_dinh_vi_tri_vu(n, danh_sach_vu)
                    res.append({"Ngày": n, "Vị trí": v, "Ngày thứ": nt, "Lần": data_view[n]['val']})
            st.table(res)
