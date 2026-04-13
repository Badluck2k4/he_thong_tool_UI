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

st.set_page_config(page_title="Phân tích Mùa vụ Đa biến v3.0", layout="wide")

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

def chia_giai_doan_da_bien(danh_sach_ngay, du_lieu_tong_hop, cau_hinh_nguong):
    """
    Chia giai đoạn dựa trên sự biến thiên đồng thời của nhiều chỉ số.
    Sử dụng List và Dict thuần, không dùng Pandas.
    """
    danh_sach_cac_gd = []
    if not danh_sach_ngay:
        return danh_sach_cac_gd

    nhom_hien_tai = [danh_sach_ngay[0]]

    for i in range(1, len(danh_sach_ngay)):
        ngay_dang_xet = danh_sach_ngay[i]
        ngat_giai_doan = False
        
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
                    
                    if (sai_so > nguong_sai_so and len(nhom_hien_tai) >= 3) or (sai_so > nguong_sai_so * 3):
                        ngat_giai_doan = True
                        break

        if ngat_giai_doan:
            danh_sach_cac_gd.append(nhom_hien_tai)
            nhom_hien_tai = [ngay_dang_xet]
        else:
            nhom_hien_tai.append(ngay_dang_xet)

    danh_sach_cac_gd.append(nhom_hien_tai)
    return danh_sach_cac_gd

def ve_bieu_do_da_bien(du_lieu_bieu_do, danh_sach_gd, tieu_de, khoa_gia_tri):
    cac_ngay_dao_nguoc = sorted(du_lieu_bieu_do.keys(), reverse=True)
    ngay_hien_thi = [n for n in cac_ngay_dao_nguoc if du_lieu_bieu_do[n].get(khoa_gia_tri) is not None]
    
    if not ngay_hien_thi:
        return

    gia_tri_cot = [du_lieu_bieu_do[n][khoa_gia_tri] for n in ngay_hien_thi]
    
    bang_mau = ['#2E7D32', '#1565C0', '#C62828', '#AD1457', '#6A1B9A', '#00838F', '#283593']
    mau_tung_cot = []
    for ngay in ngay_hien_thi:
        mau_chon = bang_mau[0]
        for idx, gd in enumerate(danh_sach_gd):
            if ngay in gd:
                mau_chon = bang_mau[idx % len(bang_mau)]
                break
        mau_tung_cot.append(mau_chon)

    fig, ax = plt.subplots(figsize=(10, len(ngay_hien_thi)*0.4 + 2))
    ax.barh(ngay_hien_thi, gia_tri_cot, color=mau_tung_cot, alpha=0.8)
    for i, v in enumerate(gia_tri_cot):
        ax.text(v, i, f" {v:.2f}", va='center')
    ax.set_title(tieu_de, fontweight='bold')
    st.pyplot(fig)

# --- 3. GIAO DIỆN 1 (SIDEBAR) ---
with st.sidebar:
    st.header("📂 Dữ liệu & Cấu hình")
    tep_nho_giot = st.file_uploader("Tải file Nhỏ giọt", type=['json'], accept_multiple_files=True)
    tep_cham_phan = st.file_uploader("Tải file Châm phân", type=['json'], accept_multiple_files=True)
    
    st.divider()
    st.subheader("⚙️ Ngưỡng sai số đồng thời")
    ss_lan_tuoi = st.number_input("Sai số Lần tưới", value=GIATRI_GOC["LAN_TUOI"], step=0.1)
    ss_tbec = st.number_input("Sai số TBEC", value=GIATRI_GOC["TBEC"], step=0.1)
    ss_ecreq = st.number_input("Sai số EC Req", value=GIATRI_GOC["EC_REQ"], step=0.1)

# --- 4. GIAO DIỆN 2 (MAINBODY) ---
if tep_nho_giot:
    du_lieu_tho_ng = []
    for t in tep_nho_giot: 
        du_lieu_tho_ng.extend(json.load(t))
    
    danh_sach_stt = sorted(list(set(str(d.get('STT')) for d in du_lieu_tho_ng if d.get('STT'))))
    khu_vuc_chon = st.sidebar.selectbox("🎯 Chọn khu vực (STT)", danh_sach_stt)

    # A. Xử lý dữ liệu Nhỏ giọt
    thong_ke_tuoi_ngay = {}
    data_loc = sorted([d for d in du_lieu_tho_ng if str(d.get('STT')) == khu_vuc_chon], key=lambda x: x['Thời gian'])
    
    for i in range(len(data_loc)-1):
        if data_loc[i].get('Trạng thái') == "Bật" and data_loc[i+1].get('Trạng thái') == "Tắt":
            tg_bat = datetime.strptime(data_loc[i]['Thời gian'], "%Y-%m-%d %H-%M-%S")
            tg_tat = datetime.strptime(data_loc[i+1]['Thời gian'], "%Y-%m-%d %H-%M-%S")
            thoi_luong = (tg_tat - tg_bat).total_seconds()
            if GIATRI_GOC["GIAY_MIN"] <= thoi_luong <= GIATRI_GOC["GIAY_MAX"]:
                ngay_key = tg_bat.strftime("%Y-%m-%d")
                thong_ke_tuoi_ngay[ngay_key] = thong_ke_tuoi_ngay.get(ngay_key, 0) + 1

    ngay_du_dieu_kien = sorted([datetime.strptime(n, "%Y-%m-%d").date() for n, c in thong_ke_tuoi_ngay.items() if c >= GIATRI_GOC["LAN_MIN_NGAY"]])
    
    if ngay_du_dieu_kien:
        danh_sach_vu_mua = []
        ngay_bat_dau_vu = ngay_du_dieu_kien[0]
        for i in range(1, len(ngay_du_dieu_kien)):
            if (ngay_du_dieu_kien[i] - ngay_du_dieu_kien[i-1]).days > GIATRI_GOC["GAP_NGAY"]:
                if (ngay_du_dieu_kien[i-1] - ngay_bat_dau_vu).days + 1 >= GIATRI_GOC["MIN_VU"]:
                    danh_sach_vu_mua.append((ngay_bat_dau_vu, ngay_du_dieu_kien[i-1]))
                ngay_bat_dau_vu = ngay_du_dieu_kien[i]
        danh_sach_vu_mua.append((ngay_bat_dau_vu, ngay_du_dieu_kien[-1]))

        chon_vu = st.selectbox("📅 Chọn mùa vụ", [f"Vụ {i+1}: {v[0]} đến {v[1]}" for i, v in enumerate(danh_sach_vu_mua)])
        chi_so_vu = int(chon_vu.split(':')[0].split()[1]) - 1
        vu_hien_tai = danh_sach_vu_mua[chi_so_vu]

        # B. Xử lý dữ liệu Châm phân
        du_lieu_cham_phan_ngay = {}
        if tep_cham_phan:
            data_cp_raw = []
            for t in tep_cham_phan: 
                data_cp_raw.extend(json.load(t))
            
            for item in data_cp_raw:
                if str(item.get('STT')) != khu_vuc_chon: continue
                tg_obj = datetime.strptime(item['Thời gian'], "%Y-%m-%d %H-%M-%S")
                if vu_hien_tai[0] <= tg_obj.date() <= vu_hien_tai[1]:
                    n_key = tg_obj.strftime("%Y-%m-%d")
                    if n_key not in du_lieu_cham_phan_ngay: 
                        du_lieu_cham_phan_ngay[n_key] = {'tbec_list': [], 'ecreq_list': []}
                    
                    val_tbec = chuyen_doi_so_thuc(item, ['TBEC', 'tbec'])
                    val_req = chuyen_doi_so_thuc(item, ['EC yêu cầu', 'ecreq'])
                    if val_tbec: du_lieu_cham_phan_ngay[n_key]['tbec_list'].append(val_tbec)
                    if val_req: du_lieu_cham_phan_ngay[n_key]['ecreq_list'].append(val_req)
        
        # C. Hợp nhất dữ liệu không dùng Pandas
        du_lieu_tong_hop = {}
        tat_ca_ngay_trong_vu = sorted([n for n in thong_ke_tuoi_ngay if vu_hien_tai[0] <= datetime.strptime(n, "%Y-%m-%d").date() <= vu_hien_tai[1]])
        
        for n in tat_ca_ngay_trong_vu:
            du_lieu_tong_hop[n] = {
                'so_lan_tuoi': thong_ke_tuoi_ngay.get(n),
                'tbec': np.mean(du_lieu_cham_phan_ngay[n]['tbec_list']) if n in du_lieu_cham_phan_ngay and du_lieu_cham_phan_ngay[n]['tbec_list'] else None,
                'ecreq': np.mean(du_lieu_cham_phan_ngay[n]['ecreq_list']) if n in du_lieu_cham_phan_ngay and du_lieu_cham_phan_ngay[n]['ecreq_list'] else None
            }
        
        # D. Chia giai đoạn dựa trên biến thiên đồng thời
        nguong_cau_hinh = {
            'so_lan_tuoi': ss_lan_tuoi,
            'tbec': ss_tbec,
            'ecreq': ss_ecreq
        }
        
        danh_sach_giai_doan = chia_giai_doan_da_bien(tat_ca_ngay_trong_vu, du_lieu_tong_hop, nguong_cau_hinh)

        # E. Hiển thị kết quả
        st.subheader(f"Kết quả phân tích: {len(danh_sach_giai_doan)} giai đoạn được tìm thấy")
        
        tab1, tab2, tab3 = st.tabs(["💧 Lần tưới", "🧪 TBEC", "📋 EC Yêu cầu"])
        
        with tab1:
            ve_bieu_do_da_bien(du_lieu_tong_hop, danh_sach_giai_doan, "Biến thiên Lần tưới theo Giai đoạn", 'so_lan_tuoi')
        with tab2:
            ve_bieu_do_da_bien(du_lieu_tong_hop, danh_sach_giai_doan, "Biến thiên TBEC theo Giai đoạn", 'tbec')
        with tab3:
            ve_bieu_do_da_bien(du_lieu_tong_hop, danh_sach_giai_doan, "Biến thiên EC Yêu cầu theo Giai đoạn", 'ecreq')

        # Bảng chi tiết (Dùng st.table hoặc st.write thay cho dataframe nếu muốn tránh pandas hoàn toàn)
        st.divider()
        st.write("### Chi tiết các giai đoạn")
        du_lieu_bang = []
        for i, gd in enumerate(danh_sach_giai_doan):
            for n in gd:
                du_lieu_bang.append({
                    "Giai đoạn": i + 1,
                    "Ngày": n,
                    "Số lần tưới": du_lieu_tong_hop[n]['so_lan_tuoi'],
                    "TBEC": round(du_lieu_tong_hop[n]['tbec'], 2) if du_lieu_tong_hop[n]['tbec'] else "-",
                    "EC Yêu cầu": round(du_lieu_tong_hop[n]['ecreq'], 2) if du_lieu_tong_hop[n]['ecreq'] else "-"
                })
        st.table(du_lieu_bang)

    else:
        st.error("Không tìm thấy dữ liệu mùa vụ hợp lệ.")
else:
    st.info("👋 Vui lòng tải file dữ liệu ở thanh bên để bắt đầu.")
