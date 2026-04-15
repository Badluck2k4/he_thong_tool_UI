import streamlit as st
import numpy as np
import json
from datetime import datetime
import matplotlib.pyplot as plt

# =====================================================================
# PHẦN 1: CẤU HÌNH CÁC QUY TẮC CHUNG
# =====================================================================
CAU_HINH_QUY_TAC = {
    "GIAY_TUOI_TOI_THIEU": 20,     # Lọc nhiễu bật bơm dưới 20s
    "GIAY_TUOI_TOI_DA": 3600,      # Lọc lỗi quên tắt bơm trên 1 tiếng
    "SO_NGAY_NGHI_TOI_DA": 2,      # Rớt dữ liệu quá 2 ngày coi như kết thúc vụ
    "SO_NGAY_TOI_THIEU_MOT_VU": 7  # Một vụ mùa phải dài ít nhất 7 ngày
}

# =====================================================================
# PHẦN 2: CÁC HÀM XỬ LÝ DỮ LIỆU
# =====================================================================

def lay_gia_tri_so_thuc_tu_chuoi(dong_du_lieu, danh_sach_tu_khoa):
    for tu_khoa in danh_sach_tu_khoa:
        gia_tri_tim_thay = dong_du_lieu.get(tu_khoa)
        if gia_tri_tim_thay is not None:
            try:
                chuoi_gia_tri = str(gia_tri_tim_thay).replace(',', '.')
                # CHUẨN HÓA EC: Chia 100 tại đây
                return float(chuoi_gia_tri) / 100.0 
            except (ValueError, TypeError):
                continue
    return None

def ham_lay_thoi_gian_de_sap_xep(dong_du_lieu):
    return dong_du_lieu['Thời gian']

def tao_so_cai_du_lieu_tong_hop(danh_sach_tep_tin_nho_giot, danh_sach_tep_tin_cham_phan, khu_vuc_duoc_chon):
    du_lieu_tam_thoi_theo_ngay = {}

    # --- ĐỌC DỮ LIỆU NHỎ GIỌT ---
    if danh_sach_tep_tin_nho_giot:
        toan_bo_du_lieu_nho_giot = []
        for tep_tin in danh_sach_tep_tin_nho_giot:
            tep_tin.seek(0)
            du_lieu_trong_tep = json.load(tep_tin)
            for dong in du_lieu_trong_tep: toan_bo_du_lieu_nho_giot.append(dong)
        
        du_lieu_nho_giot_da_loc = [d for d in toan_bo_du_lieu_nho_giot if str(d.get('STT')) == khu_vuc_duoc_chon]
        du_lieu_nho_giot_da_loc.sort(key=ham_lay_thoi_gian_de_sap_xep)

        for dong_du_lieu in du_lieu_nho_giot_da_loc:
            try:
                thoi_diem = datetime.strptime(dong_du_lieu['Thời gian'], "%Y-%m-%d %H-%M-%S")
                ngay_str = thoi_diem.strftime("%Y-%m-%d")
            except: continue 
                
            if ngay_str not in du_lieu_tam_thoi_theo_ngay: 
                du_lieu_tam_thoi_theo_ngay[ngay_str] = {'so_lan_tuoi': 0, 'tong_so_giay_tuoi': 0, 'danh_sach_tbec': [], 'danh_sach_ec_yeu_cau': []}
                
            gia_tri_tbec = lay_gia_tri_so_thuc_tu_chuoi(dong_du_lieu, ['TBEC', 'tbec'])
            if gia_tri_tbec is not None: du_lieu_tam_thoi_theo_ngay[ngay_str]['danh_sach_tbec'].append(gia_tri_tbec)

        for vi_tri in range(len(du_lieu_nho_giot_da_loc) - 1):
            d1, d2 = du_lieu_nho_giot_da_loc[vi_tri], du_lieu_nho_giot_da_loc[vi_tri + 1]
            if d1.get('Trạng thái') == "Bật" and d2.get('Trạng thái') == "Tắt":
                t1, t2 = datetime.strptime(d1['Thời gian'], "%Y-%m-%d %H-%M-%S"), datetime.strptime(d2['Thời gian'], "%Y-%m-%d %H-%M-%S")
                so_giay = (t2 - t1).total_seconds()
                if CAU_HINH_QUY_TAC["GIAY_TUOI_TOI_THIEU"] <= so_giay <= CAU_HINH_QUY_TAC["GIAY_TUOI_TOI_DA"]:
                    ngay_s = t1.strftime("%Y-%m-%d")
                    if ngay_s in du_lieu_tam_thoi_theo_ngay:
                        du_lieu_tam_thoi_theo_ngay[ngay_s]['so_lan_tuoi'] += 1
                        du_lieu_tam_thoi_theo_ngay[ngay_s]['tong_so_giay_tuoi'] += so_giay

    # --- ĐỌC DỮ LIỆU CHÂM PHÂN ---
    if danh_sach_tep_tin_cham_phan:
        for tep_tin in danh_sach_tep_tin_cham_phan:
            tep_tin.seek(0)
            du_lieu_trong_tep = json.load(tep_tin)
            for dong_du_lieu in du_lieu_trong_tep:
                if str(dong_du_lieu.get('STT')) != khu_vuc_duoc_chon: continue 
                try: ngay_str = datetime.strptime(dong_du_lieu['Thời gian'], "%Y-%m-%d %H-%M-%S").strftime("%Y-%m-%d")
                except: continue
                if ngay_str not in du_lieu_tam_thoi_theo_ngay: 
                    du_lieu_tam_thoi_theo_ngay[ngay_str] = {'so_lan_tuoi': 0, 'tong_so_giay_tuoi': 0, 'danh_sach_tbec': [], 'danh_sach_ec_yeu_cau': []}
                gia_tri_ec_yc = lay_gia_tri_so_thuc_tu_chuoi(dong_du_lieu, ['EC yêu cầu', 'ecreq'])
                if gia_tri_ec_yc is not None: du_lieu_tam_thoi_theo_ngay[ngay_str]['danh_sach_ec_yeu_cau'].append(gia_tri_ec_yc)

    # --- TỔNG HỢP SỔ CÁI ---
    so_cai = {}
    for ngay, d in du_lieu_tam_thoi_theo_ngay.items():
        so_cai[ngay] = {
            'so_lan_tuoi': d['so_lan_tuoi'],
            'thoi_gian_tuoi_phut': int(round(d['tong_so_giay_tuoi'] / 60)),
            'tbec': float(f"{np.mean(d['danh_sach_tbec']):.2f}") if d['danh_sach_tbec'] else 0.0,
            'ec_yeu_cau': float(f"{np.mean(d['danh_sach_ec_yeu_cau']):.2f}") if d['danh_sach_ec_yeu_cau'] else 0.0
        }
    return so_cai

def tim_kiem_cac_mua_vu(so_cai_du_lieu, ten_chi_so_lam_goc, nguong_gia_tri_bat_dau):
    danh_sach_ngay = sorted([datetime.strptime(ngay, "%Y-%m-%d").date() for ngay, d in so_cai_du_lieu.items() if d[ten_chi_so_lam_goc] >= nguong_gia_tri_bat_dau])
    danh_sach_cac_mua_vu = []
    if not danh_sach_ngay: return []
    
    ngay_bat_dau_vu = danh_sach_ngay[0]
    for i in range(1, len(danh_sach_ngay)):
        if (danh_sach_ngay[i] - danh_sach_ngay[i-1]).days > CAU_HINH_QUY_TAC["SO_NGAY_NGHI_TOI_DA"]:
            if (danh_sach_ngay[i-1] - ngay_bat_dau_vu).days + 1 >= CAU_HINH_QUY_TAC["SO_NGAY_TOI_THIEU_MOT_VU"]:
                danh_sach_cac_mua_vu.append((ngay_bat_dau_vu, danh_sach_ngay[i-1]))
            ngay_bat_dau_vu = danh_sach_ngay[i]
    if (danh_sach_ngay[-1] - ngay_bat_dau_vu).days + 1 >= CAU_HINH_QUY_TAC["SO_NGAY_TOI_THIEU_MOT_VU"]:
        danh_sach_cac_mua_vu.append((ngay_bat_dau_vu, danh_sach_ngay[-1]))
    return danh_sach_cac_mua_vu

def chia_nho_mua_vu_thanh_cac_giai_doan(danh_sach_ngay_trong_vu, so_cai_du_lieu, ten_chi_so_lam_goc, sai_so_cho_phep):
    if not danh_sach_ngay_trong_vu: return []
    danh_sach_cac_giai_doan = []
    giai_doan_hien_tai = [danh_sach_ngay_trong_vu[0]]
    ngay_nghi_ngo = None 

    for i in range(1, len(danh_sach_ngay_trong_vu)):
        ngay_xet = danh_sach_ngay_trong_vu[i]
        val_xet = so_cai_du_lieu[ngay_xet][ten_chi_so_lam_goc]
        val_moc = so_cai_du_lieu[giai_doan_hien_tai[0]][ten_chi_so_lam_goc]
        
        if abs(val_xet - val_moc) >= sai_so_cho_phep:
            if ngay_nghi_ngo is None:
                ngay_nghi_ngo = ngay_xet
                giai_doan_hien_tai.append(ngay_xet)
            else: # XÁC NHẬN KÉP 2 NGÀY LIÊN TIẾP
                giai_doan_hien_tai.pop() 
                danh_sach_cac_giai_doan.append(giai_doan_hien_tai)
                giai_doan_hien_tai = [ngay_nghi_ngo, ngay_xet]
                ngay_nghi_ngo = None
        else:
            ngay_nghi_ngo = None
            giai_doan_hien_tai.append(ngay_xet)
            
    danh_sach_cac_giai_doan.append(giai_doan_hien_tai)
    return danh_sach_cac_giai_doan

# =====================================================================
# PHẦN 3: HÀM VẼ BIỂU ĐỒ (MÀU RIÊNG TỪNG GIAI ĐOẠN)
# =====================================================================

def ve_bieu_do_chi_so_duoc_chon(du_lieu_tong_hop, danh_sach_cac_giai_doan, ten_chi_so_hien_thi, ten_bien_trong_so_cai):
    khung_tranh = plt.figure(figsize=(16, 6))
    truc_toa_do = plt.gca()
    bang_mau = ['#66b3ff', '#99ff99', '#ff9999', '#ffcc99', '#c2c2f0', '#ffb3e6', '#c4e17f', '#ffdf80']
    
    danh_sach_ngay_ve = []
    truc_x_hien_tai = 0
    
    for i, gd in enumerate(danh_sach_cac_giai_doan):
        mau = bang_mau[i % len(bang_mau)]
        du_lieu_y = []
        for n in gd:
            danh_sach_ngay_ve.append(n)
            du_lieu_y.append(du_lieu_tong_hop[n][ten_bien_trong_so_cai])
            
        x_gd = np.arange(truc_x_hien_tai, truc_x_hien_tai + len(gd))
        truc_toa_do.bar(x_gd, du_lieu_y, color=mau, edgecolor='black', label=f'GĐ {i+1}')
        truc_x_hien_tai += len(gd)
        
    truc_toa_do.set_ylabel(ten_chi_so_hien_thi)
    truc_toa_do.grid(axis='y', linestyle='--', alpha=0.5)
    truc_toa_do.legend(title="Giai đoạn", loc='upper left', bbox_to_anchor=(1, 1))
    
    buoc = max(1, len(danh_sach_ngay_ve) // 25)
    plt.xticks(np.arange(len(danh_sach_ngay_ve))[::buoc], [n[-5:] for n in danh_sach_ngay_ve[::buoc]], rotation=45)
    plt.title(f"Phân tích theo: {ten_chi_so_hien_thi}")
    plt.tight_layout()
    return khung_tranh

# =====================================================================
# PHẦN 4: GIAO DIỆN STREAMLIT
# =====================================================================

def main():
    st.set_page_config(page_title="Phân Tích Nông Nghiệp", layout="wide")
    st.title("📊 Phân Tích Dữ Liệu Logic Mùa Vụ")
    
    with st.sidebar:
        st.header("📂 Cấu hình dữ liệu")
        tep_nho_giot = st.file_uploader("Tệp Nhỏ giọt (JSON)", accept_multiple_files=True)
        tep_cham_phan = st.file_uploader("Tệp Châm phân (JSON)", accept_multiple_files=True)
        khu_vuc = st.selectbox("Khu vực", ["1", "2", "3", "4"])
        
        st.markdown("---")
        st.header("⚙️ Cài đặt thuật toán")
        tu_dien = {"Lần tưới": "so_lan_tuoi", "TBEC": "tbec", "EC Yêu cầu": "ec_yeu_cau"}
        ten_hien_thi = st.selectbox("🎯 Chỉ số làm mốc", list(tu_dien.keys()))
        bien_goc = tu_dien[ten_hien_thi]
        
        # Thiết lập mặc định
        def_n, def_s = (6, 3.0) if bien_goc == "so_lan_tuoi" else (0.40, 0.15) if bien_goc == "tbec" else (0.90, 0.2)
        nguong = st.number_input(f"📈 Ngưỡng bắt đầu", value=def_n)
        sai_so = st.number_input(f"✂️ Sai số cắt GĐ", value=def_s)

    if tep_nho_giot and tep_cham_phan:
        so_cai = tao_so_cai_du_lieu_tong_hop(tep_nho_giot, tep_cham_phan, khu_vuc)
        if not so_cai: st.error("Không có dữ liệu!"); return
            
        mua_vu = tim_kiem_cac_mua_vu(so_cai, bien_goc, nguong)
        if not mua_vu: st.warning("Không tìm thấy vụ mùa nào thỏa mãn ngưỡng!"); return
            
        ten_vu = [f"Vụ {i+1}: {v[0].strftime('%d/%m')} - {v[1].strftime('%d/%m')}" for i, v in enumerate(mua_vu)]
        vi_tri_vu = st.selectbox("🌾 Chọn Mùa Vụ", range(len(mua_vu)), format_func=lambda x: ten_vu[x])
        
        vu_chot = mua_vu[vi_tri_vu]
        cac_ngay_vu = sorted([n for n in so_cai.keys() if vu_chot[0] <= datetime.strptime(n, "%Y-%m-%d").date() <= vu_chot[1]])
        
        gd_list = chia_nho_mua_vu_thanh_cac_giai_doan(cac_ngay_vu, so_cai, bien_goc, sai_so)
        st.success(f"✅ Đã phân tích được {len(gd_list)} giai đoạn.")

        st.pyplot(ve_bieu_do_chi_so_duoc_chon(so_cai, gd_list, ten_hien_thi, bien_goc))
        
        bang_data = []
        for i, gd in enumerate(gd_list):
            for n in gd:
                row = {"Giai đoạn": f"GĐ {i+1}", "Ngày": n}
                row.update({k.upper(): v for k, v in so_cai[n].items()})
                bang_data.append(row)
        st.dataframe(bang_data, use_container_width=True)
    else:
        st.info("👈 Vui lòng tải lên tệp JSON để bắt đầu.")

    # --- CHỮ KÝ FOOTER ---
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #888888; padding: 20px; font-weight: bold; font-style: italic;'>"
        \n"CODED BY QUANG SKIBIDI DOPYEYE-GEMINI 👽, PLS DONATED ME"
        "YOU CAN DONATE TO XXXXXXXXXXX"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
