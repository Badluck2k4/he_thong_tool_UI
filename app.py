import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd

# --- 1. CẤU HÌNH HẰNG SỐ GỐC ---
GIATRI_GOC = {
    "LAN_TUOI": 2.5,
    "TBEC": 8.0,
    "EC_REQ": 5.0,
    "GIAY_MIN": 20,
    "GIAY_MAX": 3600,
    "LAN_MIN_NGAY": 5,
    "GAP_NGAY": 2,
    "MIN_VU": 7
}

st.set_page_config(page_title="Phân tích Mùa vụ v2.0", layout="wide")

# --- 2. CÁC HÀM LOGIC ---

def chuyen_doi_so_thuc(du_lieu, danh_sach_khoa):
    for khoa in danh_sach_khoa:
        gia_tri = du_lieu.get(khoa)
        if gia_tri is not None:
            try:
                return float(str(gia_tri).replace(',', '.'))
            except ValueError:
                continue
    return None

def chia_giai_doan_tu_dong(danh_sach_ngay, du_lieu_ngay, khoa_chi_so, nguong_sai_so):
    danh_sach_cac_gd = []
    if not danh_sach_ngay: return danh_sach_cac_gd
    
    nhom_hien_tai = [danh_sach_ngay[0]]
    for i in range(1, len(danh_sach_ngay)):
        ngay_dang_xet = danh_sach_ngay[i]
        gia_tri_ngay = du_lieu_ngay[ngay_dang_xet][khoa_chi_so]
        trung_binh_nhom = np.mean([du_lieu_ngay[d][khoa_chi_so] for d in nhom_hien_tai])
        
        sai_so = abs(gia_tri_ngay - trung_binh_nhom)
        if (sai_so > nguong_sai_so and len(nhom_hien_tai) >= 3) or (sai_so > nguong_sai_so * 3):
            danh_sach_cac_gd.append(nhom_hien_tai)
            nhom_hien_tai = [ngay_dang_xet]
        else:
            nhom_hien_tai.append(ngay_dang_xet)
            
    danh_sach_cac_gd.append(nhom_hien_tai)
    return danh_sach_cac_gd

def ve_bieu_do(du_lieu_bieu_do, danh_sach_gd, tieu_de, khoa_gia_tri):
    cac_ngay = sorted(du_lieu_bieu_do.keys(), reverse=True)
    gia_tri_hien_thi = [du_lieu_bieu_do[n].get('gia_tri_ao', du_lieu_bieu_do[n][khoa_gia_tri]) for n in cac_ngay]
    gia_tri_thuc = [du_lieu_bieu_do[n][khoa_gia_tri] for n in cac_ngay]
    
    bang_mau = ['#2E7D32', '#1565C0', '#C62828', '#AD1457', '#6A1B9A', '#00838F', '#283593']
    mau_cot = []
    for ngay in cac_ngay:
        mau_chon = bang_mau[0]
        for idx, gd in enumerate(danh_sach_gd):
            if ngay in gd:
                mau_chon = bang_mau[idx % len(bang_mau)]
                break
        mau_cot.append(mau_chon)

    fig, ax = plt.subplots(figsize=(10, len(cac_ngay)*0.4 + 2))
    ax.barh(cac_ngay, gia_tri_hien_thi, color=mau_cot, alpha=0.8)
    for i, v in enumerate(gia_tri_thuc):
        ax.text(gia_tri_hien_thi[i], i, f" {v:.2f}" if khoa_gia_tri != 'so_lan_tuoi' else f" {int(v)}", va='center')
    ax.set_title(tieu_de, fontweight='bold')
    st.pyplot(fig)

# --- 3. GIAO DIỆN 1 (SIDEBAR) ---
with st.sidebar:
    st.header("📂 Dữ liệu & Cấu hình")
    tep_nho_giot = st.file_uploader("Tải file Nhỏ giọt", type=['json'], accept_multiple_files=True)
    tep_cham_phan = st.file_uploader("Tải file Châm phân", type=['json'], accept_multiple_files=True)
    
    st.divider()
    st.subheader("🛠 Chọn cách hiển thị")
    chon_c1 = st.checkbox("Cách 1: Tần suất tưới", value=True)
    chon_c2 = st.checkbox("Cách 2: Chỉ số TBEC")
    chon_c3 = st.checkbox("Cách 3: EC Yêu cầu")

    st.divider()
    with st.expander("⚙️ Chỉnh sai số ngắt GD"):
        if st.button("Reset về mặc định"):
            st.session_state.ss_c1 = GIATRI_GOC["LAN_TUOI"]
            st.session_state.ss_c2 = GIATRI_GOC["TBEC"]
            st.session_state.ss_c3 = GIATRI_GOC["EC_REQ"]

        ss_c1 = st.number_input("Sai số Lần tưới", value=st.session_state.get('ss_c1', GIATRI_GOC["LAN_TUOI"]), step=0.1, key='ss_c1')
        ss_c2 = st.number_input("Sai số TBEC", value=st.session_state.get('ss_c2', GIATRI_GOC["TBEC"]), step=0.1, key='ss_c2')
        ss_c3 = st.number_input("Sai số EC Req", value=st.session_state.get('ss_c3', GIATRI_GOC["EC_REQ"]), step=0.1, key='ss_c3')

# --- 4. GIAO DIỆN 2 (MAINBODY) ---
if tep_nho_giot:
    # (Phần xử lý dữ liệu thô giữ nguyên logic đã tối ưu ở các bước trước)
    du_lieu_tho_ng = []
    for t in tep_nho_giot: du_lieu_tho_ng.extend(json.load(t))
    
    stt_list = sorted(list(set(str(d.get('STT')) for d in du_lieu_tho_ng if d.get('STT'))))
    khu_vuc = st.sidebar.selectbox("🎯 Chọn khu vực (STT)", stt_list)

    # Logic xác định mùa vụ
    thong_ke_ngay = {}
    data_kv = sorted([d for d in du_lieu_tho_ng if str(d.get('STT')) == khu_vuc], key=lambda x: x['Thời gian'])
    for i in range(len(data_kv)-1):
        if data_kv[i].get('Trạng thái') == "Bật" and data_kv[i+1].get('Trạng thái') == "Tắt":
            t1 = datetime.strptime(data_kv[i]['Thời gian'], "%Y-%m-%d %H-%M-%S")
            t2 = datetime.strptime(data_kv[i+1]['Thời gian'], "%Y-%m-%d %H-%M-%S")
            dur = (t2 - t1).total_seconds()
            if GIATRI_GOC["GIAY_MIN"] <= dur <= GIATRI_GOC["GIAY_MAX"]:
                d_str = t1.strftime("%Y-%m-%d")
                thong_ke_ngay[d_str] = thong_ke_ngay.get(d_str, 0) + 1

    ngay_hop_le = sorted([datetime.strptime(n, "%Y-%m-%d").date() for n, c in thong_ke_ngay.items() if c >= GIATRI_GOC["LAN_MIN_NGAY"]])
    
    if ngay_hop_le:
        danh_sach_vu = []
        start = ngay_hop_le[0]
        for i in range(1, len(ngay_hop_le)):
            if (ngay_hop_le[i] - ngay_hop_le[i-1]).days > GIATRI_GOC["GAP_NGAY"]:
                if (ngay_hop_le[i-1] - start).days + 1 >= GIATRI_GOC["MIN_VU"]:
                    danh_sach_vu.append((start, ngay_hop_le[i-1]))
                start = ngay_hop_le[i]
        danh_sach_vu.append((start, ngay_hop_le[-1]))

        chon_vu = st.selectbox("📅 Chọn mùa vụ để phân tích", [f"Vụ {i+1}: {v[0]} đến {v[1]}" for i, v in enumerate(danh_sach_vu)])
        v_hien_tai = danh_sach_vu[int(chon_vu.split(':')[0].split()[1])-1]

        # Chuẩn bị Tab
        list_tab_ten = []
        if chon_c1: list_tab_ten.append("💧 Lần tưới")
        if chon_c2: list_tab_ten.append("🧪 TBEC")
        if chon_c3: list_tab_ten.append("📋 EC Yêu cầu")
        
        if list_tab_ten:
            tabs = st.tabs(list_tab_ten)
            
            # --- TAB 1: LẦN TƯỚI ---
            if chon_c1:
                with tabs[list_tab_ten.index("💧 Lần tưới")]:
                    ngay_vu = sorted([d for d in thong_ke_ngay if v_hien_tai[0] <= datetime.strptime(d, "%Y-%m-%d").date() <= v_hien_tai[1]])
                    data_c1 = {n: {'so_lan_tuoi': thong_ke_ngay[n]} for n in ngay_vu}
                    ds_gd = chia_giai_doan_tu_dong(ngay_vu, data_c1, 'so_lan_tuoi', ss_c1)
                    
                    # Tính giá trị ảo để biểu đồ bằng phẳng
                    for gd in ds_gd:
                        avg = round(np.mean([data_c1[d]['so_lan_tuoi'] for d in gd]))
                        for d in gd: data_c1[d]['gia_tri_ao'] = avg
                    
                    ve_bieu_do(data_c1, ds_gd, "Phân tích theo Lần tưới", 'so_lan_tuoi')
                    
                    # Bảng chi tiết
                    df = pd.DataFrame([{'Ngày': n, 'Số lần': data_c1[n]['so_lan_tuoi'], 'Giai đoạn': i+1} for i, gd in enumerate(ds_gd) for n in gd])
                    st.dataframe(df.sort_values('Ngày', ascending=False), use_container_width=True)

            # --- TAB 2 & 3: CHÂM PHÂN ---
            if (chon_c2 or chon_c3) and tep_cham_phan:
                data_cp_tho = []
                for t in tep_cham_phan: data_cp_tho.extend(json.load(t))
                thong_ke_cp = {}
                for item in data_cp_tho:
                    if str(item.get('STT')) != khu_vuc: continue
                    dt_obj = datetime.strptime(item['Thời gian'], "%Y-%m-%d %H-%M-%S")
                    if v_hien_tai[0] <= dt_obj.date() <= v_hien_tai[1]:
                        n_str = dt_obj.strftime("%Y-%m-%d")
                        if n_str not in thong_ke_cp: thong_ke_cp[n_str] = {'tbec': [], 'ecreq': []}
                        tbec_val = chuyen_doi_so_thuc(item, ['TBEC', 'tbec'])
                        req_val = chuyen_doi_so_thuc(item, ['EC yêu cầu', 'ecreq'])
                        if tbec_val: thong_ke_cp[n_str]['tbec'].append(tbec_val)
                        if req_val: thong_ke_cp[n_str]['ecreq'].append(req_val)
                
                data_chot_cp = {n: {'tbec': np.mean(v['tbec']), 'ecreq': np.mean(v['ecreq'])} for n, v in thong_ke_cp.items() if v['tbec'] or v['ecreq']}
                ngay_cp = sorted(data_chot_cp.keys())

                if chon_c2:
                    with tabs[list_tab_ten.index("🧪 TBEC")]:
                        ds_gd_c2 = chia_giai_doan_tu_dong(ngay_cp, data_chot_cp, 'tbec', ss_c2)
                        ve_bieu_do(data_chot_cp, ds_gd_c2, "Phân tích theo TBEC", 'tbec')
                        df_c2 = pd.DataFrame([{'Ngày': n, 'Chỉ số TBEC': round(data_chot_cp[n]['tbec'], 2), 'Giai đoạn': i+1} for i, gd in enumerate(ds_gd_c2) for n in gd])
                        st.dataframe(df_c2.sort_values('Ngày', ascending=False), use_container_width=True)

                if chon_c3:
                    with tabs[list_tab_ten.index("📋 EC Yêu cầu")]:
                        ds_gd_c3 = chia_giai_doan_tu_dong(ngay_cp, data_chot_cp, 'ecreq', ss_c3)
                        ve_bieu_do(data_chot_cp, ds_gd_c3, "Phân tích theo EC Yêu cầu", 'ecreq')
                        df_c3 = pd.DataFrame([{'Ngày': n, 'EC Yêu cầu': round(data_chot_cp[n]['ecreq'], 2), 'Giai đoạn': i+1} for i, gd in enumerate(ds_gd_c3) for n in gd])
                        st.dataframe(df_c3.sort_values('Ngày', ascending=False), use_container_width=True)
        else:
            st.info("👈 Hãy chọn ít nhất một cách chia ở Thanh bên.")
    else:
        st.error("Không tìm thấy dữ liệu mùa vụ hợp lệ.")
else:
    st.info("👋 Chào mừng! Hãy bắt đầu bằng cách tải file dữ liệu ở Thanh bên (Giao diện 1).")
