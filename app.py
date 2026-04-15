# =====================================================================
# PHẦN 1: CẤU HÌNH & KHỞI TẠO CÁC THÔNG SỐ CƠ BẢN
# =====================================================================
import streamlit as st
import numpy as np
import json
from datetime import datetime
import matplotlib.pyplot as plt

# Từ điển chứa các quy tắc chung cho toàn bộ hệ thống
CAU_HINH_QUY_TAC = {
    "GIAY_TUOI_TOI_THIEU": 20,     # Lọc bỏ các lần bật máy bơm bị nhiễu (dưới 20 giây)
    "GIAY_TUOI_TOI_DA": 3600,      # Lọc bỏ các lần quên tắt máy bơm (trên 1 tiếng)
    "SO_NGAY_NGHI_TOI_DA": 2,      # Nếu dữ liệu rớt dưới ngưỡng quá 2 ngày thì coi như kết thúc vụ mùa đó
    "SO_NGAY_TOI_THIEU_MOT_VU": 7  # Một vụ mùa phải kéo dài ít nhất 7 ngày mới được tính là hợp lệ
}

# =====================================================================
# PHẦN 2: CÁC HÀM XỬ LÝ DỮ LIỆU CỐT LÕI (KHÔNG VIẾT TẮT)
# =====================================================================

def lay_gia_tri_so_thuc_tu_chuoi(dong_du_lieu, danh_sach_tu_khoa):
    for tu_khoa in danh_sach_tu_khoa:
        gia_tri_tim_thay = dong_du_lieu.get(tu_khoa)
        if gia_tri_tim_thay is not None:
            try:
                chuoi_gia_tri = str(gia_tri_tim_thay).replace(',', '.')
                # Chia 100 tại đây để chuẩn hóa toàn bộ chỉ số EC
                return float(chuoi_gia_tri) / 100.0 
            except (ValueError, TypeError):
                continue
    return None

# Hàm phụ để giúp hệ thống biết cách sắp xếp thời gian (Thay thế cho lambda)
def ham_lay_thoi_gian_de_sap_xep(dong_du_lieu):
    return dong_du_lieu['Thời gian']

def tao_so_cai_du_lieu_tong_hop(danh_sach_tep_tin_nho_giot, danh_sach_tep_tin_cham_phan, khu_vuc_duoc_chon):
    du_lieu_tam_thoi_theo_ngay = {}

    # --- ĐỌC TỆP TIN NHỎ GIỌT ---
    if danh_sach_tep_tin_nho_giot:
        toan_bo_du_lieu_nho_giot = []
        for tep_tin in danh_sach_tep_tin_nho_giot:
            tep_tin.seek(0)
            du_lieu_trong_tep = json.load(tep_tin)
            # Dùng vòng lặp for truyền thống thay vì viết tắt (extend)
            for dong in du_lieu_trong_tep:
                toan_bo_du_lieu_nho_giot.append(dong)
        
        # Lọc dữ liệu theo khu vực bằng vòng lặp for cơ bản
        du_lieu_nho_giot_da_loc = []
        for dong in toan_bo_du_lieu_nho_giot:
            if str(dong.get('STT')) == khu_vuc_duoc_chon:
                du_lieu_nho_giot_da_loc.append(dong)
                
        # Sắp xếp thời gian (dùng hàm phụ thay vì lambda)
        du_lieu_nho_giot_da_loc.sort(key=ham_lay_thoi_gian_de_sap_xep)

        # Quét lần 1: Lấy TBEC
        for dong_du_lieu in du_lieu_nho_giot_da_loc:
            try:
                thoi_diem = datetime.strptime(dong_du_lieu['Thời gian'], "%Y-%m-%d %H-%M-%S")
                ngay_dinh_dang_chuoi = thoi_diem.strftime("%Y-%m-%d")
            except:
                continue 
                
            if ngay_dinh_dang_chuoi not in du_lieu_tam_thoi_theo_ngay: 
                du_lieu_tam_thoi_theo_ngay[ngay_dinh_dang_chuoi] = {
                    'so_lan_tuoi': 0, 'tong_so_giay_tuoi': 0, 'danh_sach_tbec': [], 'danh_sach_ec_yeu_cau': []
                }
                
            gia_tri_tbec = lay_gia_tri_so_thuc_tu_chuoi(dong_du_lieu, ['TBEC', 'tbec'])
            if gia_tri_tbec is not None: 
                du_lieu_tam_thoi_theo_ngay[ngay_dinh_dang_chuoi]['danh_sach_tbec'].append(gia_tri_tbec)

        # Quét lần 2: Đếm lần tưới
        so_luong_dong = len(du_lieu_nho_giot_da_loc)
        for vi_tri in range(so_luong_dong - 1):
            dong_hien_tai = du_lieu_nho_giot_da_loc[vi_tri]
            dong_tiep_theo = du_lieu_nho_giot_da_loc[vi_tri + 1]
            
            if dong_hien_tai.get('Trạng thái') == "Bật" and dong_tiep_theo.get('Trạng thái') == "Tắt":
                thoi_diem_bat_dau = datetime.strptime(dong_hien_tai['Thời gian'], "%Y-%m-%d %H-%M-%S")
                thoi_diem_ket_thuc = datetime.strptime(dong_tiep_theo['Thời gian'], "%Y-%m-%d %H-%M-%S")
                so_giay_tuoi_thuc_te = (thoi_diem_ket_thuc - thoi_diem_bat_dau).total_seconds()
                
                if CAU_HINH_QUY_TAC["GIAY_TUOI_TOI_THIEU"] <= so_giay_tuoi_thuc_te <= CAU_HINH_QUY_TAC["GIAY_TUOI_TOI_DA"]:
                    ngay_dinh_dang_chuoi = thoi_diem_bat_dau.strftime("%Y-%m-%d")
                    
                    if ngay_dinh_dang_chuoi not in du_lieu_tam_thoi_theo_ngay: 
                        du_lieu_tam_thoi_theo_ngay[ngay_dinh_dang_chuoi] = {'so_lan_tuoi': 0, 'tong_so_giay_tuoi': 0, 'danh_sach_tbec': [], 'danh_sach_ec_yeu_cau': []}
                    
                    du_lieu_tam_thoi_theo_ngay[ngay_dinh_dang_chuoi]['so_lan_tuoi'] += 1
                    du_lieu_tam_thoi_theo_ngay[ngay_dinh_dang_chuoi]['tong_so_giay_tuoi'] += so_giay_tuoi_thuc_te

    # --- ĐỌC TỆP TIN CHÂM PHÂN ---
    if danh_sach_tep_tin_cham_phan:
        for tep_tin in danh_sach_tep_tin_cham_phan:
            tep_tin.seek(0)
            du_lieu_trong_tep = json.load(tep_tin)
            
            for dong_du_lieu in du_lieu_trong_tep:
                if str(dong_du_lieu.get('STT')) != khu_vuc_duoc_chon: 
                    continue 
                
                try:
                    thoi_diem = datetime.strptime(dong_du_lieu['Thời gian'], "%Y-%m-%d %H-%M-%S")
                    ngay_dinh_dang_chuoi = thoi_diem.strftime("%Y-%m-%d")
                except:
                    continue
                
                if ngay_dinh_dang_chuoi not in du_lieu_tam_thoi_theo_ngay: 
                    du_lieu_tam_thoi_theo_ngay[ngay_dinh_dang_chuoi] = {'so_lan_tuoi': 0, 'tong_so_giay_tuoi': 0, 'danh_sach_tbec': [], 'danh_sach_ec_yeu_cau': []}
                
                gia_tri_ec_yeu_cau = lay_gia_tri_so_thuc_tu_chuoi(dong_du_lieu, ['EC yêu cầu', 'ecreq'])
                if gia_tri_ec_yeu_cau is not None: 
                    du_lieu_tam_thoi_theo_ngay[ngay_dinh_dang_chuoi]['danh_sach_ec_yeu_cau'].append(gia_tri_ec_yeu_cau)

    # --- CHỐT SỔ CÁI ---
    so_cai_chinh_thuc = {}
    for ngay_dang_xet, du_lieu_trong_ngay in du_lieu_tam_thoi_theo_ngay.items():
        # Kiểm tra danh sách có dữ liệu không trước khi tính trung bình (tránh lỗi chia cho 0)
        if len(du_lieu_trong_ngay['danh_sach_tbec']) > 0:
            trung_binh_tbec = float(f"{np.mean(du_lieu_trong_ngay['danh_sach_tbec']):.2f}")
        else:
            trung_binh_tbec = 0.0

        if len(du_lieu_trong_ngay['danh_sach_ec_yeu_cau']) > 0:
            trung_binh_ec = float(f"{np.mean(du_lieu_trong_ngay['danh_sach_ec_yeu_cau']):.2f}")
        else:
            trung_binh_ec = 0.0

        so_cai_chinh_thuc[ngay_dang_xet] = {
            'so_lan_tuoi': du_lieu_trong_ngay['so_lan_tuoi'],
            'thoi_gian_tuoi_phut': int(round(du_lieu_trong_ngay['tong_so_giay_tuoi'] / 60)),
            'tbec': trung_binh_tbec,
            'ec_yeu_cau': trung_binh_ec
        }
    return so_cai_chinh_thuc

def tim_kiem_cac_mua_vu(so_cai_du_lieu, ten_chi_so_lam_goc, nguong_gia_tri_bat_dau):
    danh_sach_ngay_vuot_nguong = []
    for chuoi_ngay, du_lieu in so_cai_du_lieu.items():
        if du_lieu[ten_chi_so_lam_goc] >= nguong_gia_tri_bat_dau:
            ngay_kieu_thoi_gian = datetime.strptime(chuoi_ngay, "%Y-%m-%d").date()
            danh_sach_ngay_vuot_nguong.append(ngay_kieu_thoi_gian)
            
    danh_sach_ngay_vuot_nguong.sort()
    danh_sach_cac_mua_vu = []
    
    if len(danh_sach_ngay_vuot_nguong) > 0:
        ngay_bat_dau_vu_hien_tai = danh_sach_ngay_vuot_nguong[0]
        
        for vi_tri in range(1, len(danh_sach_ngay_vuot_nguong)):
            ngay_dang_xet = danh_sach_ngay_vuot_nguong[vi_tri]
            ngay_lien_truoc = danh_sach_ngay_vuot_nguong[vi_tri - 1]
            khoang_cach_giua_hai_ngay = (ngay_dang_xet - ngay_lien_truoc).days
            
            if khoang_cach_giua_hai_ngay > CAU_HINH_QUY_TAC["SO_NGAY_NGHI_TOI_DA"]: 
                do_dai_cua_vu_vua_qua = (ngay_lien_truoc - ngay_bat_dau_vu_hien_tai).days + 1
                if do_dai_cua_vu_vua_qua >= CAU_HINH_QUY_TAC["SO_NGAY_TOI_THIEU_MOT_VU"]:
                    danh_sach_cac_mua_vu.append((ngay_bat_dau_vu_hien_tai, ngay_lien_truoc))
                
                ngay_bat_dau_vu_hien_tai = ngay_dang_xet 
                
        ngay_cuoi_cung = danh_sach_ngay_vuot_nguong[-1]
        do_dai_vu_cuoi = (ngay_cuoi_cung - ngay_bat_dau_vu_hien_tai).days + 1
        if do_dai_vu_cuoi >= CAU_HINH_QUY_TAC["SO_NGAY_TOI_THIEU_MOT_VU"]:
            danh_sach_cac_mua_vu.append((ngay_bat_dau_vu_hien_tai, ngay_cuoi_cung))
            
    return danh_sach_cac_mua_vu

def chia_nho_mua_vu_thanh_cac_giai_doan(danh_sach_ngay_trong_vu, so_cai_du_lieu, ten_chi_so_lam_goc, sai_so_cho_phep):
    if len(danh_sach_ngay_trong_vu) == 0: 
        return []
    
    danh_sach_cac_giai_doan_hoan_thien = []
    giai_doan_hien_tai = []
    
    # Bỏ ngày đầu tiên vào giai đoạn hiện tại
    ngay_dau_tien = danh_sach_ngay_trong_vu[0]
    giai_doan_hien_tai.append(ngay_dau_tien)
    
    # Bổ sung: Biến theo dõi trạng thái "xác nhận kép" liên tiếp 2 ngày
    ngay_nghi_ngo_bien_dong = None 
    
    for vi_tri in range(1, len(danh_sach_ngay_trong_vu)):
        ngay_dang_xet = danh_sach_ngay_trong_vu[vi_tri]
        ngay_moc_cua_giai_doan = giai_doan_hien_tai[0] 
        
        gia_tri_cua_ngay_dang_xet = so_cai_du_lieu[ngay_dang_xet].get(ten_chi_so_lam_goc, 0)
        gia_tri_cua_ngay_moc = so_cai_du_lieu[ngay_moc_cua_giai_doan].get(ten_chi_so_lam_goc, 0)
        
        muc_chenh_lech = abs(gia_tri_cua_ngay_dang_xet - gia_tri_cua_ngay_moc)
        
        if muc_chenh_lech >= sai_so_cho_phep:
            if ngay_nghi_ngo_bien_dong is None:
                # TRƯỜNG HỢP 1: Ngày đầu tiên phát hiện lệch
                # Đưa vào diện tình nghi, thêm tạm vào giai đoạn cũ chứ CHƯA CẮT
                ngay_nghi_ngo_bien_dong = ngay_dang_xet
                giai_doan_hien_tai.append(ngay_dang_xet)
            else:
                # TRƯỜNG HỢP 2: Ngày thứ 2 liên tiếp vẫn lệch -> CHÍNH THỨC CẮT
                # Rút ngày tình nghi của hôm qua ra khỏi giai đoạn cũ
                giai_doan_hien_tai.pop() 
                danh_sach_cac_giai_doan_hoan_thien.append(giai_doan_hien_tai)
                
                # Bắt đầu giai đoạn mới tính từ đúng ngày phát hiện biến động (ngày hôm qua)
                giai_doan_hien_tai = [ngay_nghi_ngo_bien_dong, ngay_dang_xet]
                ngay_nghi_ngo_bien_dong = None # Reset lại trạng thái
        else:
            # TRƯỜNG HỢP 3: Giá trị không lệch (hoặc lệch rồi lại tụt về bình thường)
            # Đây là nhiễu, hủy bỏ tình trạng nghi ngờ và thêm vào giai đoạn bình thường
            ngay_nghi_ngo_bien_dong = None
            giai_doan_hien_tai.append(ngay_dang_xet)
            
    # Chốt sổ giai đoạn cuối cùng
    if len(giai_doan_hien_tai) > 0:
        danh_sach_cac_giai_doan_hoan_thien.append(giai_doan_hien_tai)
        
    return danh_sach_cac_giai_doan_hoan_thien

# =====================================================================
# PHẦN 3: HÀM VẼ BIỂU ĐỒ (CHỈ VẼ 1 BIỂU ĐỒ THEO CHỈ SỐ CHỌN)
# =====================================================================

def ve_bieu_do_chi_so_duoc_chon(du_lieu_tong_hop, danh_sach_cac_giai_doan, ten_chi_so_hien_thi, ten_bien_trong_so_cai):
    # Tạo 1 khung tranh duy nhất
    khung_tranh = plt.figure(figsize=(16, 6))
    truc_toa_do = plt.gca()
    
    # Nối tất cả các ngày lại thành 1 danh sách dài (không dùng list comprehension)
    danh_sach_ngay_thuc_te_de_ve = []
    for giai_doan in danh_sach_cac_giai_doan: 
        for ngay in giai_doan:
            danh_sach_ngay_thuc_te_de_ve.append(ngay)
            
    # Tạo trục X dạng số đếm (0, 1, 2, 3...)
    truc_x_duoi_dang_so_dem = np.arange(len(danh_sach_ngay_thuc_te_de_ve))
    
    # Lấy dữ liệu trục Y tương ứng với chỉ số được chọn
    du_lieu_doc_truc_y = []
    for ngay in danh_sach_ngay_thuc_te_de_ve:
        gia_tri_trong_ngay = du_lieu_tong_hop[ngay][ten_bien_trong_so_cai]
        du_lieu_doc_truc_y.append(gia_tri_trong_ngay)
        
    # Vẽ cột
    truc_toa_do.bar(truc_x_duoi_dang_so_dem, du_lieu_doc_truc_y, color='skyblue', edgecolor='black')
    truc_toa_do.set_ylabel(ten_chi_so_hien_thi, fontsize=12)
    truc_toa_do.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Vẽ các đường kẻ dọc màu đỏ để ngăn cách các giai đoạn
    so_luong_giai_doan = len(danh_sach_cac_giai_doan)
    if so_luong_giai_doan > 1:
        # Lặp qua tất cả các giai đoạn, TRỪ giai đoạn cuối cùng
        for vi_tri_gd in range(so_luong_giai_doan - 1):
            giai_doan_dang_xet = danh_sach_cac_giai_doan[vi_tri_gd]
            ngay_cuoi_cung_cua_giai_doan = giai_doan_dang_xet[-1]
            vi_tri_cat_giai_doan = danh_sach_ngay_thuc_te_de_ve.index(ngay_cuoi_cung_cua_giai_doan) 
            truc_toa_do.axvline(x=vi_tri_cat_giai_doan + 0.5, color='red', linestyle='-', linewidth=2.5)

    # Cấu hình nhãn ngày tháng trục X cho khỏi vướng
    buoc_nhay_hien_thi_nhan = max(1, len(danh_sach_ngay_thuc_te_de_ve) // 30) 
    danh_sach_vi_tri_dat_nhan = truc_x_duoi_dang_so_dem[::buoc_nhay_hien_thi_nhan]
    
    # Cắt lấy ngày/tháng (bỏ năm) bằng vòng lặp for
    danh_sach_nhan_ngay_thang = []
    for vi_tri in danh_sach_vi_tri_dat_nhan:
        ngay_day_du = danh_sach_ngay_thuc_te_de_ve[vi_tri]
        ngay_thang_ngan_gon = ngay_day_du[-5:] # Cắt 5 ký tự cuối cùng
        danh_sach_nhan_ngay_thang.append(ngay_thang_ngan_gon)
    
    plt.xticks(danh_sach_vi_tri_dat_nhan, danh_sach_nhan_ngay_thang, rotation=45, ha='right', fontsize=10)
    plt.title(f"Biểu đồ phân tích Cắt Giai Đoạn dựa theo: {ten_chi_so_hien_thi}", fontsize=16)
    
    return khung_tranh

# =====================================================================
# PHẦN 4: GIAO DIỆN NGƯỜI DÙNG CHÍNH (STREAMLIT)
# =====================================================================

def main():
    st.set_page_config(page_title="Phân Tích Dữ Liệu Nông Nghiệp", layout="wide")
    st.title("📊 Hệ Thống Phân Tích Logic Hợp Nhất Dữ Tại Liệu")
    
    with st.sidebar:
        st.header("📂 1. Tải Tệp Tin Dữ Liệu")
        tep_tin_nho_giot = st.file_uploader("Tải lên tệp Nhỏ giọt (JSON)", accept_multiple_files=True, type=['json'])
        tep_tin_cham_phan = st.file_uploader("Tải lên tệp Châm phân (JSON)", accept_multiple_files=True, type=['json'])
        khu_vuc_chuyen_doi = st.selectbox("Chọn khu vực cần phân tích", ["1", "2", "3", "4"])
        
        st.markdown("---")
        st.header("⚙️ 2. Cài Đặt Thuật Toán Cắt Giai Đoạn")
        st.caption("Hệ thống sẽ dùng 1 chỉ số làm mốc để chia giai đoạn.")
        
        tu_dien_chi_so_dieu_khien = {"Lần tưới": "so_lan_tuoi", "TBEC": "tbec", "EC Yêu cầu": "ec_yeu_cau"}
        ten_chi_so_hien_thi = st.selectbox("🎯 Chọn Chỉ số làm Mốc", list(tu_dien_chi_so_dieu_khien.keys()))
        ten_bien_chi_so_goc = tu_dien_chi_so_dieu_khien[ten_chi_so_hien_thi]
        
        # Thiết lập ngưỡng và sai số mặc định riêng cho từng chỉ số
        if ten_bien_chi_so_goc == "so_lan_tuoi":
            gia_tri_nguong_goi_y, gia_tri_sai_so_goi_y = 8.1, 5.0
        elif ten_bien_chi_so_goc == "tbec":
            gia_tri_nguong_goi_y, gia_tri_sai_so_goi_y = 0.38, 0.14
        else: # EC_yeu_cau
            gia_tri_nguong_goi_y, gia_tri_sai_so_goi_y = 0.90, 0.16
            
        nguong_bat_dau_vu = st.number_input(f"📈 Ngưỡng Bắt Đầu Vụ ({ten_chi_so_hien_thi})", value=gia_tri_nguong_goi_y, step=0.1)
        sai_so_cat_giai_doan = st.number_input(f"✂️ Sai Số Cắt GĐ ({ten_chi_so_hien_thi})", value=gia_tri_sai_so_goi_y, step=0.1)

    if tep_tin_nho_giot and tep_tin_cham_phan:
        # BƯỚC 1: Lập Sổ Cái
        so_cai_du_lieu_hoan_chinh = tao_so_cai_du_lieu_tong_hop(tep_tin_nho_giot, tep_tin_cham_phan, khu_vuc_chuyen_doi)
        
        # Nếu Sổ cái trống, thông báo lỗi
        if len(so_cai_du_lieu_hoan_chinh) == 0:
            st.error("❌ Không tìm thấy dữ liệu cho khu vực này trong các tệp đã tải lên.")
            return
            
        # BƯỚC 2: Tìm Mùa Vụ
        danh_sach_cac_mua_vu = tim_kiem_cac_mua_vu(so_cai_du_lieu_hoan_chinh, ten_bien_chi_so_goc, nguong_bat_dau_vu)
        
        if len(danh_sach_cac_mua_vu) == 0:
            st.warning(f"⚠️ Không tìm thấy vụ nào có {ten_chi_so_hien_thi} vượt qua mức ngưỡng {nguong_bat_dau_vu} liên tục trên 7 ngày.")
            return
            
        # Tạo danh sách tên để hiển thị lên hộp chọn (Không dùng list comprehension)
        danh_sach_ten_hien_thi_mua_vu = []
        for vi_tri_vu in range(len(danh_sach_cac_mua_vu)):
            vu_mua_dang_xet = danh_sach_cac_mua_vu[vi_tri_vu]
            ngay_bat_dau_chuoi = vu_mua_dang_xet[0].strftime('%d/%m/%Y')
            ngay_ket_thuc_chuoi = vu_mua_dang_xet[1].strftime('%d/%m/%Y')
            ten_vu = f"Vụ {vi_tri_vu + 1}: {ngay_bat_dau_chuoi} đến {ngay_ket_thuc_chuoi}"
            danh_sach_ten_hien_thi_mua_vu.append(ten_vu)
            
        # Hàm phụ để hiển thị tên thay cho lambda
        def ham_hien_thi_ten_mua_vu(vi_tri):
            return danh_sach_ten_hien_thi_mua_vu[vi_tri]
            
        vi_tri_vu_duoc_chon = st.selectbox(
            "🌾 3. Chọn Mùa Vụ Để Phân Tích Chi Tiết", 
            range(len(danh_sach_cac_mua_vu)), 
            format_func=ham_hien_thi_ten_mua_vu
        )
        
        vu_mua_da_chot = danh_sach_cac_mua_vu[vi_tri_vu_duoc_chon]
        
        # Lọc ra những ngày nằm gọn trong mùa vụ đã chọn (Bỏ list comprehension)
        cac_ngay_trong_vu_mua_nay = []
        for ngay_chuoi in so_cai_du_lieu_hoan_chinh.keys():
            ngay_kieu_thoi_gian = datetime.strptime(ngay_chuoi, "%Y-%m-%d").date()
            if vu_mua_da_chot[0] <= ngay_kieu_thoi_gian <= vu_mua_da_chot[1]:
                cac_ngay_trong_vu_mua_nay.append(ngay_chuoi)
                
        # Sắp xếp ngày từ cũ đến mới
        cac_ngay_trong_vu_mua_nay.sort()
        
        # BƯỚC 3: Cắt Giai Đoạn
        danh_sach_cac_giai_doan_cua_vu = chia_nho_mua_vu_thanh_cac_giai_doan(
            cac_ngay_trong_vu_mua_nay, 
            so_cai_du_lieu_hoan_chinh, 
            ten_bien_chi_so_goc, 
            sai_so_cat_giai_doan
        )
        
        st.success(f"✅ Hệ thống đang phân tích theo **{ten_chi_so_hien_thi}**. Đã cắt được thành công **{len(danh_sach_cac_giai_doan_cua_vu)} giai đoạn**.")

        # BƯỚC 4: Hiển thị kết quả
        st.subheader(f"📈 Biểu Đồ {ten_chi_so_hien_thi} (Các đường kẻ dọc màu đỏ là mốc chia giai đoạn)")
        bieu_do_hoan_thien = ve_bieu_do_chi_so_duoc_chon(
            so_cai_du_lieu_hoan_chinh, 
            danh_sach_cac_giai_doan_cua_vu, 
            ten_chi_so_hien_thi, 
            ten_bien_chi_so_goc
        )
        st.pyplot(bieu_do_hoan_thien)
        
        st.subheader("📋 Bảng Tổng Hợp Dữ Liệu Từng Ngày")
        du_lieu_hien_thi_len_bang = []
        for chi_muc_giai_doan in range(len(danh_sach_cac_giai_doan_cua_vu)):
            giai_doan_dang_xet = danh_sach_cac_giai_doan_cua_vu[chi_muc_giai_doan]
            for ngay in giai_doan_dang_xet:
                du_lieu_hien_thi_len_bang.append({
                    "Giai đoạn": f"Giai đoạn {chi_muc_giai_doan + 1}",
                    "Ngày": ngay,
                    "Số Lần Tưới": so_cai_du_lieu_hoan_chinh[ngay]['so_lan_tuoi'],
                    "Thời Gian (Phút)": so_cai_du_lieu_hoan_chinh[ngay]['thoi_gian_tuoi_phut'],
                    "EC Trung Bình (TBEC)": so_cai_du_lieu_hoan_chinh[ngay]['tbec'],
                    "EC Yêu Cầu": so_cai_du_lieu_hoan_chinh[ngay]['ec_yeu_cau']
                })
        
        st.dataframe(du_lieu_hien_thi_len_bang, use_container_width=True)
    else:
        st.info("👈 Bạn vui lòng tải lên cả 2 tệp Nhỏ Giọt và Châm Phân ở cột điều khiển bên trái để bắt đầu nhé.")

if __name__ == "__main__":
    main()
