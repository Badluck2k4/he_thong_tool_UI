import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# =================================================================
# KHUNG 1 & 2: GIỮ NGUYÊN LOGIC TÍNH TOÁN
# =================================================================
GIATRI_GOC = {"LAN_TUOI": 2.5, "TBEC": 8.0, "EC_REQ": 5.0}

def chuyen_doi_so_thuc(du_lieu, danh_sach_khoa):
    for khoa in danh_sach_khoa:
        gia_tri = du_lieu.get(khoa)
        if gia_tri is not None:
            try: return float(str(gia_tri).replace(',', '.'))
            except: continue
    return None

def chia_giai_doan_dong_thuan(danh_sach_ngay, du_lieu_tong, cac_chi_so_chon, sai_so_dict):
    danh_sach_cac_gd = []
    if not danh_sach_ngay or not cac_chi_so_chon: return []
    nhom_hien_tai = [danh_sach_ngay[0]]
    for i in range(1, len(danh_sach_ngay)):
        ngay_dang_xet = danh_sach_ngay[i]
        kiem_tra_ngat = []
        for cs in cac_chi_so_chon:
            gia_tri_ngay = du_lieu_tong[ngay_dang_xet][cs]
            trung_binh_nhom = np.mean([du_lieu_tong[d][cs] for d in nhom_hien_tai])
            kiem_tra_ngat.append(abs(gia_tri_ngay - trung_binh_nhom) > sai_so_dict[cs])
        if all(kiem_tra_ngat):
            danh_sach_cac_gd.append(nhom_hien_tai)
            nhom_hien_tai = [ngay_dang_xet]
        else: nhom_hien_tai.append(ngay_dang_xet)
    danh_sach_cac_gd.append(nhom_hien_tai)
    return danh_sach_cac_gd

# =================================================================
# KHUNG 3: BIỂU ĐỒ CỘT ĐƠN GIẢN (DỄ HIỂU CHO NÔNG DÂN)
# =================================================================
def ve_bieu_do_cot_don_gian(du_lieu_tong, ds_gd, cac_chi_so_chon):
    ngay_list = sorted(du_lieu_tong.keys())
    x = np.arange(len(ngay_list))
    width = 0.6 / len(cac_chi_so_chon) if cac_chi_so_chon else 0.6
    
    fig, ax = plt.subplots(figsize=(15, 6))
    
    colors = {'lan_tuoi': '#2E7D32', 'tbec': '#1565C0', 'ecreq': '#C62828'}
    labels = {'lan_tuoi': 'Lần tưới', 'tbec': 'Chỉ số TBEC', 'ecreq': 'Chỉ số EC Req'}

    # Vẽ từng nhóm cột cạnh nhau
    for i, cs in enumerate(cac_chi_so_chon):
        vals = [du_lieu_tong[n][cs] for n in ngay_list]
        offset = (i - len(cac_chi_so_chon)/2 + 0.5) * width
        ax.bar(x + offset, vals, width, label=labels[cs], color=colors[cs], alpha=0.8)

    # Vạch đỏ phân chia giai đoạn (Cái này quan trọng để nông dân biết khi nào đổi vụ)
    pos = 0
    for gd in ds_gd[:-1]:
        pos += len(gd)
        ax.axvline(x=pos - 0.5, color='black', linestyle='--', linewidth=1.5, alpha=0.7)
        ax.text(pos - 0.5, ax.get_ylim()[1]*0.9, ' Đổi giai đoạn', color='black', fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels([n[-5:] for n in ngay_list], rotation=45)
    ax.legend()
    ax.set_title("BIỂU ĐỒ THEO DÕI MÙA VỤ", fontsize=16, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    st.pyplot(fig)

# =================================================================
# KHUNG 4: GIAO DIỆN CHÍNH
# =================================================================
st.sidebar.header("📂 Tải dữ liệu")
tep_ng = st.sidebar.file_uploader("File Nhỏ giọt", type=['json'], accept_multiple_files=True)
tep_cp = st.sidebar.file_uploader("File Châm phân", type=['json'], accept_multiple_files=True)

st.sidebar.divider()
st.sidebar.header("🔍 Chọn chỉ số theo dõi")
d_lan = st.sidebar.checkbox("Lần tưới", value=True)
d_tbec = st.sidebar.checkbox("TBEC", value=True)
d_ecreq = st.sidebar.checkbox("EC Req", value=False)

if tep_ng:
    # Xử lý dữ liệu (Rút gọn để tập trung vào hiển thị)
    raw_ng = []
    for t in tep_ng: raw_ng.extend(json.load(t))
    stt_list = sorted(list(set(str(d.get('STT')) for d in raw_ng if d.get('STT'))))
    kv = st.selectbox("Chọn Khu vực canh tác", stt_list)
    
    # ... (Các bước xử lý data_ng, data_cp và tong_hop giữ nguyên như bản trước) ...
    # [Giả định biến tong_hop và ngay_all đã được tính toán giống bản v3.8]
    
    # Đoạn này tôi viết tắt để bạn dễ hình dung luồng:
    data_ng = {}
    for i in range(len(raw_ng)-1):
        if str(raw_ng[i].get('STT')) == kv and raw_ng[i].get('Trạng thái') == "Bật":
            d_str = raw_ng[i]['Thời gian'][:10]
            data_ng[d_str] = data_ng.get(d_str, 0) + 1
            
    data_cp = {}
    if tep_cp:
        raw_cp = []
        for t in tep_cp: raw_cp.extend(json.load(t))
        for item in raw_cp:
            if str(item.get('STT')) == kv:
                d_str = item['Thời gian'][:10]
                if d_str not in data_cp: data_cp[d_str] = {'tbec': [], 'ecreq': []}
                vt = chuyen_doi_so_thuc(item, ['TBEC', 'tbec'])
                if vt: data_cp[d_str]['tbec'].append(vt)

    ngay_all = sorted(list(set(data_ng.keys()) | set(data_cp.keys())))
    tong_hop = {n: {'lan_tuoi': data_ng.get(n, 0), 'tbec': np.mean(data_cp[n]['tbec']) if n in data_cp else 0, 'ecreq': 0} for n in ngay_all}

    chon = []
    if d_lan: chon.append('lan_tuoi')
    if d_tbec: chon.append('tbec')
    
    if chon:
        sai_so = {'lan_tuoi': GIATRI_GOC["LAN_TUOI"], 'tbec': GIATRI_GOC["TBEC"], 'ecreq': GIATRI_GOC["EC_REQ"]}
        ds_gd = chia_giai_doan_dong_thuan(ngay_all, tong_hop, chon, sai_so)
        
        ve_bieu_do_cot_don_gian(tong_hop, ds_gd, chon)
        
        # Bảng dữ liệu ngay dưới biểu đồ
        st.subheader("📋 Chi tiết các giai đoạn")
        st.table([{"Giai đoạn": i+1, "Từ ngày": g[0], "Đến ngày": g[-1], "Số ngày": len(g)} for i, g in enumerate(ds_gd)])
