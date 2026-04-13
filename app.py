import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# =================================================================
# KHUNG 1: CẤU HÌNH
# =================================================================
GIATRI_GOC = {"LAN_TUOI": 2.5, "TBEC": 8.0, "EC_REQ": 5.0}

def chuyen_doi_so_thuc(du_lieu, danh_sach_khoa):
    for khoa in danh_sach_khoa:
        gia_tri = du_lieu.get(khoa)
        if gia_tri is not None:
            try: return float(str(gia_tri).replace(',', '.'))
            except: continue
    return None

# =================================================================
# KHUNG 2: LOGIC CHIA GIAI ĐOẠN (SỬA LỖI GỘP NGÀY)
# =================================================================
def chia_giai_doan_dong_thuan(danh_sach_ngay, du_lieu_tong, cac_chi_so_chon, sai_so_dict):
    danh_sach_cac_gd = []
    # Loại bỏ các ngày trống (None) trước khi tính toán logic
    ngay_co_du_lieu = [n for n in danh_sach_ngay if du_lieu_tong[n] is not None]
    if not ngay_co_du_lieu or not cac_chi_so_chon: return []
    
    nhom_hien_tai = [ngay_co_du_lieu[0]]
    for i in range(1, len(ngay_co_du_lieu)):
        ngay_dang_xet = ngay_co_du_lieu[i]
        kiem_tra_ngat = []
        for cs in cac_chi_so_chon:
            gia_tri_ngay = du_lieu_tong[ngay_dang_xet][cs]
            trung_binh_nhom = np.mean([du_lieu_tong[d][cs] for d in nhom_hien_tai])
            kiem_tra_ngat.append(abs(gia_tri_ngay - trung_binh_nhom) > sai_so_dict[cs])
        
        # Ngắt giai đoạn khi thỏa mãn điều kiện đồng thuận
        if all(kiem_tra_ngat):
            danh_sach_cac_gd.append(nhom_hien_tai)
            nhom_hien_tai = [ngay_dang_xet]
        else:
            nhom_hien_tai.append(ngay_dang_xet)
    danh_sach_cac_gd.append(nhom_hien_tai)
    return danh_sach_cac_gd

# =================================================================
# KHUNG 3: BIỂU ĐỒ CỘT (DỄ NHÌN, CÓ KHOẢNG NGHỈ)
# =================================================================
def ve_bieu_do_nong_dan(du_lieu_tong, ds_gd, cac_chi_so_chon):
    ngay_list = sorted(du_lieu_tong.keys())
    x = np.arange(len(ngay_list))
    width = 0.7 / len(cac_chi_so_chon) if cac_chi_so_chon else 0.7
    
    # Ép kích thước rộng ra để không bị bóp nhỏ
    fig, ax = plt.subplots(figsize=(max(16, len(ngay_list) * 0.4), 6))
    
    colors = {'lan_tuoi': '#2E7D32', 'tbec': '#1565C0', 'ecreq': '#C62828'}
    labels = {'lan_tuoi': 'Lần tưới', 'tbec': 'Chỉ số TBEC', 'ecreq': 'Chỉ số EC Req'}

    for i, cs in enumerate(cac_chi_so_chon):
        vals = []
        for n in ngay_list:
            if du_lieu_tong[n] is None: vals.append(0)
            else: vals.append(du_lieu_tong[n][cs])
            
        offset = (i - len(cac_chi_so_chon)/2 + 0.5) * width
        ax.bar(x + offset, vals, width, label=labels[cs], color=colors[cs])

    # Kẻ vạch đổi giai đoạn
    pos = 0
    all_ngay_co_dl = [n for n in ngay_list if du_lieu_tong[n] is not None]
    for gd in ds_gd[:-1]:
        # Tìm vị trí thực tế trên trục X của ngày cuối giai đoạn
        ngay_cuoi = gd[-1]
        idx = ngay_list.index(ngay_cuoi)
        ax.axvline(x=idx + 0.5, color='red', linestyle='--', alpha=0.7)

    ax.set_xticks(x)
    ax.set_xticklabels([n[-5:] for n in ngay_list], rotation=90, fontsize=8)
    ax.legend()
    plt.grid(axis='y', alpha=0.2)
    st.pyplot(fig, use_container_width=False) # Tắt container_width để hiện thanh cuộn ngang

# =================================================================
# KHUNG 4: XỬ LÝ CHÍNH
# =================================================================
st.sidebar.header("📂 Dữ liệu")
tep_ng = st.sidebar.file_uploader("File Nhỏ giọt", type=['json'], accept_multiple_files=True)
tep_cp = st.sidebar.file_uploader("File Châm phân", type=['json'], accept_multiple_files=True)

d_lan = st.sidebar.checkbox("Lần tưới", value=True)
d_tbec = st.sidebar.checkbox("TBEC", value=True)

if tep_ng:
    raw_ng = []
    for t in tep_ng: raw_ng.extend(json.load(t))
    stt_list = sorted(list(set(str(d.get('STT')) for d in raw_ng if d.get('STT'))))
    kv = st.selectbox("Chọn Khu vực", stt_list)
    
    # 1. Gom dữ liệu Lần tưới
    data_ng = {}
    for i in range(len(raw_ng)-1):
        if str(raw_ng[i].get('STT')) == kv and raw_ng[i].get('Trạng thái') == "Bật":
            d_str = raw_ng[i]['Thời gian'][:10]
            data_ng[d_str] = data_ng.get(d_str, 0) + 1
            
    # 2. Gom dữ liệu TBEC
    data_cp = {}
    if tep_cp:
        raw_cp = []
        for t in tep_cp: raw_cp.extend(json.load(t))
        for item in raw_cp:
            if str(item.get('STT')) == kv:
                d_str = item['Thời gian'][:10]
                if d_str not in data_cp: data_cp[d_str] = []
                v = chuyen_doi_so_thuc(item, ['TBEC', 'tbec'])
                if v: data_cp[d_str].append(v)

    # 3. Tạo dòng thời gian liên tục (Để hiện khoảng cách giữa các vụ)
    if data_ng:
        all_dates = sorted(data_ng.keys())
        start_d = datetime.strptime(all_dates[0], "%Y-%m-%d").date()
        end_d = datetime.strptime(all_dates[-1], "%Y-%m-%d").date()
        
        ngay_truc_x = []
        tong_hop = {}
        curr = start_d
        while curr <= end_d:
            d_str = curr.strftime("%Y-%m-%d")
            ngay_truc_x.append(d_str)
            if d_str in data_ng or d_str in data_cp:
                tong_hop[d_str] = {
                    'lan_tuoi': data_ng.get(d_str, 0),
                    'tbec': np.mean(data_cp[d_str]) if d_str in data_cp and data_cp[d_str] else 0,
                    'ecreq': 0
                }
            else:
                tong_hop[d_str] = None # Ngày nghỉ
            curr += timedelta(days=1)

        chon = []
        if d_lan: chon.append('lan_tuoi')
        if d_tbec: chon.append('tbec')

        if chon:
            sai_so = {'lan_tuoi': GIATRI_GOC["LAN_TUOI"], 'tbec': GIATRI_GOC["TBEC"], 'ecreq': GIATRI_GOC["EC_REQ"]}
            ds_gd = chia_giai_doan_dong_thuan(ngay_truc_x, tong_hop, chon, sai_so)
            
            st.subheader("📈 BIỂU ĐỒ THEO DÕI MÙA VỤ")
            ve_bieu_do_nong_dan(tong_hop, ds_gd, chon)
            
            st.subheader("📋 Chi tiết các giai đoạn")
            bang = []
            for i, g in enumerate(ds_gd):
                bang.append({
                    "Giai đoạn": i+1,
                    "Từ ngày": g[0],
                    "Đến ngày": g[-1],
                    "Số ngày thực tế": len(g)
                })
            st.table(bang)
