# =====================================================================
# PHẦN 1: CẤU HÌNH & KHỞI TẠO (PHÒNG QUẢN LÝ)
# =====================================================================
"""
Vai trò cốt lõi: Nơi thiết lập luật chơi và chuẩn bị công cụ trước khi nhà hàng mở cửa.
Nhiệm vụ: 
- Khai báo các thư viện (đưa công cụ vào).
- Định nghĩa GIATRI_GOC chứa các hằng số không thay đổi.
- Khởi tạo bộ nhớ tạm (st.session_state) để lưu dữ liệu UI.
Nguyên tắc: TUYỆT ĐỐI KHÔNG viết hàm tính toán hay lệnh in giao diện (st.write) ở đây.
"""
import streamlit as st
import numpy as np
import json
from datetime import datetime
import matplotlib.pyplot as plt

# 1. Hằng số luật chơi chung (Sửa thông số ở đây, toàn hệ thống sẽ thay đổi theo)
GIATRI_GOC = {
    "GIAY_MIN": 20,       # Thời gian tưới tối thiểu để được ghi nhận (giây)
    "GIAY_MAX": 3600,     # Thời gian tưới tối đa (giây)
    "LAN_MIN_NGAY": 5,    # Số lần tưới tối thiểu trong 1 ngày để không bị coi là ngày nghỉ
    "GAP_NGAY": 2,        # Số ngày nghỉ liên tiếp tối đa trước khi bị ngắt thành Vụ mới
    "MIN_VU": 7           # Một vụ mùa hợp lệ phải kéo dài ít nhất bao nhiêu ngày
}

# 2. Khởi tạo bộ nhớ tạm (Session State) cho giao diện
if 'ss_lan_key' not in st.session_state: st.session_state.ss_lan_key = 1.0
if 'ss_tbec_key' not in st.session_state: st.session_state.ss_tbec_key = 0.5
if 'ss_req_key' not in st.session_state: st.session_state.ss_req_key = 0.5


# =====================================================================
# PHẦN 2: LÕI XỬ LÝ DỮ LIỆU (NHÀ BẾP - LÕI THUẬT TOÁN)
# =====================================================================
"""
Vai trò cốt lõi: "Bộ não" của hệ thống. Nơi các thuật toán phức tạp nhất hoạt động.
Nhiệm vụ:
- Xử lý file, làm sạch dữ liệu rác.
- Chạy thuật toán Cắt Mùa Vụ và Cắt Giai Đoạn.
Nguyên tắc: CẤM VẬN GIAO DIỆN. Các hàm ở đây chỉ nhận nguyên liệu (tham số), 
tính toán và trả ra (return) dữ liệu sạch. Không dùng lệnh in ra màn hình ở đây.
"""

def chuyen_doi_so_thuc(du_lieu, danh_sach_khoa):
    """Làm sạch dữ liệu: Đổi dấu phẩy thành dấu chấm và ép kiểu số thực"""
    for khoa in danh_sach_khoa:
        gia_tri = du_lieu.get(khoa)
        if gia_tri is not None:
            try:
                return float(str(gia_tri).replace(',', '.'))
            except (ValueError, TypeError):
                continue
    return None

def xu_ly_file_nho_giot(tep_nho_giot, khu_vuc):
    """Lọc dữ liệu nhỏ giọt theo khu vực, sắp xếp thời gian và tìm số lần/số phút tưới"""
    du_lieu_tho = []
    for tep in tep_nho_giot:
        tep.seek(0)
        du_lieu_tho.extend(json.load(tep))
        
    # Lọc khu vực và sắp xếp theo thời gian từ cũ đến mới
    data_kv = sorted([d for d in du_lieu_tho if str(d.get('STT')) == khu_vuc], 
                     key=lambda x: x['Thời gian'])
    
    thong_ke_ngay = {}
    thoi_gian_ngay = {}
    
    # Truy tìm cặp lệnh "Bật - Tắt" để tính thời gian
    for i in range(len(data_kv)-1):
        if data_kv[i].get('Trạng thái') == "Bật" and data_kv[i+1].get('Trạng thái') == "Tắt":
            t1 = datetime.strptime(data_kv[i]['Thời gian'], "%Y-%m-%d %H-%M-%S")
            t2 = datetime.strptime(data_kv[i+1]['Thời gian'], "%Y-%m-%d %H-%M-%S")
            thoi_gian_tuoi = (t2 - t1).total_seconds()
            
            # Lọc nhiễu: Chỉ lấy những lần tưới nằm trong khung thời gian hợp lệ
            if GIATRI_GOC["GIAY_MIN"] <= thoi_gian_tuoi <= GIATRI_GOC["GIAY_MAX"]:
                d_str = t1.strftime("%Y-%m-%d")
                thong_ke_ngay[d_str] = thong_ke_ngay.get(d_str, 0) + 1
                thoi_gian_ngay[d_str] = thoi_gian_ngay.get(d_str, 0) + thoi_gian_tuoi
                
    return thong_ke_ngay, thoi_gian_ngay

def tim_kiem_mua_vu(thong_ke_ngay):
    """Tìm các khoảng đứt gãy (ngày nghỉ) để chặt dữ liệu thành từng Mùa Vụ riêng biệt"""
    # Lọc bỏ những ngày tưới lắt nhắt (dưới LAN_MIN_NGAY)
    ngay_ok = sorted([datetime.strptime(n, "%Y-%m-%d").date() 
                      for n, c in thong_ke_ngay.items() if c >= GIATRI_GOC["LAN_MIN_NGAY"]])
    
    danh_sach_vu = []
    if ngay_ok:
        start = ngay_ok[0]
        for i in range(1, len(ngay_ok)):
            # Nếu chênh lệch giữa 2 ngày lớn hơn mức cho phép -> Cắt vụ
            if (ngay_ok[i] - ngay_ok[i-1]).days > GIATRI_GOC["GAP_NGAY"]:
                # Kiểm tra xem vụ này có đủ dài để công nhận không
                if (ngay_ok[i-1] - start).days + 1 >= GIATRI_GOC["MIN_VU"]:
                    danh_sach_vu.append((start, ngay_ok[i-1]))
                start = ngay_ok[i] # Dời mốc bắt đầu sang ngày mới
        danh_sach_vu.append((start, ngay_ok[-1])) # Vét máng vụ cuối cùng
        
    return danh_sach_vu

def tong_hop_du_lieu_ngay(tep_cham_phan, khu_vuc, v_hien_tai, thong_ke_ngay, thoi_gian_ngay):
    """Ghép dữ liệu Châm Phân vào Nhỏ Giọt, tạo thành Sổ Cái tổng hợp cho từng ngày"""
    data_cp_ngay = {}
    for tep in tep_cham_phan:
        tep.seek(0)
        for item in json.load(tep):
            if str(item.get('STT')) != khu_vuc: continue
            dt = datetime.strptime(item['Thời gian'], "%Y-%m-%d %H-%M-%S")
            
            # Chỉ lấy dữ liệu nằm trong Mùa Vụ đang chọn
            if v_hien_tai[0] <= dt.date() <= v_hien_tai[1]:
                n_str = dt.strftime("%Y-%m-%d")
                if n_str not in data_cp_ngay: data_cp_ngay[n_str] = {'tbec': [], 'req': []}
                
                v1 = chuyen_doi_so_thuc(item, ['TBEC', 'tbec'])
                v2 = chuyen_doi_so_thuc(item, ['EC yêu cầu', 'ecreq'])
                if v1 is not None: data_cp_ngay[n_str]['tbec'].append(v1)
                if v2 is not None: data_cp_ngay[n_str]['req'].append(v2)

    du_lieu_tong_hop = {}
    ngay_vu = sorted([n for n in thong_ke_ngay 
                      if v_hien_tai[0] <= datetime.strptime(n, "%Y-%m-%d").date() <= v_hien_tai[1]])
    
    # Tính trung bình các chỉ số cho mỗi ngày
    for n in ngay_vu:
        raw_tbec = np.mean(data_cp_ngay[n]['tbec']) if n in data_cp_ngay and data_cp_ngay[n]['tbec'] else 0
        raw_req = np.mean(data_cp_ngay[n]['req']) if n in data_cp_ngay and data_cp_ngay[n]['req'] else 0
        phut_tuoi = int(round(thoi_gian_ngay.get(n, 0) / 60))
        
        du_lieu_tong_hop[n] = {
            'so_lan_tuoi': thong_ke_ngay[n],
            'thoi_gian_tuoi_phut': phut_tuoi,
            'tbec': float(f"{raw_tbec:.2f}"),
            'ecreq': float(f"{raw_req:.2f}")
        }
    return du_lieu_tong_hop, ngay_vu

def chia_giai_doan_bien_thien_dong_thoi(danh_sach_ngay, du_lieu_tong_hop, cau_hinh_nguong):
    """Dùng sai số biến thiên để chia nhỏ Mùa Vụ thành các Giai Đoạn sinh trưởng"""
    if not cau_hinh_nguong or not danh_sach_ngay: return [danh_sach_ngay]
    
    danh_sach_cac_gd = []
    nhom_hien_tai = [danh_sach_ngay[0]]
    
    for i in range(1, len(danh_sach_ngay)):
        ngay_dang_xet = danh_sach_ngay[i]
        ngay_truoc_do = nhom_hien_tai[-1] # Lấy ngày cuối cùng của Giai đoạn hiện tại làm mốc
        ket_qua_kiem_tra = []
        
        # Kiểm tra từng chỉ số được cấu hình
        for khoa_chi_so, nguong_sai_so in cau_hinh_nguong.items():
            v_now = du_lieu_tong_hop[ngay_dang_xet].get(khoa_chi_so)
            v_prev = du_lieu_tong_hop[ngay_truoc_do].get(khoa_chi_so)
            
            if v_now is not None and v_prev is not None:
                # Nếu độ chênh lệch >= sai số -> Ghi nhận biến thiên
                if abs(v_now - v_prev) >= nguong_sai_so:
                    ket_qua_kiem_tra.append(True)
                    
        # Nếu tất cả các chỉ số yêu cầu đều bị biến thiên -> Ngắt giai đoạn
        if len(ket_qua_kiem_tra) == len(cau_hinh_nguong) and all(ket_qua_kiem_tra):
            danh_sach_cac_gd.append(nhom_hien_tai)
            nhom_hien_tai = [ngay_dang_xet]
        else:
            nhom_hien_tai.append(ngay_dang_xet) # Chưa đủ biến thiên -> Nối tiếp giai đoạn cũ
            
    danh_sach_cac_gd.append(nhom_hien_tai)
    return danh_sach_cac_gd


# =====================================================================
# PHẦN 3: LÕI VẼ BIỂU ĐỒ (TRẠM TRANG TRÍ MÓN ĂN)
# =====================================================================
"""
Vai trò cốt lõi: Chuyên gia hội họa. Biến con số thành hình ảnh trực quan.
Nhiệm vụ: Nhận dữ liệu "đã chín", dùng matplotlib để vẽ đồ thị, kẻ vạch phân cách.
Nguyên tắc: Họa sĩ chỉ vẽ theo đúng dữ liệu được giao, KHÔNG tự ý tính toán 
hay sửa đổi số liệu ở đây.
"""

def ve_bieu_do_dong_thoi(du_lieu_tong_hop, danh_sach_gd, chi_so_chon):
    # Khởi tạo khung tranh (nếu người dùng chưa chọn gì thì báo lỗi nhẹ nhàng)
    if not chi_so_chon or not danh_sach_gd:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.text(0.5, 0.5, 'Chưa có chỉ số nào được chọn để vẽ', ha='center', va='center')
        return fig

    so_tang = len(chi_so_chon)
    # Tạo các tầng biểu đồ dựa trên số lượng chỉ số được tick
    fig, axes = plt.subplots(so_tang, 1, figsize=(12, 4 * so_tang), sharex=True)
    if so_tang == 1: axes = [axes] # Đảm bảo luôn là list để code lặp không bị lỗi
    
    # Gom tất cả các ngày vào 1 trục X liên tục
    truc_x = []
    for gd in danh_sach_gd: truc_x.extend(gd)
    
    # Từ điển dịch tên hiển thị sang tên biến (Key) trong Sổ Cái
    map_key = {"Lần tưới": "so_lan_tuoi", "TBEC": "tbec", "EC Yêu cầu": "ecreq"}
    
    for i, chi_so in enumerate(chi_so_chon):
        ax = axes[i]
        key_du_lieu = map_key[chi_so]
        truc_y = [du_lieu_tong_hop[ngay][key_du_lieu] for ngay in truc_x]
        
        # Vẽ cột
        ax.bar(truc_x, truc_y, color='skyblue', edgecolor='black')
        ax.set_ylabel(chi_so, fontsize=12)
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Vẽ các đường ranh giới đỏ (Nhát cắt giai đoạn)
        if len(danh_sach_gd) > 1:
            for gd in danh_sach_gd[:-1]: # Bỏ qua giai đoạn cuối cùng vì không cần cắt đuôi
                ngay_cuoi_gd = gd[-1]
                ax.axvline(x=ngay_cuoi_gd, color='red', linestyle='--', linewidth=2)
                
    # Xoay chữ ở trục X 45 độ cho đỡ bị đè lên nhau
    plt.xticks(rotation=45, ha='right')
    fig.tight_layout()
    return fig


# =====================================================================
# PHẦN 4: GIAO DIỆN NGƯỜI DÙNG (SÂN KHẤU VÀ BỒI BÀN)
# =====================================================================
"""
Vai trò cốt lõi: Nơi giao tiếp với người dùng và điều phối kịch bản chính.
Nhiệm vụ: 
- Vẽ giao diện (Sidebar, Button, Text...).
- Lấy input từ người dùng -> Truyền cho Phần 2 (Bếp) -> Truyền cho Phần 3 (Họa sĩ).
- Hiển thị kết quả ra màn hình.
"""

def main():
    st.set_page_config(page_title="Phân Tích Dữ Liệu", layout="wide")
    st.title("📊 Bảng Điều Khiển Phân Tích Tưới Tiêu")
    
    # ---------------------------------------------------------
    # GIAO DIỆN SIDEBAR: CẤU HÌNH ĐẦU VÀO
    # ---------------------------------------------------------
    with st.sidebar:
        st.header("📂 1. Tải Dữ Liệu")
        tep_nho_giot = st.file_uploader("Upload file Nhỏ giọt (JSON)", accept_multiple_files=True, type=['json'])
        tep_cham_phan = st.file_uploader("Upload file Châm phân (JSON)", accept_multiple_files=True, type=['json'])
        
        khu_vuc = st.selectbox("Chọn khu vực", ["1", "2", "3", "4"])
        
        st.header("⚙️ 2. Cấu Hình Cắt Giai Đoạn")
        st.caption("Tick chọn chỉ số và nhập sai số muốn ngắt:")
        
        col1, col2 = st.columns([1, 1])
        with col1: tick_lan = st.checkbox("Lần tưới")
        with col2: ss_lan = st.number_input("Sai số Lần", value=st.session_state.ss_lan_key, step=0.5)
        
        col3, col4 = st.columns([1, 1])
        with col3: tick_tbec = st.checkbox("TBEC")
        with col4: ss_tbec = st.number_input("Sai số TBEC", value=st.session_state.ss_tbec_key, step=0.1)
        
        col5, col6 = st.columns([1, 1])
        with col5: tick_req = st.checkbox("EC Y/C")
        with col6: ss_req = st.number_input("Sai số Req", value=st.session_state.ss_req_key, step=0.1)

    # ---------------------------------------------------------
    # LUỒNG THỰC THI CHÍNH (Chỉ chạy khi người dùng đã up đủ 2 file)
    # ---------------------------------------------------------
    if tep_nho_giot and tep_cham_phan:
        
        # BƯỚC A & B: Giao cho Đầu bếp xử lý file và tìm mùa vụ
        thong_ke_ngay, thoi_gian_ngay = xu_ly_file_nho_giot(tep_nho_giot, khu_vuc)
        danh_sach_vu = tim_kiem_mua_vu(thong_ke_ngay)
        
        if not danh_sach_vu:
            st.warning("Không tìm thấy mùa vụ nào hợp lệ (Ít nhất 7 ngày, mỗi ngày tưới > 5 lần).")
            return
            
        # Hiển thị UI chọn Vụ mùa (Bắt buộc phải chọn vụ trước khi phân tích)
        chuoi_vu = [f"Vụ {i+1}: {v[0].strftime('%d/%m/%Y')} - {v[1].strftime('%d/%m/%Y')}" 
                    for i, v in enumerate(danh_sach_vu)]
        lua_chon_vu = st.selectbox("🌾 3. Chọn Mùa Vụ Để Phân Tích", range(len(danh_sach_vu)), format_func=lambda x: chuoi_vu[x])
        v_hien_tai = danh_sach_vu[lua_chon_vu]
        
        # BƯỚC C: Gom dữ liệu tạo Sổ Cái theo mùa vụ đã chọn
        du_lieu_tong_hop, danh_sach_ngay = tong_hop_du_lieu_ngay(
            tep_cham_phan, khu_vuc, v_hien_tai, thong_ke_ngay, thoi_gian_ngay)
            
        if not du_lieu_tong_hop:
            st.warning("Không có dữ liệu châm phân cho mùa vụ này.")
            return

        # BƯỚC D: Lấy cấu hình sai số từ UI và chạy thuật toán cắt giai đoạn
        nguong_ngat = {}
        chi_so_duoc_chon = [] # Danh sách gửi cho Họa sĩ để biết đường vẽ
        if tick_lan: 
            nguong_ngat['so_lan_tuoi'] = ss_lan
            chi_so_duoc_chon.append("Lần tưới")
        if tick_tbec: 
            nguong_ngat['tbec'] = ss_tbec
            chi_so_duoc_chon.append("TBEC")
        if tick_req: 
            nguong_ngat['ecreq'] = ss_req
            chi_so_duoc_chon.append("EC Yêu cầu")
            
        # Gọi Đầu bếp chạy thuật toán cắt
        ds_giai_doan = chia_giai_doan_bien_thien_dong_thoi(danh_sach_ngay, du_lieu_tong_hop, nguong_ngat)
        
        # In tổng kết nhanh
        st.success(f"✅ Hệ thống đã phân tích và cắt thành **{len(ds_giai_doan)} giai đoạn** dựa trên các sai số bạn chọn.")

        # BƯỚC E: Giao cho Họa sĩ vẽ và hiển thị Biểu đồ
        st.subheader("📈 Biểu Đồ Trực Quan")
        fig = ve_bieu_do_dong_thoi(du_lieu_tong_hop, ds_giai_doan, chi_so_duoc_chon)
        st.pyplot(fig)
        
        # BƯỚC F: Sắp xếp dữ liệu thành Dạng Bảng (List of Dicts) để hiển thị
        st.subheader("📋 Bảng Dữ Liệu Chi Tiết")
        bang_hien_thi = []
        for gd_idx, gd_ngay in enumerate(ds_giai_doan):
            for ngay in gd_ngay:
                bang_hien_thi.append({
                    "Giai đoạn": f"Giai đoạn {gd_idx + 1}",
                    "Ngày": ngay,
                    "Lần tưới": du_lieu_tong_hop[ngay]['so_lan_tuoi'],
                    "Phút tưới": du_lieu_tong_hop[ngay]['thoi_gian_tuoi_phut'],
                    "TBEC": du_lieu_tong_hop[ngay]['tbec'],
                    "EC Req": du_lieu_tong_hop[ngay]['ecreq']
                })
        
        # Streamlit tự động nhận diện List of Dicts và vẽ bảng luôn, không cần Pandas!
        st.dataframe(bang_hien_thi, use_container_width=True)

    else:
        # Nếu chưa up file thì hiện thông báo chờ
        st.info("👈 Vui lòng tải lên file dữ liệu Nhỏ Giọt và Châm Phân ở thanh bên trái để bắt đầu.")

# Lệnh mồi khởi chạy ứng dụng Streamlit
if __name__ == "__main__":
    main()
