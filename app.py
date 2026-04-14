# =====================================================================
# PHẦN 1: CẤU HÌNH & KHỞI TẠO (PHÒNG QUẢN LÝ)
# =====================================================================
import streamlit as st
import numpy as np
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Hằng số luật chơi chung
CAU_HINH_GOC = {
    "GIAY_TUOI_TOI_THIEU": 20,
    "GIAY_TUOI_TOI_DA": 3600,
    "SO_NGAY_NGHI_TOI_DA": 2,      # Rớt ngưỡng bao nhiêu ngày thì đóng nắp vụ mùa
    "SO_NGAY_TOI_THIEU_MOT_VU": 7  # Chống nhiễu vụ mùa quá ngắn
}

# =====================================================================
# PHẦN 2: LÕI XỬ LÝ DỮ LIỆU (NHÀ BẾP - LÕI THUẬT TOÁN)
# =====================================================================

def lay_gia_tri_so_thuc(dong_du_lieu, danh_sach_tu_khoa):
    for tu_khoa in danh_sach_tu_khoa:
        gia_tri = dong_du_lieu.get(tu_khoa)
        if gia_tri is not None:
            try:
                chuoi_gia_tri = str(gia_tri).replace(',', '.')
                return float(chuoi_gia_tri)
            except (ValueError, TypeError):
                continue
    return None

def tong_hop_SBC_toan_dien(danh_sach_file_nho_giot, danh_sach_file_cham_phan, khu_vuc_duoc_chon):
    """BƯỚC 1: Đọc cả 2 file và gộp chung thành một Sổ Cái duy nhất từ đầu đến cuối"""
    du_lieu_ngay = {}

    # --- ĐỌC FILE NHỎ GIỌT ---
    if danh_sach_file_nho_giot:
        dl_nho_giot = []
        for file in danh_sach_file_nho_giot:
            file.seek(0)
            dl_nho_giot.extend(json.load(file))
        
        dl_nho_giot = [d for d in dl_nho_giot if str(d.get('STT')) == khu_vuc_duoc_chon]
        dl_nho_giot.sort(key=lambda x: x['Thời gian'])

        for i in range(len(dl_nho_giot) - 1):
            if dl_nho_giot[i].get('Trạng thái') == "Bật" and dl_nho_giot[i+1].get('Trạng thái') == "Tắt":
                thoi_diem_bat_dau = datetime.strptime(dl_nho_giot[i]['Thời gian'], "%Y-%m-%d %H-%M-%S")
                thoi_diem_ket_thuc = datetime.strptime(dl_nho_giot[i+1]['Thời gian'], "%Y-%m-%d %H-%M-%S")
                giay_tuoi = (thoi_diem_ket_thuc - thoi_diem_bat_dau).total_seconds()
                
                if CAU_HINH_GOC["GIAY_TUOI_TOI_THIEU"] <= giay_tuoi <= CAU_HINH_GOC["GIAY_TUOI_TOI_DA"]:
                    ngay_chuoi = thoi_diem_bat_dau.strftime("%Y-%m-%d")
                    if ngay_chuoi not in du_lieu_ngay: du_lieu_ngay[ngay_chuoi] = {'so_lan_tuoi': 0, 'tong_giay': 0, 'ds_tbec': [], 'ds_ec_req': []}
                    du_lieu_ngay[ngay_chuoi]['so_lan_tuoi'] += 1
                    du_lieu_ngay[ngay_chuoi]['tong_giay'] += giay_tuoi

    # --- ĐỌC FILE CHÂM PHÂN ---
    if danh_sach_file_cham_phan:
        for file in danh_sach_file_cham_phan:
            file.seek(0)
            for dong in json.load(file):
                if str(dong.get('STT')) != khu_vuc_duoc_chon: continue
                thoi_diem = datetime.strptime(dong['Thời gian'], "%Y-%m-%d %H-%M-%S")
                ngay_chuoi = thoi_diem.strftime("%Y-%m-%d")
                
                if ngay_chuoi not in du_lieu_ngay: du_lieu_ngay[ngay_chuoi] = {'so_lan_tuoi': 0, 'tong_giay': 0, 'ds_tbec': [], 'ds_ec_req': []}
                
                tbec = lay_gia_tri_so_thuc(dong, ['TBEC', 'tbec'])
                ec_req = lay_gia_tri_so_thuc(dong, ['EC yêu cầu', 'ecreq'])
                if tbec is not None: du_lieu_ngay[ngay_chuoi]['ds_tbec'].append(tbec)
                if ec_req is not None: du_lieu_ngay[ngay_chuoi]['ds_ec_req'].append(ec_req)

    # --- TÍNH TRUNG BÌNH & HOÀN THIỆN SỔ CÁI ---
    so_cai_chinh_thuc = {}
    for ngay, dl in du_lieu_ngay.items():
        so_cai_chinh_thuc[ngay] = {
            'so_lan_tuoi': dl['so_lan_tuoi'],
            'thoi_gian_tuoi_phut': int(round(dl['tong_giay'] / 60)),
            'tbec': float(f"{np.mean(dl['ds_tbec']):.2f}") if dl['ds_tbec'] else 0.0,
            'ec_yeu_cau': float(f"{np.mean(dl['ds_ec_req']):.2f}") if dl['ds_ec_req'] else 0.0
        }
    return so_cai_chinh_thuc

def tim_kiem_cac_mua_vu(so_cai, chi_so_goc, nguong_bat_dau):
    """BƯỚC 2: Cỗ Máy Master - Cắt Vụ Mùa (Logic Vượt Ngưỡng)"""
    danh_sach_ngay_hop_le = []
    
    # Lọc những ngày thỏa mãn điều kiện Vượt Ngưỡng
    for chuoi_ngay, du_lieu in so_cai.items():
        if du_lieu[chi_so_goc] >= nguong_bat_dau:
            ngay_dinh_dang = datetime.strptime(chuoi_ngay, "%Y-%m-%d").date()
            danh_sach_ngay_hop_le.append(ngay_dinh_dang)
            
    danh_sach_ngay_hop_le.sort()
    danh_sach_mua_vu = []
    
    # Chặt vụ nếu rớt ngưỡng quá số ngày cho phép
    if danh_sach_ngay_hop_le:
        ngay_bat_dau_vu = danh_sach_ngay_hop_le[0]
        for i in range(1, len(danh_sach_ngay_hop_le)):
            ngay_dang_xet = danh_sach_ngay_hop_le[i]
            ngay_lien_truoc = danh_sach_ngay_hop_le[i-1]
            khoang_cach_ngay = (ngay_dang_xet - ngay_lien_truoc).days
            
            if khoang_cach_ngay > CAU_HINH_GOC["SO_NGAY_NGHI_TOI_DA"]: 
                do_dai_vu_cu = (ngay_lien_truoc - ngay_bat_dau_vu).days + 1
                if do_dai_vu_cu >= CAU_HINH_GOC["SO_NGAY_TOI_THIEU_MOT_VU"]:
                    danh_sach_mua_vu.append((ngay_bat_dau_vu, ngay_lien_truoc))
                ngay_bat_dau_vu = ngay_dang_xet 
                
        # Vét nốt vụ cuối
        ngay_cuoi_cung = danh_sach_ngay_hop_le[-1]
        if (ngay_cuoi_cung - ngay_bat_dau_vu).days + 1 >= CAU_HINH_GOC["SO_NGAY_TOI_THIEU_MOT_VU"]:
            danh_sach_mua_vu.append((ngay_bat_dau_vu, ngay_cuoi_cung))
            
    return danh_sach_mua_vu

def chia_nho_thanh_cac_giai_doan(danh_sach_ngay_trong_vu, so_cai, chi_so_goc, sai_so_giai_doan):
    """BƯỚC 3: Cỗ Máy Master - Cắt Giai Đoạn (Logic Bước Nhảy Delta)"""
    if not danh_sach_ngay_trong_vu: return []
    
    tat_ca_giai_doan = []
    giai_doan_hien_tai = [danh_sach_ngay_trong_vu[0]]
    
    for i in range(1, len(danh_sach_ngay_trong_vu)):
        ngay_dang_xet = danh_sach_ngay_trong_vu[i]
        ngay_moc = giai_doan_hien_tai[0] # Lấy ngày mở đầu giai đoạn làm mốc nền
        
        gia_tri_hom_nay = so_cai[ngay_dang_xet].get(chi_so_goc, 0)
        gia_tri_moc = so_cai[ngay_moc].get(chi_so_goc, 0)
        
        # Logic Nhảy Bậc Thang
        if abs(gia_tri_hom_nay - gia_tri_moc) >= sai_so_giai_doan:
            tat_ca_giai_doan.append(giai_doan_hien_tai)
            giai_doan_hien_tai = [ngay_dang_xet] # Chém nhát cắt, mở giai đoạn mới
        else:
            giai_doan_hien_tai.append(ngay_dang_xet)
            
    tat_ca_giai_doan.append(giai_doan_hien_tai)
    return tat_ca_giai_doan

# =====================================================================
# PHẦN 3: LÕI VẼ BIỂU ĐỒ (Giữ nguyên logic vẽ, chỉ làm đẹp trục)
# =====================================================================

def ve_bieu_do_dong_thoi(du_lieu_tong_hop, tat_ca_giai_doan):
    danh_sach_chi_so_can_ve = [("Lần tưới", "so_lan_tuoi"), ("TBEC", "tbec"), ("EC Yêu cầu", "ec_yeu_cau")]
    khung_tranh, danh_sach_truc = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
    
    danh_sach_ngay_thuc_te = []
    for gd in tat_ca_giai_doan: danh_sach_ngay_thuc_te.extend(gd)
    truc_x_so_dem = np.arange(len(danh_sach_ngay_thuc_te))
    
    for vi_tri, (ten_hien_thi, ten_bien) in enumerate(danh_sach_chi_so_can_ve):
        truc = danh_sach_truc[vi_tri]
        du_lieu_y = [du_lieu_tong_hop[ngay][ten_bien] for ngay in danh_sach_ngay_thuc_te]
        
        truc.bar(truc_x_so_dem, du_lieu_y, color='skyblue' if vi_tri==0 else ('lightgreen' if vi_tri==1 else 'salmon'), edgecolor='black')
        truc.set_ylabel(ten_hien_thi, fontsize=12)
        truc.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Vẽ vạch đỏ cắt giai đoạn
        if len(tat_ca_giai_doan) > 1:
            for gd in tat_ca_giai_doan[:-1]:
                vi_tri_cat = danh_sach_ngay_thuc_te.index(gd[-1]) 
                truc.axvline(x=vi_tri_cat + 0.5, color='red', linestyle='-', linewidth=2.5)

    buoc_nhay_nhan = max(1, len(danh_sach_ngay_thuc_te) // 30) 
    ds_vitri_nhan = truc_x_so_dem[::buoc_nhay_nhan]
    ds_nhan_ngay = [danh_sach_ngay_thuc_te[i][-5:] for i in ds_vitri_nhan] # Chỉ hiện MM-DD cho gọn
    
    plt.xticks(ds_vitri_nhan, ds_nhan_ngay, rotation=45, ha='right', fontsize=10)
    khung_tranh.subplots_adjust(hspace=0.3) 
    return khung_tranh

# =====================================================================
# PHẦN 4: GIAO DIỆN NGƯỜI DÙNG (SÂN KHẤU VÀ BỒI BÀN)
# =====================================================================

def main():
    st.set_page_config(page_title="Phân Tích Dữ Liệu", layout="wide")
    st.title("📊 Thuật Toán Logic Hợp Nhất (Master Algorithm)")
    
    with st.sidebar:
        st.header("📂 1. Tải Dữ Liệu")
        file_ng = st.file_uploader("Upload Nhỏ giọt (JSON)", accept_multiple_files=True, type=['json'])
        file_cp = st.file_uploader("Upload Châm phân (JSON)", accept_multiple_files=True, type=['json'])
        khu_vuc = st.selectbox("Chọn khu vực", ["1", "2", "3", "4"])
        
        st.markdown("---")
        st.header("⚙️ 2. Cỗ Máy Thuật Toán Gốc")
        st.caption("Chỉ dùng 1 chỉ số duy nhất để cắt vụ & cắt giai đoạn")
        
        tu_dien_chi_so = {"Lần tưới": "so_lan_tuoi", "TBEC": "tbec", "EC Yêu cầu": "ec_yeu_cau"}
        chi_so_hien_thi = st.selectbox("🎯 Chọn Chỉ số Master", list(tu_dien_chi_so.keys()))
        chi_so_goc = tu_dien_chi_so[chi_so_hien_thi]
        
        # Mặc định gợi ý số liệu hợp lý dựa trên chỉ số
        if chi_so_goc == "so_lan_tuoi":
            gia_tri_nguong_md, gia_tri_sai_so_md = 5.0, 2.0
        else:
            gia_tri_nguong_md, gia_tri_sai_so_md = 0.5, 0.3
            
        nguong_bat_dau = st.number_input(f"📈 Ngưỡng Bắt Đầu Vụ ({chi_so_hien_thi})", value=gia_tri_nguong_md, step=0.1)
        sai_so_giai_doan = st.number_input(f"✂️ Sai Số Cắt GĐ ({chi_so_hien_thi})", value=gia_tri_sai_so_md, step=0.1)

    # ---------------------------------------------------------
    # LUỒNG THỰC THI CHÍNH
    # ---------------------------------------------------------
    if file_ng and file_cp:
        # BƯỚC 1: Lập Sổ Cái
        so_cai = tong_hop_SBC_toan_dien(file_ng, file_cp, khu_vuc)
        if not so_cai:
            st.error("Không tìm thấy dữ liệu cho khu vực này.")
            return
            
        # BƯỚC 2: Tìm Mùa Vụ dựa trên Master Metric
        ds_mua_vu = tim_kiem_cac_mua_vu(so_cai, chi_so_goc, nguong_bat_dau)
        
        if not ds_mua_vu:
            st.warning(f"Không tìm thấy vụ nào có {chi_so_hien_thi} vượt ngưỡng {nguong_bat_dau} liên tục trên 7 ngày.")
            return
            
        ds_ten_vu = [f"Vụ {i+1}: {vu[0].strftime('%d/%m/%Y')} - {vu[1].strftime('%d/%m/%Y')}" for i, vu in enumerate(ds_mua_vu)]
        vi_tri_vu = st.selectbox("🌾 3. Chọn Mùa Vụ Để Phân Tích", range(len(ds_mua_vu)), format_func=lambda x: ds_ten_vu[x])
        vu_chon = ds_mua_vu[vi_tri_vu]
        
        # Lọc Sổ Cái theo ngày thuộc vụ
        ngay_trong_vu = sorted([ngay for ngay in so_cai.keys() if vu_chon[0] <= datetime.strptime(ngay, "%Y-%m-%d").date() <= vu_chon[1]])
        
        # BƯỚC 3: Cắt Giai Đoạn
        tat_ca_giai_doan = chia_nho_thanh_cac_giai_doan(ngay_trong_vu, so_cai, chi_so_goc, sai_so_giai_doan)
        st.success(f"✅ Đang phân tích theo **{chi_so_hien_thi}**. Hệ thống cắt được **{len(tat_ca_giai_doan)} giai đoạn**.")

        # BƯỚC 4: Hiển thị 
        st.subheader("📈 Biểu Đồ Trực Quan (Đường cắt đỏ dựa trên Master Metric)")
        st.pyplot(ve_bieu_do_dong_thoi(so_cai, tat_ca_giai_doan))
        
        st.subheader("📋 Bảng Dữ Liệu Chi Tiết")
        bang_hien_thi = []
        for index_gd, gd in enumerate(tat_ca_giai_doan):
            for ngay in gd:
                bang_hien_thi.append({
                    "Giai đoạn": f"GĐ {index_gd + 1}",
                    "Ngày": ngay,
                    "Lần tưới": so_cai[ngay]['so_lan_tuoi'],
                    "Phút tưới": so_cai[ngay]['thoi_gian_tuoi_phut'],
                    "TBEC": so_cai[ngay]['tbec'],
                    "EC Req": so_cai[ngay]['ec_yeu_cau']
                })
        st.dataframe(bang_hien_thi, use_container_width=True)
    else:
        st.info("👈 Vui lòng tải lên cả 2 file Nhỏ Giọt và Châm Phân ở thanh bên trái.")

if __name__ == "__main__":
    main()
