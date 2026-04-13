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

st.set_page_config(page_title="Phân tích Mùa vụ v3.6", layout="wide")

# =================================================================
# KHUNG 2: CÁC THUẬT TOÁN LOGIC TÍNH TOÁN (CORE LOGIC)
# =================================================================

def chuyen_doi_so_thuc(du_lieu, danh_sach_khoa):
    for khoa in danh_sach_khoa:
        gia_tri = du_lieu.get(khoa)
        if gia_tri is not None:
            try: return float(str(gia_tri).replace(',', '.'))
            except: continue
    return None

def chia_giai_doan_tu_dong(danh_sach_ngay, du_lieu_ngay, khoa_chi_so, nguong_sai_so):
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

def xac_dinh_vi_tri_vu(ngay_dang_xet_str, danh_sach_vu):
    ngay_dt = datetime.strptime(ngay_dang_xet_str, "%Y-%m-%d").date()
    for i, (start, end) in enumerate(danh_sach_vu):
        if start <= ngay_dt <= end:
            stt_trong_vu = (ngay_dt - start).days + 1
            return f"Vụ {i+1}", stt_trong_vu
    return "Ngoài vụ", "-"

# =================================================================
# KHUNG 3: LOGIC TRỰC QUAN HÓA (ĐÃ HIỆU CHỈNH KÍCH THƯỚC)
# =================================================================

def ve_bieu_do_doc(du_lieu_bieu_do, danh_sach_gd, tieu_de, khoa_gia_tri):
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

    # --- ĐIỀU CHỈNH KÍCH THƯỚC TẠI ĐÂY ---
    # Tăng hệ số nhân từ 0.35 lên 0.6 để biểu đồ dài ra, không bị bóp
    chieu_rong = max(15, len(cac_ngay) * 0.6) 
    fig, ax = plt.subplots(figsize=(chieu_rong, 6)) # Tăng chiều cao lên 6
    
    # width=0.6: Làm cột hẹp lại một chút để tạo khoảng cách giữa các cột lớn hơn
    ax.bar(so_thu_tu, gia_tri_hien_thi, color=mau_cot, alpha=0.8, width=0.6)
    
    ax.set_title(tieu_de, fontweight='bold', fontsize=16, pad=25)
    ax.set_xlabel("Số thứ tự hiển thị (STT)", fontsize=12)
    ax.set_xticks(so_thu_tu)
    plt.grid(axis='y', linestyle='--', alpha=0.4)
    
    # Hiển thị biểu đồ chiếm trọn chiều ngang container
    st.pyplot(fig, use_container_width=True)

# =================================================================
# KHUNG 4: LOGIC HIỆU CHỈNH GIAO DIỆN (UI)
# =================================================================

with st.sidebar:
    st.header("📂 Dữ liệu & Cấu hình")
    tep_nho_giot = st.file_uploader("Tải file Nhỏ giọt", type=['json'], accept_multiple_files=True)
    tep_cham_phan = st.file_uploader("Tải file Châm phân", type=['json'], accept_multiple_files=True)
    
    st.divider()
    st.subheader("🔍 Khoảng thời gian tự do")
    ngay_bat_dau = st.date_input("Từ ngày", value=None)
    ngay_ket_thuc = st.date_input("Đến ngày", value=None)

    st.divider()
    st.subheader("🛠 Hiển thị")
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

# --- Xử lý dữ liệu chính ---
if tep_nho_giot:
    du_lieu_tho_ng = []
    for t in tep_nho_giot:
        try: du_lieu_tho_ng.extend(json.load(t))
        except: continue
    
    stt_list = sorted(list(set(str(d.get('STT')) for d in du_lieu_tho_ng if d.get('STT'))))
    khu_vuc = st.sidebar.selectbox("🎯 Khu vực", stt_list)

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
                if (ngay_hl_full[i-1] - start).days + 1 >= GIATRI_GOC["MIN_VU"]:
                    danh_sach_vu_goc.append((start, ngay_hl_full[i-1]))
                start = ngay_hl_full[i]
        danh_sach_vu_goc.append((start, ngay_hl_full[-1]))

    ngay_da_loc = [n for n in sorted(thong_ke_full.keys()) if (not ngay_bat_dau or datetime.strptime(n, "%Y-%m-%d").date() >= ngay_bat_dau) and (not ngay_ket_thuc or datetime.strptime(n, "%Y-%m-%d").date() <= ngay_ket_thuc)]

    if ngay_da_loc:
        tabs = st.tabs([t for t, c in zip(["💧 Lần tưới", "🧪 TBEC", "📋 EC Req"], [chon_c1, chon_c2, chon_c3]) if c])
        tab_idx = 0
        
        if chon_c1:
            with tabs[tab_idx]:
                data_view = {n: {'val': thong_ke_full[n], 'dur': thoi_gian_full[n]} for n in ngay_da_loc}
                ds_gd = chia_giai_doan_tu_dong(ngay_da_loc, data_view, 'val', ss_c1)
                for gd in ds_gd:
                    avg = round(np.mean([data_view[d]['val'] for d in gd]))
                    for d in gd: data_view[d]['gia_tri_ao'] = avg
                ve_bieu_do_doc(data_view, ds_gd, "Biểu đồ Lần tưới", 'val')
                st.table([{"Ngày": n, "Vị trí": xac_dinh_vi_tri_vu(n, danh_sach_vu_goc)[0], "Ngày thứ": xac_dinh_vi_tri_vu(n, danh_sach_vu_goc)[1], "Lần tưới": data_view[n]['val'], "Tổng TG": f"{int(data_view[n]['dur']//60):02d}:{int(data_view[n]['dur']%60):02d}", "GD": i+1} for i, gd in enumerate(ds_gd) for n in gd])
            tab_idx += 1

        if (chon_c2 or chon_c3) and tep_cham_phan:
            data_cp_tho = []
            for t in tep_cham_phan: data_cp_tho.extend(json.load(t))
            thong_ke_cp = {}
            for item in data_cp_tho:
                if str(item.get('STT')) != khu_vuc: continue
                try:
                    dt = datetime.strptime(item['Thời gian'], "%Y-%m-%d %H-%M-%S")
                    curr_d = dt.date()
                    if (ngay_bat_dau and curr_d < ngay_bat_dau) or (ngay_ket_thuc and curr_d > ngay_ket_thuc): continue
                    n_str = dt.strftime("%Y-%m-%d")
                    if n_str not in thong_ke_cp: thong_ke_cp[n_str] = {'tbec': [], 'ecreq': []}
                    vt, vr = chuyen_doi_so_thuc(item, ['TBEC', 'tbec']), chuyen_doi_so_thuc(item, ['EC yêu cầu', 'ecreq'])
                    if vt is not None: thong_ke_cp[n_str]['tbec'].append(vt)
                    if vr is not None: thong_ke_cp[n_str]['ecreq'].append(vr)
                except: continue
            data_chot_cp = {n: {'tbec': np.mean(v['tbec']), 'ecreq': np.mean(v['ecreq'])} for n, v in thong_ke_cp.items() if v['tbec'] or v['ecreq']}
            ngay_cp = sorted(data_chot_cp.keys())

            if chon_c2 and ngay_cp:
                with tabs[tab_idx]:
                    ds_gd2 = chia_giai_doan_tu_dong(ngay_cp, data_chot_cp, 'tbec', ss_c2)
                    ve_bieu_do_doc(data_chot_cp, ds_gd2, "Biểu đồ TBEC", 'tbec')
                    st.table([{"Ngày": n, "Vị trí": xac_dinh_vi_tri_vu(n, danh_sach_vu_goc)[0], "Ngày thứ": xac_dinh_vi_tri_vu(n, danh_sach_vu_goc)[1], "TBEC": round(data_chot_cp[n]['tbec'],2), "GD": i+1} for i, gd in enumerate(ds_gd2) for n in gd])
                tab_idx += 1
            if chon_c3 and ngay_cp:
                with tabs[tab_idx]:
                    ds_gd3 = chia_giai_doan_tu_dong(ngay_cp, data_chot_cp, 'ecreq', ss_c3)
                    ve_bieu_do_doc(data_chot_cp, ds_gd3, "Biểu đồ EC Req", 'ecreq')
                    st.table([{"Ngày": n, "Vị trí": xac_dinh_vi_tri_vu(n, danh_sach_vu_goc)[0], "Ngày thứ": xac_dinh_vi_tri_vu(n, danh_sach_vu_goc)[1], "EC Req": round(data_chot_cp[n]['ecreq'],2), "GD": i+1} for i, gd in enumerate(ds_gd3) for n in gd])
