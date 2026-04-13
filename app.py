import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, date, timedelta

# =================================================================
# KHUNG 1: CẤU HÌNH GỐC
# =================================================================
GIATRI_GOC = {
    "LAN_TUOI": 2.5, "TBEC": 8.0, "EC_REQ": 5.0,
    "GIAY_MIN": 20, "GIAY_MAX": 3600, "LAN_MIN_NGAY": 5,
    "GAP_NGAY": 2, "MIN_VU": 7
}

st.set_page_config(page_title="Phân tích Đa chỉ số", layout="wide")

# =================================================================
# KHUNG 2: BỘ NÃO TÍNH TOÁN (Logic Đa chỉ số)
# =================================================================
def chuyen_doi_so_thuc(du_lieu, danh_sach_khoa):
    for khoa in danh_sach_khoa:
        gia_tri = du_lieu.get(khoa)
        if gia_tri is not None:
            try: return float(str(gia_tri).replace(',', '.'))
            except: continue
    return None

def xac_dinh_vi_tri_vu(ngay_dang_xet_str, danh_sach_vu):
    ngay_dt = datetime.strptime(ngay_dang_xet_str, "%Y-%m-%d").date()
    for i, (start, end) in enumerate(danh_sach_vu):
        if start <= ngay_dt <= end:
            return f"Vụ {i+1}", (ngay_dt - start).days + 1
    return "Ngoài vụ", "-"

def chia_giai_doan_da_chi_so(danh_sach_ngay, du_lieu_tong_hop, cac_chi_so_chon, sai_so_dict):
    """
    Logic: Chỉ ngắt giai đoạn khi TẤT CẢ chỉ số trong danh sách chọn đều vượt ngưỡng sai số.
    """
    danh_sach_cac_gd = []
    if not danh_sach_ngay or not cac_chi_so_chon: return []
    
    nhom_hien_tai = [danh_sach_ngay[0]]
    
    for i in range(1, len(danh_sach_ngay)):
        ngay_dang_xet = danh_sach_ngay[i]
        
        # Kiểm tra sự biến động của từng chỉ số
        ket_qua_kiem_tra = []
        for cs in cac_chi_so_chon:
            gia_tri_ngay = du_lieu_tong_hop[ngay_dang_xet][cs]
            # Tính trung bình nhóm hiện tại của chỉ số đó
            trung_binh_nhom = np.mean([du_lieu_tong_hop[d][cs] for d in nhom_hien_tai])
            
            # Nếu vượt sai số thì đánh dấu là True
            if abs(gia_tri_ngay - trung_binh_nhom) > sai_so_dict[cs]:
                ket_qua_kiem_tra.append(True)
            else:
                ket_qua_kiem_tra.append(False)
        
        # QUAN TRỌNG: Chỉ ngắt khi TOÀN BỘ ket_qua_kiem_tra đều là True (Logic AND)
        if all(ket_qua_kiem_tra) and len(ket_qua_kiem_tra) > 0:
            danh_sach_cac_gd.append(nhom_hien_tai)
            nhom_hien_tai = [ngay_dang_xet]
        else:
            nhom_hien_tai.append(ngay_dang_xet)
            
    danh_sach_cac_gd.append(nhom_hien_tai)
    return danh_sach_cac_gd

# =================================================================
# KHUNG 4: LUỒNG XỬ LÝ CHÍNH
# =================================================================
with st.sidebar:
    st.header("📂 Nguồn dữ liệu")
    tep_nho_giot = st.file_uploader("File Nhỏ giọt", type=['json'], accept_multiple_files=True)
    tep_cham_phan = st.file_uploader("File Châm phân", type=['json'], accept_multiple_files=True)
    
    st.divider()
    st.header("🔍 Tiêu chí phân vụ")
    st.info("Mùa vụ sẽ được chia khi các chỉ số được chọn dưới đây CÙNG THAY ĐỔI.")
    dung_lan_tuoi = st.checkbox("Sử dụng Lần tưới", value=True)
    dung_tbec = st.checkbox("Sử dụng TBEC", value=False)
    dung_ecreq = st.checkbox("Sử dụng EC Req", value=False)
    
    with st.expander("⚙️ Cấu hình sai số"):
        ss_lan = st.number_input("Sai số Lần tưới", value=GIATRI_GOC["LAN_TUOI"])
        ss_tbec = st.number_input("Sai số TBEC", value=GIATRI_GOC["TBEC"])
        ss_ecreq = st.number_input("Sai số EC Req", value=GIATRI_GOC["EC_REQ"])

if tep_nho_giot:
    # 1. Xử lý dữ liệu Nhỏ giọt (Lần tưới)
    du_lieu_tho_ng = []
    for t in tep_nho_giot: du_lieu_tho_ng.extend(json.load(t))
    stt_list = sorted(list(set(str(d.get('STT')) for d in du_lieu_tho_ng if d.get('STT'))))
    khu_vuc = st.selectbox("Chọn Khu vực", stt_list)
    
    # Gom dữ liệu lần tưới theo ngày
    thong_ke_ng = {}
    data_kv = sorted([d for d in du_lieu_tho_ng if str(d.get('STT')) == khu_vuc], key=lambda x: x['Thời gian'])
    for i in range(len(data_kv)-1):
        if data_kv[i].get('Trạng thái') == "Bật" and data_kv[i+1].get('Trạng thái') == "Tắt":
            t1 = datetime.strptime(data_kv[i]['Thời gian'], "%Y-%m-%d %H-%M-%S")
            d_str = t1.strftime("%Y-%m-%d")
            thong_ke_ng[d_str] = thong_ke_ng.get(d_str, 0) + 1

    # 2. Xử lý dữ liệu Châm phân (TBEC & EC Req)
    thong_ke_cp = {}
    if tep_cham_phan:
        du_lieu_tho_cp = []
        for t in tep_cham_phan: du_lieu_tho_cp.extend(json.load(t))
        for item in du_lieu_tho_cp:
            if str(item.get('STT')) == khu_vuc:
                d_str = item['Thời gian'][:10].replace('-', '-') # Lấy YYYY-MM-DD
                if d_str not in thong_ke_cp: thong_ke_cp[d_str] = {'tbec': [], 'ecreq': []}
                vt = chuyen_doi_so_thuc(item, ['TBEC', 'tbec'])
                vr = chuyen_doi_so_thuc(item, ['EC yêu cầu', 'ecreq'])
                if vt: thong_ke_cp[d_str]['tbec'].append(vt)
                if vr: thong_ke_cp[d_str]['ecreq'].append(vr)

    # 3. Hợp nhất dữ liệu để phân tích đa chiều
    ngay_chung = sorted(list(set(thong_ke_ng.keys()) | set(thong_ke_cp.keys())))
    du_lieu_tong_hop = {}
    for n in ngay_chung:
        du_lieu_tong_hop[n] = {
            'lan_tuoi': thong_ke_ng.get(n, 0),
            'tbec': np.mean(thong_ke_cp[n]['tbec']) if n in thong_ke_cp and thong_ke_cp[n]['tbec'] else 0,
            'ecreq': np.mean(thong_ke_cp[n]['ecreq']) if n in thong_ke_cp and thong_ke_cp[n]['ecreq'] else 0
        }

    # 4. Thực hiện chia giai đoạn theo lựa chọn
    cac_chi_so_chon = []
    if dung_lan_tuoi: cac_chi_so_chon.append('lan_tuoi')
    if dung_tbec: cac_chi_so_chon.append('tbec')
    if dung_ecreq: cac_chi_so_chon.append('ecreq')
    
    sai_so_dict = {'lan_tuoi': ss_lan, 'tbec': ss_tbec, 'ecreq': ss_ecreq}
    
    if cac_chi_so_chon:
        ds_giai_doan = chia_giai_doan_da_chi_so(ngay_chung, du_lieu_tong_hop, cac_chi_so_chon, sai_so_dict)
        
        st.subheader(f"📊 Kết quả chia giai đoạn (Dựa trên {', '.join(cac_chi_so_chon)})")
        st.write(f"Tìm thấy **{len(ds_giai_doan)}** giai đoạn đồng thuận.")
        
        # Hiển thị bảng tóm tắt
        hien_thi = []
        for i, gd in enumerate(ds_giai_doan):
            hien_thi.append({
                "Giai đoạn": i + 1,
                "Từ ngày": gd[0],
                "Đến ngày": gd[-1],
                "Số ngày": len(gd),
                "Lần tưới TB": round(np.mean([du_lieu_tong_hop[d]['lan_tuoi'] for d in gd]), 1),
                "TBEC TB": round(np.mean([du_lieu_tong_hop[d]['tbec'] for d in gd]), 2)
            })
        st.table(hien_thi)
    else:
        st.warning("Vui lòng chọn ít nhất một chỉ số để phân tích.")
