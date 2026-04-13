import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# --- 1. CẤU HÌNH HẰNG SỐ GỐC ---
GIATRI_GOC = {
    "LAN_TUOI": 2.5,
    "TBEC": 8.0,
    "EC_REQ": 5.0,
    "GIAY_MIN": 20,
    "GIAY_MAX": 3600,
    "LAN_MIN_NGAY": 5,
    "GAP_NGAY": 2,
    "MIN_VU": 7
}

st.set_page_config(page_title="Phân tích Mùa vụ Đa biến v4.3", layout="wide")

# --- 2. CÁC HÀM LOGIC ---

def chuyen_doi_so_thuc(du_lieu, danh_sach_khoa):
    for khoa in danh_sach_khoa:
        gia_tri = du_lieu.get(khoa)
        if gia_tri is not None:
            try:
                return float(str(gia_tri).replace(',', '.'))
            except ValueError:
                continue
    return None

def chia_giai_doan_bien_thien_dong_thoi(danh_sach_ngay, du_lieu_tong_hop, cau_hinh_nguong):
    danh_sach_cac_gd = []
    if not danh_sach_ngay:
        return danh_sach_cac_gd

    nhom_hien_tai = [danh_sach_ngay[0]]

    for i in range(1, len(danh_sach_ngay)):
        ngay_dang_xet = danh_sach_ngay[i]
        ket_qua_kiem_tra = []
        
        for khoa_chi_so, nguong_sai_so in cau_hinh_nguong.items():
            gia_tri_ngay = du_lieu_tong_hop[ngay_dang_xet].get(khoa_chi_so)
            
            if gia_tri_ngay is not None:
                danh_sach_gia_tri_nhom = [
                    du_lieu_tong_hop[d][khoa_chi_so] 
                    for d in nhom_hien_tai 
                    if du_lieu_tong_hop[d].get(khoa_chi_so) is not None
                ]
                
                if danh_sach_gia_tri_nhom:
                    trung_binh_nhom = np.mean(danh_sach_gia_tri_nhom)
                    sai_so = abs(gia_tri_ngay - trung_binh_nhom)
                    
                    vuot = (sai_so > nguong_sai_so and len(nhom_hien_tai) >= 3) or (sai_so > nguong_sai_so * 3)
                    ket_qua_kiem_tra.append(vuot)

        if ket_qua_kiem_tra and all(ket_qua_kiem_tra):
            danh_sach_cac_gd.append(nhom_hien_tai)
            nhom_hien_tai = [ngay_dang_xet]
        else:
            nhom_hien_tai.append(ngay_dang_xet)

    danh_sach_cac_gd.append(nhom_hien_tai)
    return danh_sach_cac_gd

def ve_bieu_do_cot_ngang(du_lieu_bieu_do, danh_sach_gd, tieu_de, khoa_gia_tri):
    cac_ngay_dao = sorted(du_lieu_bieu_do.keys(), reverse=True)
    ngay_co_so = [n for n in cac_ngay_dao if du_lieu_bieu_do[n].get(khoa_gia_tri) is not None]
    
    if not ngay_co_so:
        return

    gia_tri_hien_thi = [du_lieu_bieu_do[n][khoa_gia_tri] for n in ngay_co_so]
    
    bang_mau = ['#2E7D32', '#1565C0', '#C62828', '#AD1457', '#6A1B9A', '#00838F', '#283593']
    mau_cot = []
    for ngay in ngay_co_so:
        mau_chon = bang_mau[0]
        for idx, gd in enumerate(danh_sach_gd):
            if ngay in gd:
                mau_chon = bang_mau[idx % len(bang_mau)]
                break
        mau_cot.append(mau_chon)

    fig, ax = plt.subplots(figsize=(10, len(ngay_co_so)*0.4 + 2))
    ax.barh(ngay_co_so, gia_tri_hien_thi, color=mau_cot, alpha=0.8)
    
    for i, v in enumerate(gia_tri_hien_thi):
        ax.text(v, i, f" {v:.2f}", va='center', fontsize=9)
        
    ax.set_title(tieu_de, fontweight='bold')
    st.pyplot(fig)

# --- 3. GIAO DIỆN 1 (SIDEBAR) ---
with st.sidebar:
    st.header("📂 Dữ liệu & Cấu hình")
    tep_nho_giot = st.file_uploader("Tải file Nhỏ giọt", type=['json'], accept_multiple_files=True)
    tep_cham_phan = st.file_uploader("Tải file Châm phân", type=['json'], accept_multiple_files=True)
    
    st.divider()
    st.subheader("⚙️ Ngưỡng ngắt GD (Đồng thời)")
    ss_lan = st.number_input("Sai số Lần tưới", value=GIATRI_GOC["LAN_TUOI"], step=0.1)
    ss_tbec = st.number_input("Sai số TBEC", value=GIATRI_GOC["TBEC"], step=0.1)
    ss_req = st.number_input("Sai số EC Req", value=GIATRI_GOC["EC_REQ"], step=0.1)

# --- 4. GIAO DIỆN 2 (MAINBODY) ---
if tep_nho_giot:
    du_lieu_tho_ng = []
    for t in tep_nho_giot: du_lieu_tho_ng.extend(json.load(t))
    
    stt_list = sorted(list(set(str(d.get('STT')) for d in du_lieu_tho_ng if d.get('STT'))))
    khu_vuc = st.sidebar.selectbox("🎯 Chọn khu vực (STT)", stt_list)

    thong_ke_ngay = {}
    data_kv = sorted([d for d in du_lieu_tho_ng if str(d.get('STT')) == khu_vuc], key=lambda x: x['Thời gian'])
    for i in range(len(data_kv)-1):
        if data_kv[i].get('Trạng thái') == "Bật" and data_kv[i+1].get('Trạng thái') == "Tắt":
            t1 = datetime.strptime(data_kv[i]['Thời gian'], "%Y-%m-%d %H-%M-%S")
            t2 = datetime.strptime(data_kv[i+1]['Thời gian'], "%Y-%m-%d %H-%M-%S")
            if GIATRI_GOC["GIAY_MIN"] <= (t2 - t1).total_seconds() <= GIATRI_GOC["GIAY_MAX"]:
                d_str = t1.strftime("%Y-%m-%d")
                thong_ke_ngay[d_str] = thong_ke_ngay.get(d_str, 0) + 1

    ngay_ok = sorted([datetime.strptime(n, "%Y-%m-%d").date() for n, c in thong_ke_ngay.items() if c >= GIATRI_GOC["LAN_MIN_NGAY"]])
    
    if ngay_ok:
        danh_sach_vu = []
        start = ngay_ok[0]
        for i in range(1, len(ngay_ok)):
            if (ngay_ok[i] - ngay_ok[i-1]).days > GIATRI_GOC["GAP_NGAY"]:
                if (ngay_ok[i-1] - start).days + 1 >= GIATRI_GOC["MIN_VU"]:
                    danh_sach_vu.append((start, ngay_ok[i-1]))
                start = ngay_ok[i]
        danh_sach_vu.append((start, ngay_ok[-1]))

        chon_vu = st.selectbox("📅 Chọn mùa vụ", [f"Vụ {i+1}: {v[0]} đến {v[1]}" for i, v in enumerate(danh_sach_vu)])
        v_hien_tai = danh_sach_vu[int(chon_vu.split(':')[0].split()[1])-1]

        data_cp_ngay = {}
        if tep_cham_phan:
            for t in tep_cham_phan:
                for item in json.load(t):
                    if str(item.get('STT')) != khu_vuc: continue
                    dt = datetime.strptime(item['Thời gian'], "%Y-%m-%d %H-%M-%S")
                    if v_hien_tai[0] <= dt.date() <= v_hien_tai[1]:
                        n_str = dt.strftime("%Y-%m-%d")
                        if n_str not in data_cp_ngay: data_cp_ngay[n_str] = {'tbec': [], 'req': []}
                        v1 = chuyen_doi_so_thuc(item, ['TBEC', 'tbec'])
                        v2 = chuyen_doi_so_thuc(item, ['EC yêu cầu', 'ecreq'])
                        if v1: data_cp_ngay[n_str]['tbec'].append(v1)
                        if v2: data_cp_ngay[n_str]['req'].append(v2)

        du_lieu_tong_hop = {}
        ngay_vu = sorted([n for n in thong_ke_ngay if v_hien_tai[0] <= datetime.strptime(n, "%Y-%m-%d").date() <= v_hien_tai[1]])
        for n in ngay_vu:
            # LÀM TRÒN NGAY KHI TÍNH TOÁN TRUNG BÌNH
            tbec_tb = np.mean(data_cp_ngay[n]['tbec']) if n in data_cp_ngay and data_cp_ngay[n]['tbec'] else 0
            req_tb = np.mean(data_cp_ngay[n]['req']) if n in data_cp_ngay and data_cp_ngay[n]['req'] else 0
            
            du_lieu_tong_hop[n] = {
                'so_lan_tuoi': thong_ke_ngay[n],
                'tbec': round(float(tbec_tb), 2),
                'ecreq': round(float(req_tb), 2)
            }

        nguong_ngat = {'so_lan_tuoi': ss_lan, 'tbec': ss_tbec, 'ecreq': ss_req}
        ds_giai_doan = chia_giai_doan_bien_thien_dong_thoi(ngay_vu, du_lieu_tong_hop, nguong_ngat)

        st.write(f"### Phân tích: {len(ds_giai_doan)} giai đoạn")
        
        tab1, tab2, tab3 = st.tabs(["💧 Lần tưới", "🧪 TBEC", "📋 EC Yêu cầu"])
        with tab1:
            ve_bieu_do_cot_ngang(du_lieu_tong_hop, ds_giai_doan, "Lần tưới theo Giai đoạn", 'so_lan_tuoi')
        with tab2:
            ve_bieu_do_cot_ngang(du_lieu_tong_hop, ds_giai_doan, "TBEC theo Giai đoạn", 'tbec')
        with tab3:
            ve_bieu_do_cot_ngang(du_lieu_tong_hop, ds_giai_doan, "EC Yêu cầu theo Giai đoạn", 'ecreq')

        st.divider()
        st.write("### Chi tiết số liệu")
        bang_du_lieu = []
        for i, gd in enumerate(ds_giai_doan):
            for n in gd:
                bang_du_lieu.append({
                    "Giai đoạn": i + 1,
                    "Ngày": n,
                    "Số lần tưới": du_lieu_tong_hop[n]['so_lan_tuoi'],
                    "TBEC": du_lieu_tong_hop[n]['tbec'],
                    "EC Yêu cầu": du_lieu_tong_hop[n]['ecreq']
                })
        st.table(bang_du_lieu)
else:
    st.info("👋 Vui lòng tải file dữ liệu ở thanh bên.")
