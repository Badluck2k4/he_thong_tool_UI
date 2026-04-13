# =====================================================================
# PHẦN 1: KHAI BÁO THƯ VIỆN & CẤU HÌNH BAN ĐẦU
# =====================================================================
import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Định nghĩa các hằng số mặc định ban đầu để sử dụng trong toàn bộ chương trình
GIATRI_GOC = {
    "LAN_TUOI": 1.0,  # Sai số Lần tưới mặc định
    "TBEC": 4.0,      # Sai số TBEC mặc định
    "EC_REQ": 2.0,    # Sai số EC Yêu cầu mặc định
    "GIAY_MIN": 20,   # Thời gian 1 lần tưới tối thiểu (giây) để được tính là hợp lệ
    "GIAY_MAX": 3600, # Thời gian 1 lần tưới tối đa (giây)
    "LAN_MIN_NGAY": 5,# Số lần tưới tối thiểu trong 1 ngày để ngày đó được tính vào mùa vụ
    "GAP_NGAY": 2,    # Khoảng cách tối đa (số ngày) giữa 2 ngày tưới để gộp chung 1 vụ
    "MIN_VU": 7       # Số ngày tối thiểu để hình thành 1 mùa vụ hợp lệ
}

# Cấu hình giao diện trang web Streamlit (tiêu đề, chế độ hiển thị rộng)
st.set_page_config(page_title="Phân tích Mùa vụ Đa biến v5.9", layout="wide")


# =====================================================================
# PHẦN 2: QUẢN LÝ TRẠNG THÁI (SESSION STATE) CHO NÚT RESET
# =====================================================================
# Kiểm tra và khởi tạo các biến lưu trữ trạng thái nếu chúng chưa tồn tại.
# Việc này giúp Streamlit nhớ được giá trị sai số hiện tại khi trang load lại.
if 'ss_lan_key' not in st.session_state:
    st.session_state['ss_lan_key'] = GIATRI_GOC["LAN_TUOI"]
if 'ss_tbec_key' not in st.session_state:
    st.session_state['ss_tbec_key'] = GIATRI_GOC["TBEC"]
if 'ss_req_key' not in st.session_state:
    st.session_state['ss_req_key'] = GIATRI_GOC["EC_REQ"]

# Hàm callback: Được gọi khi người dùng bấm nút "Đặt lại mặc định"
def phuc_hoi_sai_so_mac_dinh():
    st.session_state['ss_lan_key'] = GIATRI_GOC["LAN_TUOI"]
    st.session_state['ss_tbec_key'] = GIATRI_GOC["TBEC"]
    st.session_state['ss_req_key'] = GIATRI_GOC["EC_REQ"]


# =====================================================================
# PHẦN 3: CÁC HÀM XỬ LÝ LÕI (THUẬT TOÁN)
# =====================================================================

# Hàm trích xuất và chuyển đổi số liệu từ JSON thành số thực (float) an toàn
def chuyen_doi_so_thuc(du_lieu, danh_sach_khoa):
    for khoa in danh_sach_khoa:
        gia_tri = du_lieu.get(khoa)
        if gia_tri is not None:
            try:
                # Đề phòng trường hợp dấu phẩy (,) được dùng thay cho dấu chấm (.)
                return float(str(gia_tri).replace(',', '.'))
            except (ValueError, TypeError):
                continue
    return None

# Hàm thuật toán cốt lõi: Chia giai đoạn dựa trên sự biến thiên của các chỉ số
def chia_giai_doan_bien_thien_dong_thoi(danh_sach_ngay, du_lieu_tong_hop, cau_hinh_nguong):
    danh_sach_cac_gd = []
    if not danh_sach_ngay: return danh_sach_cac_gd
    # Nếu không chọn chỉ số nào để làm ngưỡng, coi tất cả chung 1 giai đoạn
    if not cau_hinh_nguong: return [danh_sach_ngay]

    # Khởi tạo giai đoạn đầu tiên với ngày bắt đầu
    nhom_hien_tai = [danh_sach_ngay[0]]
    
    # Duyệt qua từng ngày (từ ngày thứ 2 trở đi) để so sánh với ngày cuối cùng của giai đoạn trước
    for i in range(1, len(danh_sach_ngay)):
        ngay_dang_xet = danh_sach_ngay[i]
        ngay_truoc_do = nhom_hien_tai[-1]  
        ket_qua_kiem_tra = []
        
        # Duyệt qua các chỉ số (Lần tưới, TBEC, Req) mà người dùng đang tick chọn
        for khoa_chi_so, nguong_sai_so in cau_hinh_nguong.items():
            v_now = du_lieu_tong_hop[ngay_dang_xet].get(khoa_chi_so)
            v_prev = du_lieu_tong_hop[ngay_truoc_do].get(khoa_chi_so)
            
            if v_now is not None and v_prev is not None:
                # Tính độ chênh lệch tuyệt đối. Nếu >= sai số cấu hình thì ghi nhận là True (có biến thiên)
                if abs(v_now - v_prev) >= nguong_sai_so:
                    ket_qua_kiem_tra.append(True)
        
        # Nếu TẤT CẢ các chỉ số được chọn đều có sự biến thiên vượt ngưỡng
        if len(ket_qua_kiem_tra) == len(cau_hinh_nguong) and all(ket_qua_kiem_tra):
            # Cắt giai đoạn hiện tại, lưu vào danh sách
            danh_sach_cac_gd.append(nhom_hien_tai)
            # Mở một giai đoạn mới bắt đầu bằng ngày đang xét
            nhom_hien_tai = [ngay_dang_xet]
        else:
            # Nếu không đủ điều kiện ngắt, tiếp tục thêm ngày này vào giai đoạn hiện tại
            nhom_hien_tai.append(ngay_dang_xet)
            
    # Đưa giai đoạn cuối cùng vào danh sách sau khi vòng lặp kết thúc
    danh_sach_cac_gd.append(nhom_hien_tai)
    return danh_sach_cac_gd


# =====================================================================
# PHẦN 4: HÀM VẼ BIỂU ĐỒ TRỰC QUAN (MATPLOTLIB)
# =====================================================================
def ve_bieu_do_dong_thoi(du_lieu_tong_hop, danh_sach_gd, chi_so_chon):
    # Sắp xếp ngày để vẽ trục X
    ngay_co_so = sorted(du_lieu_tong_hop.keys())
    if not ngay_co_so or not chi_so_chon: return

    x_labels = list(range(1, len(ngay_co_so) + 1))
    
    # Ánh xạ tên chỉ số với dữ liệu tương ứng trong dictionary
    map_data = {
        "Lần tưới": ([du_lieu_tong_hop[n]['so_lan_tuoi'] for n in ngay_co_so], "Lần tưới (Lần)"),
        "TBEC": ([du_lieu_tong_hop[n]['tbec'] for n in ngay_co_so], "TBEC"),
        "EC Yêu cầu": ([du_lieu_tong_hop[n]['ecreq'] for n in ngay_co_so], "EC Yêu cầu")
    }

    # Cấu hình màu sắc để phân biệt các giai đoạn khác nhau trên biểu đồ
    bang_mau = ['#2E7D32', '#1565C0', '#C62828', '#AD1457', '#6A1B9A', '#00838F', '#283593']
    mau_cot = []
    ranh_gioi_gd = [] # Lưu vị trí các đường gạch đứt đỏ phân chia giai đoạn
    
    # Xác định màu cho từng cột và vị trí vẽ đường phân ranh giới
    for i, ngay in enumerate(ngay_co_so):
        for idx, gd in enumerate(danh_sach_gd):
            if ngay in gd:
                mau_cot.append(bang_mau[idx % len(bang_mau)]) # Lặp lại màu nếu quá nhiều giai đoạn
                # Nếu là ngày đầu tiên của một giai đoạn (trừ gd đầu), đánh dấu ranh giới
                if ngay == gd[0] and idx > 0: ranh_gioi_gd.append(i + 1)
                break

    so_luong_tang = len(chi_so_chon)
    
    # Tạo khung hình biểu đồ (figure) với số tầng phụ thuộc vào số chỉ số được tick
    fig, axes = plt.subplots(so_luong_tang, 1, figsize=(20, 7 * so_luong_tang), sharex=True)
    if so_luong_tang == 1: axes = [axes] # Xử lý lỗi mảng nếu chỉ có 1 tầng
        
    fig.suptitle(f"PHÂN TÍCH BIẾN THIÊN: {' - '.join(chi_so_chon).upper()}", 
                 fontsize=24, fontweight='bold', y=0.96)

    # Hàm nội bộ để vẽ từng tầng (subplot)
    def ve_tung_tang(ax, data, title, color_list):
        ax.bar(x_labels, data, color=color_list, alpha=0.85, edgecolor='black', linewidth=0.5)
        ax.set_ylabel(title, fontweight='bold', fontsize=16)
        
        # Vẽ các đường gạch đứt màu đỏ ngăn cách giai đoạn
        for rg in ranh_gioi_gd:
            ax.axvline(x=rg - 0.5, color='red', linestyle='--', alpha=0.8, linewidth=2)
        
        ax.grid(axis='y', linestyle=':', alpha=0.6)
        ax.tick_params(axis='y', labelsize=14)
        max_val = max(data) if data and max(data) > 0 else 1
        ax.set_ylim(0, max_val * 1.1) # Tạo khoảng trống phía trên cho đẹp

    # Vòng lặp gọi hàm vẽ cho từng chỉ số đã tick
    for idx, ten_chi_so in enumerate(chi_so_chon):
        data, title = map_data[ten_chi_so]
        ve_tung_tang(axes[idx], data, title, mau_cot)

    # Cấu hình trục X cho tầng cuối cùng
    axes[-1].set_xticks(x_labels)
    axes[-1].set_xticklabels(x_labels, fontsize=14, fontweight='bold')
    axes[-1].set_xlabel("SỐ THỨ TỰ NGÀY", fontweight='bold', fontsize=16, labelpad=15)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    st.pyplot(fig, use_container_width=True)


# =====================================================================
# PHẦN 5: XÂY DỰNG GIAO DIỆN THANH BÊN (SIDEBAR)
# =====================================================================
with st.sidebar:
    st.header("📂 Dữ liệu & Cấu hình")
    # Khu vực tải file
    tep_nho_giot = st.file_uploader("Tải file Nhỏ giọt", type=['json'], accept_multiple_files=True)
    tep_cham_phan = st.file_uploader("Tải file Châm phân", type=['json'], accept_multiple_files=True)
    
    st.divider()
    st.subheader("📊 Chọn chỉ số hiển thị & phân tích")
    # Checkbox chọn chỉ số
    tick_lan = st.checkbox("Lần tưới", value=True)
    tick_tbec = st.checkbox("TBEC", value=True)
    tick_req = st.checkbox("EC Yêu cầu", value=True)
    
    # Tạo danh sách các chỉ số được chọn để truyền xuống phần xử lý
    chi_so_chon = []
    if tick_lan: chi_so_chon.append("Lần tưới")
    if tick_tbec: chi_so_chon.append("TBEC")
    if tick_req: chi_so_chon.append("EC Yêu cầu")

    st.divider()
    st.subheader("⚙️ Ngưỡng ngắt giai đoạn")
    
    # Nút reset gọi hàm phuc_hoi_sai_so_mac_dinh đã định nghĩa ở PHẦN 2
    st.button("🔄 Đặt lại mặc định", on_click=phuc_hoi_sai_so_mac_dinh, use_container_width=True)
    
    # Ô nhập liệu cấu hình sai số, liên kết trực tiếp với session_state thông qua 'key'
    ss_lan = st.number_input("Sai số Lần tưới", key="ss_lan_key", step=0.1)
    ss_tbec = st.number_input("Sai số TBEC", key="ss_tbec_key", step=0.1)
    ss_req = st.number_input("Sai số EC Req", key="ss_req_key", step=0.1)


# =====================================================================
# PHẦN 6: XỬ LÝ DỮ LIỆU NHỎ GIỌT VÀ TÌM MÙA VỤ
# =====================================================================
if tep_nho_giot:
    # 1. Gom dữ liệu từ các file Nhỏ giọt tải lên
    du_lieu_tho_ng = []
    for t in tep_nho_giot: du_lieu_tho_ng.extend(json.load(t))
    
    # Lọc danh sách các khu vực (STT) có trong file để đưa ra Selectbox
    stt_list = sorted(list(set(str(d.get('STT')) for d in du_lieu_tho_ng if d.get('STT'))))
    khu_vuc = st.sidebar.selectbox("🎯 Chọn khu vực", stt_list)

    thong_ke_ngay = {}  # Lưu số lần tưới theo ngày
    thoi_gian_ngay = {} # Lưu tổng thời gian tưới (giây) theo ngày
    
    # 2. Lọc dữ liệu theo khu vực đang chọn và sắp xếp theo thời gian
    data_kv = sorted([d for d in du_lieu_tho_ng if str(d.get('STT')) == khu_vuc], key=lambda x: x['Thời gian'])
    
    # 3. Quét qua dữ liệu để tìm các cặp Bật - Tắt tạo thành 1 lần tưới
    for i in range(len(data_kv)-1):
        if data_kv[i].get('Trạng thái') == "Bật" and data_kv[i+1].get('Trạng thái') == "Tắt":
            t1 = datetime.strptime(data_kv[i]['Thời gian'], "%Y-%m-%d %H-%M-%S")
            t2 = datetime.strptime(data_kv[i+1]['Thời gian'], "%Y-%m-%d %H-%M-%S")
            thoi_gian_tuoi = (t2 - t1).total_seconds()
            
            # Lọc nhiễu: Chỉ lấy những lần tưới nằm trong khoảng min-max cho phép
            if GIATRI_GOC["GIAY_MIN"] <= thoi_gian_tuoi <= GIATRI_GOC["GIAY_MAX"]:
                d_str = t1.strftime("%Y-%m-%d") # Lấy ra ngày tưới dạng YYYY-MM-DD
                thong_ke_ngay[d_str] = thong_ke_ngay.get(d_str, 0) + 1 # Cộng dồn số lần tưới
                thoi_gian_ngay[d_str] = thoi_gian_ngay.get(d_str, 0) + thoi_gian_tuoi # Cộng dồn giây tưới

    # 4. Tìm các ngày HỢP LỆ (có số lần tưới >= LAN_MIN_NGAY)
    ngay_ok = sorted([datetime.strptime(n, "%Y-%m-%d").date() for n, c in thong_ke_ngay.items() if c >= GIATRI_GOC["LAN_MIN_NGAY"]])
    
    if ngay_ok:
        danh_sach_vu = []
        start = ngay_ok[0]
        
        # 5. Phân chia mùa vụ dựa trên số ngày cách quãng
        for i in range(1, len(ngay_ok)):
            # Nếu 2 ngày cách nhau xa hơn GAP_NGAY, tiến hành cắt vụ
            if (ngay_ok[i] - ngay_ok[i-1]).days > GIATRI_GOC["GAP_NGAY"]:
                # Kiểm tra vụ đó có đủ thời gian tổi thiểu chưa (MIN_VU)
                if (ngay_ok[i-1] - start).days + 1 >= GIATRI_GOC["MIN_VU"]:
                    danh_sach_vu.append((start, ngay_ok[i-1]))
                start = ngay_ok[i] # Bắt đầu tính vụ tiếp theo
        
        # Đưa vụ cuối cùng vào danh sách
        danh_sach_vu.append((start, ngay_ok[-1]))

        # Khung chọn mùa vụ trên giao diện
        chon_vu = st.selectbox("📅 Chọn mùa vụ", [f"Vụ {i+1}: {v[0]} đến {v[1]}" for i, v in enumerate(danh_sach_vu)])
        v_hien_tai = danh_sach_vu[int(chon_vu.split(':')[0].split()[1])-1]


        # =====================================================================
        # PHẦN 7: XỬ LÝ DỮ LIỆU CHÂM PHÂN VÀ TỔNG HỢP VÀO TỪNG NGÀY
        # =====================================================================
        data_cp_ngay = {}
        if tep_cham_phan:
            for t in tep_cham_phan:
                for item in json.load(t):
                    if str(item.get('STT')) != khu_vuc: continue
                    dt = datetime.strptime(item['Thời gian'], "%Y-%m-%d %H-%M-%S")
                    
                    # Chỉ lấy dữ liệu châm phân nằm gọn trong mùa vụ đang chọn
                    if v_hien_tai[0] <= dt.date() <= v_hien_tai[1]:
                        n_str = dt.strftime("%Y-%m-%d")
                        if n_str not in data_cp_ngay: data_cp_ngay[n_str] = {'tbec': [], 'req': []}
                        
                        v1 = chuyen_doi_so_thuc(item, ['TBEC', 'tbec'])
                        v2 = chuyen_doi_so_thuc(item, ['EC yêu cầu', 'ecreq'])
                        if v1 is not None: data_cp_ngay[n_str]['tbec'].append(v1)
                        if v2 is not None: data_cp_ngay[n_str]['req'].append(v2)

        du_lieu_tong_hop = {}
        # Lấy các ngày thực sự nằm trong vụ để ráp dữ liệu
        ngay_vu = sorted([n for n in thong_ke_ngay if v_hien_tai[0] <= datetime.strptime(n, "%Y-%m-%d").date() <= v_hien_tai[1]])
        
        for n in ngay_vu:
            # Tính trung bình cộng TBEC và Req cho ngày đó
            raw_tbec = np.mean(data_cp_ngay[n]['tbec']) if n in data_cp_ngay and data_cp_ngay[n]['tbec'] else 0
            raw_req = np.mean(data_cp_ngay[n]['req']) if n in data_cp_ngay and data_cp_ngay[n]['req'] else 0
            
            # Làm tròn thời gian tưới ra số nguyên (phút)
            phut_tuoi = int(round(thoi_gian_ngay.get(n, 0) / 60))
            
            # Đóng gói tất cả thông tin lại vào 1 biến duy nhất cho ngày đó
            du_lieu_tong_hop[n] = {
                'so_lan_tuoi': thong_ke_ngay[n],
                'thoi_gian_tuoi_phut': phut_tuoi, 
                'tbec': float(f"{raw_tbec:.2f}"),
                'ecreq': float(f"{raw_req:.2f}")
            }

        # =====================================================================
        # PHẦN 8: KIỂM TRA ĐIỀU KIỆN, GỌI THUẬT TOÁN VÀ HIỂN THỊ KẾT QUẢ
        # =====================================================================
        if not chi_so_chon:
            st.warning("⚠️ Hãy chọn ít nhất một chỉ số để hiển thị biểu đồ.")
        else:
            # LINH HOẠT LẤY NGƯỠNG: Chỉ nhặt ra sai số của những chỉ số đang được tick
            nguong_ngat_thuc_te = {}
            if "Lần tưới" in chi_so_chon:
                nguong_ngat_thuc_te['so_lan_tuoi'] = ss_lan
            if "TBEC" in chi_so_chon:
                nguong_ngat_thuc_te['tbec'] = ss_tbec
            if "EC Yêu cầu" in chi_so_chon:
                nguong_ngat_thuc_te['ecreq'] = ss_req

            # Đưa vào hàm tính toán giai đoạn
            ds_giai_doan = chia_giai_doan_bien_thien_dong_thoi(ngay_vu, du_lieu_tong_hop, nguong_ngat_thuc_te)

            st.write(f"### Phân tích: {len(ds_giai_doan)} giai đoạn")
            
            # Vẽ biểu đồ
            ve_bieu_do_dong_thoi(du_lieu_tong_hop, ds_giai_doan, chi_so_chon)

            st.divider()
            st.write("### Bảng chi tiết")
            
            # Tạo bảng hiển thị dữ liệu chi tiết
            bang_hien_thi = []
            dem = 1
            for i, gd in enumerate(ds_giai_doan):
                for n in gd:
                    bang_hien_thi.append({
                        "STT Ngày": dem, 
                        "Giai đoạn": i + 1, 
                        "Ngày": n,
                        "Lần tưới": int(du_lieu_tong_hop[n]['so_lan_tuoi']),
                        "Thời gian tưới (Phút)": du_lieu_tong_hop[n]['thoi_gian_tuoi_phut'],
                        "TBEC": f"{du_lieu_tong_hop[n]['tbec']:.2f}",
                        "EC Yêu cầu": f"{du_lieu_tong_hop[n]['ecreq']:.2f}"
                    })
                    dem += 1
            st.table(bang_hien_thi)
else:
    # Thông báo khi chưa tải dữ liệu
    st.info("👋 Vui lòng tải dữ liệu.")
