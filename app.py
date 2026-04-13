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

st.set_page_config(page_title="Phân tích Mùa vụ v3.7", layout="wide")

# =================================================================
# KHUNG 2: CÁC THUẬT TOÁN LOGIC TÍNH TOÁN (BỘ NÃO)
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
            stt_trong_vu = (ngay_dt - start).days + 1
            return f"Vụ {i+1}", stt_trong_vu
    return "Khoảng nghỉ", "-"

def chia_giai_doan_tu_dong(danh_sach_ngay, du_lieu_ngay, khoa_chi_so, nguong_sai_so):
    danh_sach_cac_gd = []
    # Loại bỏ các ngày 'None' (khoảng trống) trước khi tính toán giai đoạn
    ngay_thuc = [n for n in danh_sach_ngay if du_lieu_ngay[n] is not None]
    if not ngay_thuc: return []
    
    nhom_hien_tai = [ngay_thuc[0]]
    for i in range(1, len(ngay_thuc)):
        ngay_dang_xet = ngay_thuc[i]
        gia_tri_ngay = du_lieu_ngay[ngay_dang_xet][khoa_chi_so]
        trung_binh_nhom = np.mean([du_lieu_ngay[d][khoa_chi_so] for d in nhom_hien_tai])
        if abs(gia_tri_ngay - trung_binh_nhom) > nguong_sai_so:
            danh_sach_cac_gd.append(nhom_hien_tai)
            nhom_hien_tai = [ngay_dang_xet]
        else: nhom_hien_tai.append(ngay_dang_xet)
    danh_sach_cac_gd.append(nhom_hien_tai)
    return danh_sach_cac_gd

# =================================================================
# KHUNG 3: LOGIC TRỰC QUAN HÓA (XỬ LÝ KHOẢNG TRỐNG VÀ KÍCH THƯỚC)
# =================================================================

def ve_bieu_do_doc(du_lieu_bieu_do, danh_sach_gd, tieu_de, khoa_gia_tri):
    # Lấy danh sách ngày bao gồm cả khoảng trống 'None'
    cac_ngay = list(du_lieu_bieu_do.keys())
    gia_tri_ve = []
    mau_ve = []
    
    bang_mau = ['#2E7D32', '#1565C0', '#C62828', '#AD1457', '#6A1B9A', '#00838F', '#283593']
    
    for ngay in cac_ngay:
        if du_lieu_bieu_do[ngay] is None:
            gia_tri_ve.append(0)
            mau_ve.append('white') # Cột trống
        else:
            val = du_lieu_bieu_do[ngay].get('gia_tri_ao', du_lieu_bieu_do[ngay][khoa_gia_tri])
            gia_tri_ve.append(val)
            # Tìm màu theo giai đoạn
            mau_chon = bang_mau[0]
            for idx, gd in enumerate(danh_sach_gd):
                if ngay in gd:
                    mau_chon = bang_mau[idx % len(bang_mau)]
                    break
            mau_ve.append(mau_chon)

    # ĐIỀU CHỈNH: Kích thước cực đại để không bị bóp
    chieu_rong_moi_cot = 0.8 
    chieu_rong_tong = max(16, len(cac_ngay) * chieu_rong_moi_cot)
    
    fig, ax = plt.subplots(figsize=(chieu_rong_tong, 6))
    x_truc = range(len(cac_ngay))
    
    ax.bar(x_truc, gia_tri_ve, color=mau_ve, width=0.6, edgecolor='none')
    
    ax.set_title(tieu_de, fontweight='bold', fontsize=18, pad=30)
    ax.set_xticks(x_truc)
    # Chỉ hiển thị nhãn ngày cho những cột có dữ liệu, tránh rối mắt
    labels = [cac_ngay[i][-5:] if gia_tri_ve[i] > 0 else "" for i in range(len(cac_ngay))]
    ax.set_xticklabels(labels, rotation=45, fontsize=9)
    
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    st.pyplot(fig)

# =================================================================
# KHUNG 4: LOGIC HIỆU CHỈNH GIAO DIỆN VÀ XỬ LÝ DỮ LIỆU
# =================================================================

with st.sidebar:
    st.header("📂 Dữ liệu & Cấu hình")
    tep_nho_giot = st.file_uploader("Tải file Nhỏ giọt", type=['json'], accept_multiple_files=True)
    tep_cham_phan = st.file_uploader("Tải file Châm phân", type=['json'], accept_multiple_files=True)
    
    st.divider()
    st.subheader("🔍 Lọc thời gian tự do")
    ngay_bat_dau = st.date_input("Từ ngày", value=None)
    ngay_ket_thuc = st.date_input("Đến ngày", value=None)
    
    chon_c1 = st.checkbox("Cách 1: Lần tưới", value=True)
    chon_c2 = st.checkbox("Cách 2: TBEC")
    chon_c3 = st.checkbox("Cách 3: EC Req")
    
    with st.expander("⚙️ Sai số"):
        ss_c1 = st.number_input("Lần tưới", value=GIATRI_GOC["LAN_TUOI"], step=0.1)
        ss_c2 = st.number_input("TBEC", value=GIATRI_GOC["TBEC"], step=0.1)
        ss_c3 = st.number_input("EC Req", value=GIATRI_GOC["EC_REQ"], step=0.1)

if tep_nho_giot:
    du_lieu_tho_ng = []
    for t in tep_nho_giot:
        try: du_lieu_tho_ng.extend(json.load(t))
        except: continue
    
    stt_list = sorted(list(set(str(d.get('STT')) for d in du_lieu_tho_ng if d.get('STT'))))
    khu_vuc = st.sidebar.selectbox("🎯 Khu vực", stt_list)

    # 1. Phân tích vụ gốc
    thong_ke_full = {}
    thoi_gian_full = {}
    data_kv = sorted([d for d in du_lieu_tho_ng if str(d.get('STT')) == khu_vuc], key=lambda x: x['Thời gian'])
    
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

    ngay_hl_full = sorted([datetime.strptime(n, "%Y-%m-%d").date() for n, c in thong_ke_full.items() if c >= GIATRI_GOC["LAN_MIN_NGAY"]])
    danh_sach_vu_goc = []
    if ngay_hl_full:
        start = ngay_hl_full[0]
        for i in range(1, len(ngay_hl_full)):
            if (ngay_hl_full[i] - ngay_hl_full[i-1]).days > GIATRI_GOC["GAP_NGAY"]:
                danh_sach_vu_goc.append((start, ngay_hl_full[i-1]))
                start = ngay_hl_full[i]
        danh_sach_vu_goc.append((start, ngay_hl_full[-1]))

    # 2. Xử lý hiển thị với KHOẢNG TRỐNG
    all_ngay_str = sorted(thong_ke_full.keys())
    if not all_ngay_str: st.stop()
    
    min_date = datetime.strptime(all_ngay_str[0], "%Y-%m-%d").date()
    max_date = datetime.strptime(all_ngay_str[-1], "%Y-%m-%d").date()
    
    # Ghi đè bằng lọc tùy chọn nếu có
    start_view = ngay_bat_dau if ngay_bat_dau else min_date
    end_view = ngay_ket_thuc if ngay_ket_thuc else max_date
    
    # Tạo danh sách ngày liên tục (để thấy được khoảng nghỉ)
    data_with_gaps = {}
    curr = start_view
    while curr <= end_view:
        d_str = curr.strftime("%Y-%m-%d")
        if d_str in thong_ke_full:
            data_with_gaps[d_str] = {'val': thong_ke_full[d_str], 'dur': thoi_gian_full[d_str]}
        else:
            data_with_gaps[d_str] = None # Đánh dấu ngày không có dữ liệu
        curr += timedelta(days=1)

    # Hiển thị
    tabs = st.tabs([t for t, c in zip(["💧 Lần tưới", "🧪 TBEC", "📋 EC Req"], [chon_c1, chon_c2, chon_c3]) if c])
    tab_idx = 0
    
    if chon_c1:
        with tabs[tab_idx]:
            ngay_hien_thi = list(data_with_gaps.keys())
            ds_gd = chia_giai_doan_tu_dong(ngay_hien_thi, data_with_gaps, 'val', ss_c1)
            # Tính giá trị ảo cho giai đoạn
            for gd in ds_gd:
                avg = round(np.mean([data_with_gaps[d]['val'] for d in gd]))
                for d in gd: data_with_gaps[d]['gia_tri_ao'] = avg
            
            ve_bieu_do_doc(data_with_gaps, ds_gd, "Biểu đồ Lần tưới (Có khoảng nghỉ giữa các vụ)", 'val')
            
            # Bảng chi tiết (Chỉ hiện ngày có dữ liệu)
            res = []
            for n in ngay_hien_thi:
                if data_with_gaps[n] is not None:
                    tv, nt = xac_dinh_vi_tri_vu(n, danh_sach_vu_goc)
                    m, s = int(data_with_gaps[n]['dur']//60), int(data_with_gaps[n]['dur']%60)
                    res.append({"Ngày": n, "Vị trí": tv, "Ngày thứ": nt, "Lần": data_with_gaps[n]['val'], "TG": f"{m:02d}:{s:02d}"})
            st.table(res)
