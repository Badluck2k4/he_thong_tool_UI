# =====================================================================
# PHẦN 1: CẤU HÌNH & KHỞI TẠO (PHÒNG QUẢN LÝ)
# =====================================================================
import streamlit as st
import numpy as np
import json
from datetime import datetime
import matplotlib.pyplot as plt

# 1. Hằng số luật chơi chung (Viết hoa toàn bộ để phân biệt)
CAU_HINH_GOC = {
    "GIAY_TUOI_TOI_THIEU": 20,    # Thời gian tưới tối thiểu để được ghi nhận (giây)
    "GIAY_TUOI_TOI_DA": 3600,     # Thời gian tưới tối đa (giây)
    "LAN_TUOI_TOI_THIEU": 5,      # Số lần tưới tối thiểu trong 1 ngày
    "SO_NGAY_NGHI_TOI_DA": 2,     # Khoảng cách ngày nghỉ tối đa trước khi ngắt Vụ mới
    "SO_NGAY_TOI_THIEU_MOT_VU": 7 # Một vụ mùa phải kéo dài ít nhất bao nhiêu ngày
}

# 2. Khởi tạo bộ nhớ tạm cho các ô nhập liệu sai số
if 'sai_so_lan_tuoi' not in st.session_state: st.session_state.sai_so_lan_tuoi = 1.0
if 'sai_so_tbec' not in st.session_state: st.session_state.sai_so_tbec = 0.5
if 'sai_so_ec_yeu_cau' not in st.session_state: st.session_state.sai_so_ec_yeu_cau = 0.5


# =====================================================================
# PHẦN 2: LÕI XỬ LÝ DỮ LIỆU (NHÀ BẾP - LÕI THUẬT TOÁN)
# =====================================================================

def lay_gia_tri_so_thuc(dong_du_lieu, danh_sach_tu_khoa):
    """Tìm giá trị trong từ điển dựa vào từ khóa, đổi phẩy thành chấm và ép kiểu số"""
    for tu_khoa in danh_sach_tu_khoa:
        gia_tri = dong_du_lieu.get(tu_khoa)
        if gia_tri is not None:
            try:
                # Tránh lỗi do dữ liệu ghi dấu phẩy (VD: 1,5 -> 1.5)
                chuoi_gia_tri = str(gia_tri).replace(',', '.')
                return float(chuoi_gia_tri)
            except (ValueError, TypeError):
                continue
    return None

def xu_ly_file_nho_giot(danh_sach_file_nho_giot, khu_vuc_duoc_chon):
    """Đọc file nhỏ giọt, lọc theo khu vực và tính tổng thời gian/số lần tưới mỗi ngày"""
    du_lieu_tong_hop = []
    
    # Đọc tất cả các file được up lên
    for file in danh_sach_file_nho_giot:
        file.seek(0)
        du_lieu_tong_hop.extend(json.load(file))
        
    # Lọc riêng khu vực và sắp xếp theo thời gian tăng dần
    du_lieu_khu_vuc = []
    for dong in du_lieu_tong_hop:
        if str(dong.get('STT')) == khu_vuc_duoc_chon:
            du_lieu_khu_vuc.append(dong)
            
    du_lieu_khu_vuc.sort(key=lambda x: x['Thời gian'])
    
    # Chuẩn bị sổ ghi chép
    so_lan_tuoi_theo_ngay = {}
    tong_giay_tuoi_theo_ngay = {}
    
    # Quét dữ liệu tìm cặp Bật - Tắt
    tong_so_dong = len(du_lieu_khu_vuc)
    for i in range(tong_so_dong - 1):
        trang_thai_hien_tai = du_lieu_khu_vuc[i].get('Trạng thái')
        trang_thai_tiep_theo = du_lieu_khu_vuc[i+1].get('Trạng thái')
        
        if trang_thai_hien_tai == "Bật" and trang_thai_tiep_theo == "Tắt":
            thoi_diem_bat_dau = datetime.strptime(du_lieu_khu_vuc[i]['Thời gian'], "%Y-%m-%d %H-%M-%S")
            thoi_diem_ket_thuc = datetime.strptime(du_lieu_khu_vuc[i+1]['Thời gian'], "%Y-%m-%d %H-%M-%S")
            
            khoang_thoi_gian_giay = (thoi_diem_ket_thuc - thoi_diem_bat_dau).total_seconds()
            
            # Lọc nhiễu: Chỉ lấy những lần tưới hợp lệ
            if CAU_HINH_GOC["GIAY_TUOI_TOI_THIEU"] <= khoang_thoi_gian_giay <= CAU_HINH_GOC["GIAY_TUOI_TOI_DA"]:
                ngay_chuoi = thoi_diem_bat_dau.strftime("%Y-%m-%d")
                
                # Cộng dồn số lần và thời gian vào ngày tương ứng
                so_lan_tuoi_theo_ngay[ngay_chuoi] = so_lan_tuoi_theo_ngay.get(ngay_chuoi, 0) + 1
                tong_giay_tuoi_theo_ngay[ngay_chuoi] = tong_giay_tuoi_theo_ngay.get(ngay_chuoi, 0) + khoang_thoi_gian_giay
                
    return so_lan_tuoi_theo_ngay, tong_giay_tuoi_theo_ngay

def tim_kiem_cac_mua_vu(so_lan_tuoi_theo_ngay):
    """Tìm các Mùa Vụ dựa trên những ngày tưới hợp lệ và khoảng cách ngày nghỉ"""
    danh_sach_ngay_hop_le = []
    
    # Bước 1: Chỉ lấy những ngày có số lần tưới đạt chuẩn
    for chuoi_ngay, so_lan in so_lan_tuoi_theo_ngay.items():
        if so_lan >= CAU_HINH_GOC["LAN_TUOI_TOI_THIEU"]:
            ngay_dinh_dang = datetime.strptime(chuoi_ngay, "%Y-%m-%d").date()
            danh_sach_ngay_hop_le.append(ngay_dinh_dang)
            
    danh_sach_ngay_hop_le.sort()
    danh_sach_mua_vu = []
    
    # Bước 2: Chặt dữ liệu thành các vụ nếu có đứt gãy (ngày nghỉ)
    if danh_sach_ngay_hop_le:
        ngay_bat_dau_vu = danh_sach_ngay_hop_le[0]
        
        for i in range(1, len(danh_sach_ngay_hop_le)):
            ngay_dang_xet = danh_sach_ngay_hop_le[i]
            ngay_lien_truoc = danh_sach_ngay_hop_le[i-1]
            
            khoang_cach_ngay = (ngay_dang_xet - ngay_lien_truoc).days
            
            # Nếu nghỉ quá lâu -> Chốt vụ cũ, mở vụ mới
            if khoang_cach_ngay > CAU_HINH_GOC["SO_NGAY_NGHI_TOI_DA"]: 
                do_dai_vu_cu = (ngay_lien_truoc - ngay_bat_dau_vu).days + 1
                
                if do_dai_vu_cu >= CAU_HINH_GOC["SO_NGAY_TOI_THIEU_MOT_VU"]:
                    danh_sach_mua_vu.append((ngay_bat_dau_vu, ngay_lien_truoc))
                    
                ngay_bat_dau_vu = ngay_dang_xet # Dời mốc bắt đầu
                
        # Vét nốt vụ cuối cùng sau khi hết vòng lặp
        ngay_cuoi_cung = danh_sach_ngay_hop_le[-1]
        if (ngay_cuoi_cung - ngay_bat_dau_vu).days + 1 >= CAU_HINH_GOC["SO_NGAY_TOI_THIEU_MOT_VU"]:
            danh_sach_mua_vu.append((ngay_bat_dau_vu, ngay_cuoi_cung))
        
    return danh_sach_mua_vu

def tong_hop_du_lieu_theo_vu(danh_sach_file_cham_phan, khu_vuc_duoc_chon, mua_vu_dang_chon, so_lan_tuoi_theo_ngay, tong_giay_tuoi_theo_ngay):
    """Ghép dữ liệu châm phân vào dữ liệu nhỏ giọt để tạo Sổ Cái cho mùa vụ đang chọn"""
    
    ngay_bat_dau_vu = mua_vu_dang_chon[0]
    ngay_ket_thuc_vu = mua_vu_dang_chon[1]
    so_ghi_chep_cham_phan = {}
    
    # Bước 1: Quét file Châm Phân
    for file in danh_sach_file_cham_phan:
        file.seek(0)
        for dong in json.load(file):
            if str(dong.get('STT')) != khu_vuc_duoc_chon: 
                continue
                
            thoi_diem = datetime.strptime(dong['Thời gian'], "%Y-%m-%d %H-%M-%S")
            ngay_cua_dong = thoi_diem.date()
            
            # Chỉ lấy dữ liệu nằm trong Mùa Vụ đang chọn
            if ngay_bat_dau_vu <= ngay_cua_dong <= ngay_ket_thuc_vu:
                chuoi_ngay = thoi_diem.strftime("%Y-%m-%d")
                
                # Khởi tạo trang sổ mới nếu chưa có
                if chuoi_ngay not in so_ghi_chep_cham_phan: 
                    so_ghi_chep_cham_phan[chuoi_ngay] = {'danh_sach_tbec': [], 'danh_sach_ec_yeu_cau': []}
                
                # Lấy số thực
                gia_tri_tbec = lay_gia_tri_so_thuc(dong, ['TBEC', 'tbec'])
                gia_tri_ec_yeu_cau = lay_gia_tri_so_thuc(dong, ['EC yêu cầu', 'ecreq'])
                
                if gia_tri_tbec is not None: 
                    so_ghi_chep_cham_phan[chuoi_ngay]['danh_sach_tbec'].append(gia_tri_tbec)
                if gia_tri_ec_yeu_cau is not None: 
                    so_ghi_chep_cham_phan[chuoi_ngay]['danh_sach_ec_yeu_cau'].append(gia_tri_ec_yeu_cau)

    # Bước 2: Tính toán trung bình và gom lại thành một cục Dữ Liệu Tổng Hợp
    du_lieu_tong_hop = {}
    danh_sach_ngay_trong_vu = []
    
    # Lọc lấy các ngày thuộc vụ này từ sổ Nhỏ Giọt và sắp xếp
    for chuoi_ngay in so_lan_tuoi_theo_ngay.keys():
        ngay_dinh_dang = datetime.strptime(chuoi_ngay, "%Y-%m-%d").date()
        if ngay_bat_dau_vu <= ngay_dinh_dang <= ngay_ket_thuc_vu:
            danh_sach_ngay_trong_vu.append(chuoi_ngay)
            
    danh_sach_ngay_trong_vu.sort()
    
    for chuoi_ngay in danh_sach_ngay_trong_vu:
        # Tính trung bình TBEC
        if chuoi_ngay in so_ghi_chep_cham_phan and so_ghi_chep_cham_phan[chuoi_ngay]['danh_sach_tbec']:
            tbec_trung_binh = np.mean(so_ghi_chep_cham_phan[chuoi_ngay]['danh_sach_tbec'])
        else:
            tbec_trung_binh = 0.0
            
        # Tính trung bình EC Yêu cầu
        if chuoi_ngay in so_ghi_chep_cham_phan and so_ghi_chep_cham_phan[chuoi_ngay]['danh_sach_ec_yeu_cau']:
            ec_yeu_cau_trung_binh = np.mean(so_ghi_chep_cham_phan[chuoi_ngay]['danh_sach_ec_yeu_cau'])
        else:
            ec_yeu_cau_trung_binh = 0.0
            
        tong_phut_tuoi = int(round(tong_giay_tuoi_theo_ngay.get(chuoi_ngay, 0) / 60))
        
        du_lieu_tong_hop[chuoi_ngay] = {
            'so_lan_tuoi': so_lan_tuoi_theo_ngay[chuoi_ngay],
            'thoi_gian_tuoi_phut': tong_phut_tuoi,
            'tbec': float(f"{tbec_trung_binh:.2f}"),
            'ec_yeu_cau': float(f"{ec_yeu_cau_trung_binh:.2f}")
        }
        
    return du_lieu_tong_hop, danh_sach_ngay_trong_vu

def chia_nho_thanh_cac_giai_doan(danh_sach_ngay_trong_vu, du_lieu_tong_hop, danh_sach_sai_so):
    """Cắt nhỏ mùa vụ thành các giai đoạn dựa trên biến thiên của các chỉ số"""
    if not danh_sach_sai_so or not danh_sach_ngay_trong_vu: 
        return [danh_sach_ngay_trong_vu]
    
    tat_ca_giai_doan = []
    giai_doan_hien_tai = [danh_sach_ngay_trong_vu[0]]
    
    for i in range(1, len(danh_sach_ngay_trong_vu)):
        ngay_dang_xet = danh_sach_ngay_trong_vu[i]
        ngay_moc_so_sanh = giai_doan_hien_tai[-1] # Lấy ngày cuối của giai đoạn hiện tại làm mốc
        
        danh_sach_kiem_tra_bien_thien = []
        
        # Kiểm tra xem hôm nay có biến thiên so với mốc không (dựa trên các chỉ số được tick)
        for ten_chi_so, muc_sai_so in danh_sach_sai_so.items():
            gia_tri_hom_nay = du_lieu_tong_hop[ngay_dang_xet].get(ten_chi_so)
            gia_tri_moc = du_lieu_tong_hop[ngay_moc_so_sanh].get(ten_chi_so)
            
            if gia_tri_hom_nay is not None and gia_tri_moc is not None:
                do_chenh_lech = abs(gia_tri_hom_nay - gia_tri_moc)
                if do_chenh_lech >= muc_sai_so:
                    danh_sach_kiem_tra_bien_thien.append(True)
                    
        # Nếu tất cả các chỉ số yêu cầu đều có sự biến thiên -> Ngắt giai đoạn
        tong_so_dieu_kien = len(danh_sach_sai_so)
        if len(danh_sach_kiem_tra_bien_thien) == tong_so_dieu_kien and all(danh_sach_kiem_tra_bien_thien):
            tat_ca_giai_doan.append(giai_doan_hien_tai)
            giai_doan_hien_tai = [ngay_dang_xet] # Mở giai đoạn mới
        else:
            giai_doan_hien_tai.append(ngay_dang_xet) # Chưa đủ biến thiên -> Nối tiếp ngày vào giai đoạn cũ
            
    tat_ca_giai_doan.append(giai_doan_hien_tai) # Vét nốt giai đoạn cuối
    return tat_ca_giai_doan


# =====================================================================
# PHẦN 3: LÕI VẼ BIỂU ĐỒ (TRẠM TRANG TRÍ MÓN ĂN)
# =====================================================================

def ve_bieu_do_dong_thoi(du_lieu_tong_hop, tat_ca_giai_doan, danh_sach_chi_so_can_ve):
    # Trả về khung trống nếu không có gì để vẽ
    if not danh_sach_chi_so_can_ve or not tat_ca_giai_doan:
        khung_tranh, truc_toa_do = plt.subplots(figsize=(10, 5))
        truc_toa_do.text(0.5, 0.5, 'Chưa có chỉ số nào được chọn để vẽ', ha='center', va='center')
        return khung_tranh

    so_tang_bieu_do = len(danh_sach_chi_so_can_ve)
    khung_tranh, danh_sach_truc = plt.subplots(so_tang_bieu_do, 1, figsize=(16, 4 * so_tang_bieu_do), sharex=True)
    
    # Đảm bảo danh_sach_truc luôn là một danh sách (kể cả khi chỉ vẽ 1 biểu đồ)
    if so_tang_bieu_do == 1: 
        danh_sach_truc = [danh_sach_truc] 
    
    # Trải phẳng tất cả các ngày từ các giai đoạn ra thành 1 trục X liên tục
    danh_sach_ngay_thuc_te = []
    for giai_doan in tat_ca_giai_doan: 
        danh_sach_ngay_thuc_te.extend(giai_doan)
        
    # Tạo trục X dạng số đếm (0, 1, 2...) để thư viện dễ xử lý khoảng cách cột
    truc_x_so_dem = np.arange(len(danh_sach_ngay_thuc_te))
    
    # Bộ từ điển dịch tên hiển thị sang tên biến trong dữ liệu
    tu_dien_dich_chi_so = {
        "Lần tưới": "so_lan_tuoi", 
        "TBEC": "tbec", 
        "EC Yêu cầu": "ec_yeu_cau"
    }
    
    # Bắt đầu vẽ từng tầng biểu đồ
    for vi_tri, ten_chi_so in enumerate(danh_sach_chi_so_can_ve):
        truc_hien_tai = danh_sach_truc[vi_tri]
        ten_bien_du_lieu = tu_dien_dich_chi_so[ten_chi_so]
        
        # Nhặt dữ liệu trục Y tương ứng với từng ngày
        du_lieu_truc_y = [du_lieu_tong_hop[ngay][ten_bien_du_lieu] for ngay in danh_sach_ngay_thuc_te]
        
        # Vẽ cột
        truc_hien_tai.bar(truc_x_so_dem, du_lieu_truc_y, color='skyblue', edgecolor='black')
        truc_hien_tai.set_ylabel(ten_chi_so, fontsize=12)
        truc_hien_tai.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Kẻ đường ranh giới đỏ (Nhát cắt giai đoạn)
        if len(tat_ca_giai_doan) > 1:
            for giai_doan in tat_ca_giai_doan[:-1]:
                ngay_cuoi_cung_cua_giai_doan = giai_doan[-1]
                vi_tri_cat_tren_truc_x = danh_sach_ngay_thuc_te.index(ngay_cuoi_cung_cua_giai_doan) 
                
                # Cắt ở mép phải của cột (vi_tri + 0.5)
                truc_hien_tai.axvline(x=vi_tri_cat_tren_truc_x + 0.5, color='red', linestyle='--', linewidth=2)
                
    # --- CHỐNG CHỒNG CHÉO CHỮ TRÊN TRỤC X ---
    # Nếu có quá 30 ngày, hệ thống tự động nhảy cách 2, 3 ngày để in nhãn
    buoc_nhay_nhan = max(1, len(danh_sach_ngay_thuc_te) // 30) 
    
    danh_sach_vi_tri_in_nhan = truc_x_so_dem[::buoc_nhay_nhan]
    danh_sach_nhan_hien_thi = [f"Ngày {idx + 1}" for idx in danh_sach_vi_tri_in_nhan]
    
    # Ép buộc in số thẳng đứng
    plt.xticks(danh_sach_vi_tri_in_nhan, danh_sach_nhan_hien_thi, rotation=0, ha='center', fontsize=10)
    
    # Tạo khoảng trống giữa các tầng biểu đồ
    khung_tranh.subplots_adjust(hspace=0.4) 
    
    return khung_tranh

# =====================================================================
# PHẦN 4: GIAO DIỆN NGƯỜI DÙNG (SÂN KHẤU VÀ BỒI BÀN)
# =====================================================================

def main():
    st.set_page_config(page_title="Phân Tích Dữ Liệu", layout="wide")
    st.title("📊 Bảng Điều Khiển Phân Tích Tưới Tiêu")
    
    # ---------------------------------------------------------
    # GIAO DIỆN CỘT TRÁI (SIDEBAR): CẤU HÌNH ĐẦU VÀO
    # ---------------------------------------------------------
    with st.sidebar:
        st.header("📂 1. Tải Dữ Liệu")
        danh_sach_file_nho_giot = st.file_uploader("Upload file Nhỏ giọt (JSON)", accept_multiple_files=True, type=['json'])
        danh_sach_file_cham_phan = st.file_uploader("Upload file Châm phân (JSON)", accept_multiple_files=True, type=['json'])
        
        khu_vuc_duoc_chon = st.selectbox("Chọn khu vực", ["1", "2", "3", "4"])
        
        st.header("⚙️ 2. Cấu Hình Cắt Giai Đoạn")
        st.caption("Tick chọn chỉ số và nhập sai số muốn ngắt:")
        
        cot_trai, cot_phai = st.columns([1, 1])
        with cot_trai: co_chon_lan_tuoi = st.checkbox("Lần tưới")
        with cot_phai: sai_so_lan_tuoi = st.number_input("Sai số Lần", value=st.session_state.sai_so_lan_tuoi, step=0.5)
        
        cot_trai, cot_phai = st.columns([1, 1])
        with cot_trai: co_chon_tbec = st.checkbox("TBEC")
        with cot_phai: sai_so_tbec = st.number_input("Sai số TBEC", value=st.session_state.sai_so_tbec, step=0.1)
        
        cot_trai, cot_phai = st.columns([1, 1])
        with cot_trai: co_chon_ec_yeu_cau = st.checkbox("EC Y/C")
        with cot_phai: sai_so_ec_yeu_cau = st.number_input("Sai số Req", value=st.session_state.sai_so_ec_yeu_cau, step=0.1)

    # ---------------------------------------------------------
    # LUỒNG THỰC THI CHÍNH
    # ---------------------------------------------------------
    if danh_sach_file_nho_giot and danh_sach_file_cham_phan:
        
        # BƯỚC A & B: Gọi bếp xử lý file và tìm mùa vụ
        so_lan_tuoi_theo_ngay, tong_giay_tuoi_theo_ngay = xu_ly_file_nho_giot(danh_sach_file_nho_giot, khu_vuc_duoc_chon)
        danh_sach_mua_vu = tim_kiem_cac_mua_vu(so_lan_tuoi_theo_ngay)
        
        if not danh_sach_mua_vu:
            st.warning("Không tìm thấy mùa vụ nào hợp lệ (Ít nhất 7 ngày, mỗi ngày tưới > 5 lần).")
            return
            
        # Hiển thị nút chọn Mùa Vụ
        danh_sach_ten_vu = [f"Vụ {i+1}: {vu[0].strftime('%d/%m/%Y')} - {vu[1].strftime('%d/%m/%Y')}" 
                            for i, vu in enumerate(danh_sach_mua_vu)]
                            
        vi_tri_vu_chon = st.selectbox("🌾 3. Chọn Mùa Vụ Để Phân Tích", range(len(danh_sach_mua_vu)), format_func=lambda x: danh_sach_ten_vu[x])
        mua_vu_dang_chon = danh_sach_mua_vu[vi_tri_vu_chon]
        
        # BƯỚC C: Gom dữ liệu tạo Sổ Cái theo mùa vụ đã chọn
        du_lieu_tong_hop, danh_sach_ngay_trong_vu = tong_hop_du_lieu_theo_vu(
            danh_sach_file_cham_phan, khu_vuc_duoc_chon, mua_vu_dang_chon, so_lan_tuoi_theo_ngay, tong_giay_tuoi_theo_ngay)
            
        if not du_lieu_tong_hop:
            st.warning("Không có dữ liệu châm phân cho mùa vụ này.")
            return

        # BƯỚC D: Lấy cấu hình sai số từ UI và chạy thuật toán cắt giai đoạn
        danh_sach_sai_so_ngat_quang = {}
        danh_sach_chi_so_can_ve = [] 
        
        if co_chon_lan_tuoi: 
            danh_sach_sai_so_ngat_quang['so_lan_tuoi'] = sai_so_lan_tuoi
            danh_sach_chi_so_can_ve.append("Lần tưới")
        if co_chon_tbec: 
            danh_sach_sai_so_ngat_quang['tbec'] = sai_so_tbec
            danh_sach_chi_so_can_ve.append("TBEC")
        if co_chon_ec_yeu_cau: 
            danh_sach_sai_so_ngat_quang['ec_yeu_cau'] = sai_so_ec_yeu_cau
            danh_sach_chi_so_can_ve.append("EC Yêu cầu")
            
        # Chạy thuật toán cắt giai đoạn
        tat_ca_giai_doan = chia_nho_thanh_cac_giai_doan(danh_sach_ngay_trong_vu, du_lieu_tong_hop, danh_sach_sai_so_ngat_quang)
        
        st.success(f"✅ Hệ thống đã phân tích và cắt thành **{len(tat_ca_giai_doan)} giai đoạn** dựa trên các sai số bạn chọn.")

        # BƯỚC E: Giao cho Họa sĩ vẽ và hiển thị Biểu đồ
        st.subheader("📈 Biểu Đồ Trực Quan")
        khung_tranh = ve_bieu_do_dong_thoi(du_lieu_tong_hop, tat_ca_giai_doan, danh_sach_chi_so_can_ve)
        st.pyplot(khung_tranh)
        
        # BƯỚC F: Bày biện dữ liệu ra Bảng
        st.subheader("📋 Bảng Dữ Liệu Chi Tiết")
        bang_du_lieu_hien_thi = []
        
        for chi_so_giai_doan, danh_sach_ngay_trong_giai_doan in enumerate(tat_ca_giai_doan):
            for chuoi_ngay in danh_sach_ngay_trong_giai_doan:
                bang_du_lieu_hien_thi.append({
                    "Giai đoạn": f"Giai đoạn {chi_so_giai_doan + 1}",
                    "Ngày": chuoi_ngay,
                    "Lần tưới": du_lieu_tong_hop[chuoi_ngay]['so_lan_tuoi'],
                    "Phút tưới": du_lieu_tong_hop[chuoi_ngay]['thoi_gian_tuoi_phut'],
                    "TBEC": du_lieu_tong_hop[chuoi_ngay]['tbec'],
                    "EC Req": du_lieu_tong_hop[chuoi_ngay]['ec_yeu_cau']
                })
        
        st.dataframe(bang_du_lieu_hien_thi, use_container_width=True)

    else:
        st.info("👈 Vui lòng tải lên file dữ liệu Nhỏ Giọt và Châm Phân ở thanh bên trái để bắt đầu.")

# Khởi động Streamlit
if __name__ == "__main__":
    main()
