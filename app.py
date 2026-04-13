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

st.set_page_config(page_title="Phân tích Đa chỉ số Mùa vụ", layout="wide")

# =================================================================
# KHUNG 2: BỘ NÃO TÍNH TOÁN
# =================================================================
def chuyen_doi_so_thuc(du_lieu, danh_sach_khoa):
    for khoa in danh_sach_khoa:
        gia_tri = du_lieu.get(khoa)
        if gia_tri is not None:
            try: return float(str(gia_tri).replace(',', '.'))
            except: continue
    return None

def chia_giai_doan_dong_thuan(danh_sach_ngay, du_lieu_tong, cac_chi_so_chon, sai_so_dict):
    """
    Logic AND: Chỉ ngắt giai đoạn khi TẤT CẢ chỉ số được chọn cùng vượt ngưỡng sai số.
    """
    danh_sach_cac_gd = []
    if not danh_sach_ngay or not cac_chi_so_chon: return []
    
    nhom_hien_tai = [danh_sach_ngay[0]]
    
    for i in range(1, len(danh_sach_ngay)):
        ngay_dang_xet = danh_sach_ngay[i]
        kiem_tra_ngat = []
        
        for cs in cac_chi_so_chon:
            gia_tri_ngay = du_lieu_tong[ngay_dang_xet][cs]
            trung_binh_nhom = np.mean([du_lieu_tong[d][cs] for d in nhom_hien_tai])
            
            if abs(gia_tri_ngay - trung_binh_nhom) > sai_so_dict[cs]:
                kiem_tra_ngat.append(True)
            else:
                kiem_tra_ngat.append(False)
        
        # Logic AND tuyệt đối
        if all(kiem_tra_ngat):
            danh_sach_cac_gd.append(nhom_hien_tai)
            nhom_hien_tai = [ngay_dang_xet]
        else:
            nhom_hien_tai.append(ngay_dang_xet)
            
    danh_sach_cac_gd.append(nhom_hien_tai)
    return danh_sach_cac_gd

# =================================================================
# KHUNG 3: TRỰC QUAN HÓA (BIỂU ĐỒ HƯỚNG GIAI ĐOẠN)
# =================================================================
def ve_bieu_do_huong_giai_doan(du_lieu_tong, ds_gd, cac_chi_so_chon):
    ngay_list = sorted(du_lieu_tong.keys())
    x = range(len(ngay_list))
    
    colors = {'lan_tuoi': '#1f77b4', 'tbec': '#ff7f0e', 'ecreq': '#2ca02c'}
    labels = {'lan_tuoi': 'Lần tưới', 'tbec': 'TBEC', 'ecreq': 'EC Req'}

    fig, ax1 = plt.subplots(figsize=(15, 6))
    ax2 = ax1.twinx() 
    
    co_ve_truc_2 = False

    for cs in cac_chi_so_chon:
        gia_tri_step = []
        for gd in ds_gd:
            avg_val = np.mean([du_lieu_tong[d][cs] for d in gd])
            gia_tri_step.extend([avg_val] * len(gd))
        
        if cs == 'lan_tuoi':
            ax1.step(x, gia_tri_step, where='post', label=labels[cs], color=colors[cs], lw=3)
            ax1.set_ylabel('Số lần tưới', color=colors[cs], fontsize=12, fontweight='bold')
        else:
            ax2.step(x, gia_tri_step, where='post', label=labels[cs], color=colors[cs], lw=2, ls='--')
            co_ve_truc_2 = True

    if co_ve_truc_2:
        ax2.set_ylabel('Chỉ số EC (mS/cm)', color='#333', fontsize=12, fontweight='bold')

    # Vẽ vạch đỏ chia giai đoạn
    pos = 0
    for gd in ds_gd[:-1]:
        pos += len(gd)
        ax1.axvline(x=pos - 0.5, color='red', linestyle=':', alpha=0.6)

    ax1.set_xticks(x)
    ax1.set_xticklabels([n[-5:] for n in ngay_list], rotation=45)
    ax1.set_title("XU HƯỚNG GIAI ĐOẠN DỰA TRÊN ĐỒNG THUẬN CHỈ SỐ", fontweight='bold')
    
    # Gộp Legend
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='upper left')
    
    plt.grid(axis='y', alpha=0.3)
    st.pyplot(fig)

# =================================================================
# KHUNG 4: LUỒNG XỬ LÝ CHÍNH
# =================================================================
with st.sidebar:
    st.header("📂 Nguồn dữ liệu")
    tep_ng = st.file_uploader("File Nhỏ giọt", type=['json'], accept_multiple_files=True)
    tep_cp = st.file_uploader("File Châm phân", type=['json'], accept_multiple_files=True)
    
    st.divider()
    st.header("🔍 Tiêu chí đồng thuận")
    d_lan = st.checkbox("Lần tưới", value=True)
    d_tbec = st.checkbox("TBEC", value=True)
    d_ecreq = st.checkbox("EC Req", value=False)
    
    with st.expander("⚙️ Cấu hình sai số"):
        ss_lan = st.number_input("Sai số Lần tưới", value=GIATRI_GOC["LAN_TUOI"])
        ss_tbec = st.number_input("Sai số TBEC", value=GIATRI_GOC["TBEC"])
        ss_ecreq = st.number_input("Sai số EC Req", value=GIATRI_GOC["EC_REQ"])

if tep_ng:
    # 1. Đọc Nhỏ giọt
    raw_ng = []
    for t in tep_ng: raw_ng.extend(json.load(t))
    stt_list = sorted(list(set(str(d.get('STT')) for d in raw_ng if d.get('STT'))))
    kv = st.selectbox("Chọn Khu vực", stt_list)
    
    data_ng = {}
    raw_kv = sorted([d for d in raw_ng if str(d.get('STT')) == kv], key=lambda x: x['Thời gian'])
    for i in range(len(raw_kv)-1):
        if raw_kv[i].get('Trạng thái') == "Bật" and raw_kv[i+1].get('Trạng thái') == "Tắt":
            d_str = raw_kv[i]['Thời gian'][:10]
            data_ng[d_str] = data_ng.get(d_str, 0) + 1

    # 2. Đọc Châm phân
    data_cp = {}
    if tep_cp:
        raw_cp = []
        for t in tep_cp: raw_cp.extend(json.load(t))
        for item in raw_cp:
            if str(item.get('STT')) == kv:
                d_str = item['Thời gian'][:10]
                if d_str not in data_cp: data_cp[d_str] = {'tbec': [], 'ecreq': []}
                vt = chuyen_doi_so_thuc(item, ['TBEC', 'tbec'])
                vr = chuyen_doi_so_thuc(item, ['EC yêu cầu', 'ecreq'])
                if vt: data_cp[d_str]['tbec'].append(vt)
                if vr: data_cp[d_str]['ecreq'].append(vr)

    # 3. Hợp nhất
    ngay_all = sorted(list(set(data_ng.keys()) | set(data_cp.keys())))
    tong_hop = {}
    for n in ngay_all:
        tong_hop[n] = {
            'lan_tuoi': data_ng.get(n, 0),
            'tbec': np.mean(data_cp[n]['tbec']) if n in data_cp and data_cp[n]['tbec'] else 0,
            'ecreq': np.mean(data_cp[n]['ecreq']) if n in data_cp and data_cp[n]['ecreq'] else 0
        }

    # 4. Phân tích & Hiển thị
    chon = []
    if d_lan: chon.append('lan_tuoi')
    if d_tbec: chon.append('tbec')
    if d_ecreq: chon.append('ecreq')
    
    sai_so = {'lan_tuoi': ss_lan, 'tbec': ss_tbec, 'ecreq': ss_ecreq}

    if chon:
        ds_gd = chia_giai_doan_dong_thuan(ngay_all, tong_hop, chon, sai_so)
        
        st.subheader(f"📊 Kết quả phân tích (Đồng thuận: {', '.join(chon)})")
        ve_bieu_do_huong_giai_doan(tong_hop, ds_gd, chon)
        
        # Bảng dữ liệu chi tiết
        bang = []
        for i, gd in enumerate(ds_gd):
            bang.append({
                "Giai đoạn": i + 1,
                "Bắt đầu": gd[0],
                "Kết thúc": gd[-1],
                "Lần tưới (TB)": round(np.mean([tong_hop[d]['lan_tuoi'] for d in gd]), 1),
                "TBEC (TB)": round(np.mean([tong_hop[d]['tbec'] for d in gd]), 2),
                "EC Req (TB)": round(np.mean([tong_hop[d]['ecreq'] for d in gd]), 2)
            })
        st.table(bang)
    else:
        st.warning("Vui lòng chọn ít nhất 1 chỉ số để bắt đầu chia giai đoạn.")
