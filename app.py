import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# --- 1. CẤU HÌNH HẰNG SỐ (TIẾNG VIỆT) ---
GIAY_TUOI_TOI_THIEU = 20
GIAY_TUOI_TOI_DA = 3600
LAN_TUOI_TOI_THIEU_NGAY = 5
KHOANG_CACH_NGAY_NGAT_VU = 2
SO_NGAY_TOI_THIEU_VU = 7

# Ngưỡng chia giai đoạn
NGUONG_NGAT_LAN_TUOI = 2.5   # Cách 1
NGUONG_NGAT_TBEC = 8.0       # Cách 2
NGUONG_NGAT_EC_YEU_CAU = 5.0 # Cách 3
SO_NGAY_TOI_THIEU_GD = 3

st.set_page_config(page_title="Hệ thống Phân tích Tưới & Dinh dưỡng", layout="wide")

# --- 2. CÁC HÀM LOGIC (TIẾNG VIỆT) ---

def chuyen_doi_so_thuc(du_lieu, danh_sach_khoa):
    """Chuyển đổi dữ liệu từ file JSON sang số thực, xử lý dấu phẩy"""
    for khoa in danh_sach_khoa:
        gia_tri = du_lieu.get(khoa)
        if gia_tri is not None:
            try:
                return float(str(gia_tri).replace(',', '.'))
            except ValueError:
                continue
    return None

def chia_giai_doan_tu_dong(danh_sach_ngay, du_lieu_ngay, khoa_chi_so, nguong_sai_so):
    """Chia các ngày thành từng giai đoạn dựa trên biến động chỉ số"""
    danh_sach_cac_gd = []
    if not danh_sach_ngay: return danh_sach_cac_gd
    
    nhom_hien_tai = [danh_sach_ngay[0]]
    for i in range(1, len(danh_sach_ngay)):
        ngay_dang_xet = danh_sach_ngay[i]
        gia_tri_ngay = du_lieu_ngay[ngay_dang_xet][khoa_chi_so]
        trung_binh_nhom = np.mean([du_lieu_ngay[d][khoa_chi_so] for d in nhom_hien_tai])
        
        sai_so_thuc_te = abs(gia_tri_ngay - trung_binh_nhom)
        
        # Ngắt giai đoạn nếu vượt ngưỡng và đủ ngày, hoặc vượt gấp 3 lần ngưỡng (ngắt ngay)
        if (sai_so_thuc_te > nguong_sai_so and len(nhom_hien_tai) >= SO_NGAY_TOI_THIEU_GD) or (sai_so_thuc_te > nguong_sai_so * 3):
            danh_sach_cac_gd.append(nhom_hien_tai)
            nhom_hien_tai = [ngay_dang_xet]
        else:
            nhom_hien_tai.append(ngay_dang_xet)
            
    danh_sach_cac_gd.append(nhom_hien_tai)
    return danh_sach_cac_gd

def ve_bieu_do_da_sac(du_lieu_bieu_do, danh_sach_gd, tieu_de, khoa_gia_tri):
    """Vẽ biểu đồ cột ngang với màu sắc phân biệt theo giai đoạn"""
    if not du_lieu_bieu_do:
        return st.warning("Không có dữ liệu để hiển thị biểu đồ.")

    cac_ngay = sorted(du_lieu_bieu_do.keys(), reverse=True)
    gia_tri_hien_thi = []
    gia_tri_thuc_te = []
    
    for ngay in cac_ngay:
        thong_tin = du_lieu_bieu_do[ngay]
        gia_tri_thuc = thong_tin.get(khoa_gia_tri, 0)
        gia_tri_thuc_te.append(gia_tri_thuc)
        # Cách 1 có giá trị ảo để biểu đồ đẹp, Cách 2-3 dùng giá trị thật
        gia_tri_hien_thi.append(thong_tin.get('gia_tri_ao', gia_tri_thuc))
    
    bang_mau = ['#2E7D32', '#1565C0', '#C62828', '#AD1457', '#6A1B9A', '#0277BD', '#00695C', '#EF6C00', '#D84315', '#4E342E']
    mau_cac_cot = []
    for ngay in cac_ngay:
        mau_chon = bang_mau[0]
        for chi_so, gd in enumerate(danh_sach_gd):
            if ngay in gd:
                mau_chon = bang_mau[chi_so % len(bang_mau)]
                break
        mau_cac_cot.append(mau_chon)

    do_cao_bieu_do = min(15, max(5, len(cac_ngay) * 0.4))
    hinh_anh, truc_to_do = plt.subplots(figsize=(10, do_cao_bieu_do))
    truc_to_do.barh(cac_ngay, gia_tri_hien_thi, color=mau_cac_cot, alpha=0.8)
    
    if khoa_gia_tri == 'so_lan_tuoi':
        truc_to_do.axvline(x=LAN_TUOI_TOI_THIEU_NGAY, color='red', linestyle='--', alpha=0.5)
    
    truc_to_do.set_title(tieu_de, fontsize=12, fontweight='bold')
    gia_tri_lon_nhat = max(gia_tri_hien_thi) if gia_tri_hien_thi else 1
    
    for i, (val_ao, val_thuc) in enumerate(zip(gia_tri_hien_thi, gia_tri_thuc_te)):
        nhan_chu = f"{val_thuc:.2f}" if khoa_gia_tri != 'so_lan_tuoi' else f"{int(val_thuc)}"
        truc_to_do.text(val_ao + (gia_tri_lon_nhat * 0.02), i, nhan_chu, va='center', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    st.pyplot(hinh_anh)

# --- 3. GIAO DIỆN VÀ XỬ LÝ CHÍNH ---

with st.sidebar:
    st.header("📂 Tải tệp dữ liệu")
    tep_nho_giot = st.file_uploader("1. File Nhỏ giọt (Gốc vụ)", type=['json'], accept_multiple_files=True)
    tep_cham_phan = st.file_uploader("2. File Châm phân", type=['json'], accept_multiple_files=True)

st.title("📊 Hệ thống Phân tích Giai đoạn Mùa vụ")

if tep_nho_giot:
    du_lieu_tho_nho_giot = []
    for tep in tep_nho_giot:
        noi_dung = json.load(tep)
        if isinstance(noi_dung, list): du_lieu_tho_nho_giot.extend(noi_dung)
    
    danh_sach_stt = sorted(list(set(str(d.get('STT')) for d in du_lieu_tho_nho_giot if d.get('STT'))))
    khu_vuc_chon = st.sidebar.selectbox("🎯 Chọn khu vực (STT):", danh_sach_stt)

    # --- BƯỚC 1: XÁC ĐỊNH MÙA VỤ (DÙNG FILE NHỎ GIỌT) ---
    DINH_DANG_GIO = "%Y-%m-%d %H-%M-%S"
    thong_ke_ngay_tuoi = {}
    du_lieu_khu_vuc = sorted([d for d in du_lieu_tho_nho_giot if str(d.get('STT')) == khu_vuc_chon],
                            key=lambda x: datetime.strptime(x['Thời gian'], DINH_DANG_GIO))

    for i in range(len(du_lieu_khu_vuc) - 1):
        hien_tai, tiep_theo = du_lieu_khu_vuc[i], du_lieu_khu_vuc[i+1]
        if hien_tai.get('Trạng thái') == "Bật" and tiep_theo.get('Trạng thái') == "Tắt":
            try:
                t1 = datetime.strptime(hien_tai['Thời gian'], DINH_DANG_GIO)
                t2 = datetime.strptime(tiep_theo['Thời gian'], DINH_DANG_GIO)
                thoi_gian_tuoi = (t2 - t1).total_seconds()
                if GIAY_TUOI_TOI_THIEU <= thoi_gian_tuoi <= GIAY_TUOI_TOI_DA:
                    ngay_str = t1.strftime("%Y-%m-%d")
                    if ngay_str not in thong_ke_ngay_tuoi: thong_ke_ngay_tuoi[ngay_str] = {'so_lan_tuoi': 0}
                    thong_ke_ngay_tuoi[ngay_str]['so_lan_tuoi'] += 1
            except: continue

    ngay_hop_le_vu = sorted([datetime.strptime(n, "%Y-%m-%d").date() 
                            for n, c in thong_ke_ngay_tuoi.items() if c['so_lan_tuoi'] >= LAN_TUOI_TOI_THIEU_NGAY])
    
    if ngay_hop_le_vu:
        danh_sach_mua_vu = []
        ngay_bat_dau_vu = ngay_hop_le_vu[0]
        for i in range(1, len(ngay_hop_le_vu)):
            if (ngay_hop_le_vu[i] - ngay_hop_le_vu[i-1]).days > KHOANG_CACH_NGAY_NGAT_VU:
                if (ngay_hop_le_vu[i-1] - ngay_bat_dau_vu).days + 1 >= SO_NGAY_TOI_THIEU_VU:
                    danh_sach_mua_vu.append({'bat_dau': ngay_bat_dau_vu, 'ket_thuc': ngay_hop_le_vu[i-1]})
                ngay_bat_dau_vu = ngay_hop_le_vu[i]
        danh_sach_mua_vu.append({'bat_dau': ngay_bat_dau_vu, 'ket_thuc': ngay_hop_le_vu[-1]})

        nhan_chon_vu = st.selectbox("📅 Chọn mùa vụ:", [f"Vụ {i+1}: {v['bat_dau']} -> {v['ket_thuc']}" for i, v in enumerate(danh_sach_mua_vu)])
        mua_vu_hien_tai = danh_sach_mua_vu[int(nhan_chon_vu.split(':')[0].split()[1]) - 1]

        # --- BƯỚC 2: CHỌN CÁCH CHIA (GIAO DIỆN TÍCH CHỌN) ---
        st.markdown("### 🛠 Phương thức phân chia giai đoạn")
        cot1, cot2, cot3 = st.columns(3)
        chon_cach_1 = cot1.checkbox("Cách 1: Theo Lần tưới", value=True)
        chon_cach_2 = cot2.checkbox("Cách 3: Theo TBEC")
        chon_cach_3 = cot3.checkbox("Cách 4: Theo EC Yêu cầu")

        # --- BƯỚC 3: XỬ LÝ VÀ HIỂN THỊ ---

        if chon_cach_1:
            st.divider()
            st.subheader("💧 Cách 1: Phân chia theo Tần suất tưới")
            ngay_trong_vu = sorted([d for d in thong_ke_ngay_tuoi 
                                   if mua_vu_hien_tai['bat_dau'] <= datetime.strptime(d, "%Y-%m-%d").date() <= mua_vu_hien_tai['ket_thuc']])
            ds_giai_doan_c1 = chia_giai_doan_tu_dong(ngay_trong_vu, thong_ke_ngay_tuoi, 'so_lan_tuoi', NGUONG_NGAT_LAN_TUOI)
            
            thong_ke_thi_giac = {}
            for gd in ds_giai_doan_c1:
                trung_binh_lam_tron = round(sum(thong_ke_ngay_tuoi[d]['so_lan_tuoi'] for d in gd) / len(gd))
                for d in gd: 
                    thong_ke_thi_giac[d] = {'so_lan_tuoi': thong_ke_ngay_tuoi[d]['so_lan_tuoi'], 'gia_tri_ao': trung_binh_lam_tron}
            ve_bieu_do_da_sac(thong_ke_thi_giac, ds_giai_doan_c1, "Biểu đồ theo Lần tưới", 'so_lan_tuoi')

        if (chon_cach_2 or chon_cach_3):
            if not tep_cham_phan:
                st.warning("⚠️ Vui lòng tải file Châm phân để xem dữ liệu này.")
            else:
                du_lieu_tho_cham_phan = []
                for tep in tep_cham_phan:
                    noi_dung = json.load(tep)
                    if isinstance(noi_dung, list): du_lieu_tho_cham_phan.extend(noi_dung)
                
                thong_ke_ngay_phan = {}
                for item in du_lieu_tho_cham_phan:
                    if str(item.get('STT')) != khu_vuc_chon: continue
                    try:
                        thoi_gian_obj = datetime.strptime(item['Thời gian'], DINH_DANG_GIO)
                        if mua_vu_hien_tai['bat_dau'] <= thoi_gian_obj.date() <= mua_vu_hien_tai['ket_thuc']:
                            ngay_str = thoi_gian_obj.strftime("%Y-%m-%d")
                            val_tbec = chuyen_doi_so_thuc(item, ['TBEC', 'tbec'])
                            val_req = chuyen_doi_so_thuc(item, ['EC yêu cầu', 'ecreq'])
                            
                            if ngay_str not in thong_ke_ngay_phan: thong_ke_ngay_phan[ngay_str] = {'ds_tbec': [], 'ds_req': []}
                            if val_tbec is not None: thong_ke_ngay_phan[ngay_str]['ds_tbec'].append(val_tbec)
                            if val_req is not None: thong_ke_ngay_phan[ngay_str]['ds_req'].append(val_req)
                    except: continue
                
                du_lieu_ngay_chot = {d: {
                    'tbec': np.mean(v['ds_tbec']) if v['ds_tbec'] else 0.0,
                    'ecreq': np.mean(v['ds_req']) if v['ds_req'] else 0.0
                } for d, v in thong_ke_ngay_phan.items()}
                
                ngay_phan_sap_xep = sorted(du_lieu_ngay_chot.keys())

                if chon_cach_2 and ngay_phan_sap_xep:
                    st.divider()
                    st.subheader("🧪 Cách 3: Phân chia theo chỉ số TBEC")
                    ds_giai_doan_c2 = chia_giai_doan_tu_dong(ngay_phan_sap_xep, du_lieu_ngay_chot, 'tbec', NGUONG_NGAT_TBEC)
                    ve_bieu_do_da_sac(du_lieu_ngay_chot, ds_giai_doan_c2, "Biểu đồ theo TBEC", 'tbec')

                if chon_cach_3 and ngay_phan_sap_xep:
                    st.divider()
                    st.subheader("📋 Cách 4: Phân chia theo EC Yêu cầu")
                    ds_giai_doan_c3 = chia_giai_doan_tu_dong(ngay_phan_sap_xep, du_lieu_ngay_chot, 'ecreq', NGUONG_NGAT_EC_YEU_CAU)
                    ve_bieu_do_da_sac(du_lieu_ngay_chot, ds_giai_doan_c3, "Biểu đồ theo EC Yêu cầu", 'ecreq')
    else:
        st.error("Không tìm thấy mùa vụ hợp lệ.")
else:
    st.info("👋 Hãy tải file Nhỏ giọt ở thanh bên để bắt đầu phân tích.")
