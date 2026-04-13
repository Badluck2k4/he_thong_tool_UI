import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, date

# --- 1. CẤU HÌNH HẰNG SỐ ---
GIATRI_GOC = {
    "LAN_TUOI": 2.5, "TBEC": 8.0, "EC_REQ": 5.0,
    "GIAY_MIN": 20, "GIAY_MAX": 3600, "LAN_MIN_NGAY": 5,
    "GAP_NGAY": 2, "MIN_VU": 7
}

st.set_page_config(page_title="Phân tích Mùa vụ v3.2", layout="wide")

# --- 2. CÁC HÀM LOGIC ---

def chuyen_doi_so_thuc(du_lieu, danh_sach_khoa):
    for khoa in danh_sach_khoa:
        gia_tri = du_lieu.get(khoa)
        if gia_tri is not None:
            try: return float(str(gia_tri).replace(',', '.'))
            except: continue
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
        else: nhom_hien_tai.append(ngay_dang_xet)
    danh_sach_cac_gd.append(nhom_hien_tai)
    return danh_sach_cac_gd

def ve_bieu_do_doc(du_lieu_bieu_do, danh_sach_gd, tieu_de, khoa_gia_tri):
    cac_ngay = sorted(du_lieu_bieu_do.keys())
    so_thu_tu = list(range(1, len(cac_ngay) + 1))
    gia_tri_hien_thi = [du_lieu_bieu_do[n].get('gia_tri_ao', du_lieu_bieu_do[n][khoa_gia_tri]) for n in cac_ngay]
    
    bang_mau = ['#2E7D32', '#1565C0', '#C62828', '#AD1457', '#6A1B9A', '#00838F', '#283593']
    mau_cot = []
    for ngay in cac_ngay:
        mau_chon = bang_mau[0]
        for idx, gd in enumerate(danh_sach_gd):
            if ngay in gd:
                mau_chon = bang_mau[idx % len(bang_mau)]
                break
        mau_cot.append(mau_chon)

    chieu_rong = max(10, len(cac_ngay) * 0.25)
    fig, ax = plt.subplots(figsize=(chieu_rong, 5))
    ax.bar(so_thu_tu, gia_tri_hien_thi, color=mau_cot, alpha=0.8)
    ax.set_title(tieu_de, fontweight='bold', fontsize=14, pad=20)
    ax.set_xlabel("Số thứ tự ngày (STT)", fontsize=10)
    ax.set_xticks(so_thu_tu)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    st.pyplot(fig)

# --- 3. GIAO DIỆN 1 (SIDEBAR) ---
with st.sidebar:
    st.header("📂 Dữ liệu & Cấu hình")
    tep_nho_giot = st.file_uploader("Tải file Nhỏ giọt", type=['json'], accept_multiple_files=True)
    tep_cham_phan = st.file_uploader("Tải file Châm phân", type=['json'], accept_multiple_files=True)
    
    st.divider()
    st.subheader("🔍 Lọc thời gian")
    ngay_bat_dau = st.date_input("Từ ngày", value=None)
    ngay_ket_thuc = st.date_input("Đến ngày", value=None)

    st.divider()
    st.subheader("🛠 Cách hiển thị")
    chon_c1 = st.checkbox("Cách 1: Lần tưới", value=True)
    chon_c2 = st.checkbox("Cách 2: TBEC")
    chon_c3 = st.checkbox("Cách 3: EC Req")

    st.divider()
    with st.expander("⚙️ Chỉnh sai số"):
        if st.button("Reset"):
            st.session_state.ss_c1 = GIATRI_GOC["LAN_TUOI"]
            st.session_state.ss_c2 = GIATRI_GOC["TBEC"]
            st.session_state.ss_c3 = GIATRI_GOC["EC_REQ"]
        ss_c1 = st.number_input("Lần tưới", value=st.session_state.get('ss_c1', GIATRI_GOC["LAN_TUOI"]), step=0.1)
        ss_c2 = st.number_input("TBEC", value=st.session_state.get('ss_c2', GIATRI_GOC["TBEC"]), step=0.1)
        ss_c3 = st.number_input("EC Req", value=st.session_state.get('ss_c3', GIATRI_GOC["EC_REQ"]), step=0.1)

# --- 4. GIAO DIỆN 2 (MAINBODY) ---
if tep_nho_giot:
    du_lieu_tho_ng = []
    for t in tep_nho_giot:
        try: du_lieu_tho_ng.extend(json.load(t))
        except: continue
    
    stt_list = sorted(list(set(str(d.get('STT')) for d in du_lieu_tho_ng if d.get('STT'))))
    khu_vuc = st.sidebar.selectbox("🎯 Khu vực", stt_list)

    thong_ke_ngay = {} # Lưu số lần tưới
    thoi_gian_ngay = {} # Lưu tổng thời gian tưới (giây)
    
    data_kv = sorted([d for d in du_lieu_tho_ng if str(d.get('STT')) == khu_vuc], key=lambda x: x['Thời gian'])
    for i in range(len(data_kv)-1):
        if data_kv[i].get('Trạng thái') == "Bật" and data_kv[i+1].get('Trạng thái') == "Tắt":
            try:
                t1 = datetime.strptime(data_kv[i]['Thời gian'], "%Y-%m-%d %H-%M-%S")
                t2 = datetime.strptime(data_kv[i+1]['Thời gian'], "%Y-%m-%d %H-%M-%S")
                dur = (t2-t1).total_seconds()
                if GIATRI_GOC["GIAY_MIN"] <= dur <= GIATRI_GOC["GIAY_MAX"]:
                    d_str = t1.strftime("%Y-%m-%d")
                    # Kiểm tra lọc thời gian tùy chọn
                    curr_date = t1.date()
                    if (ngay_bat_dau and curr_date < ngay_bat_dau) or (ngay_ket_thuc and curr_date > ngay_ket_thuc):
                        continue
                        
                    thong_ke_ngay[d_str] = thong_ke_ngay.get(d_str, 0) + 1
                    thoi_gian_ngay[d_str] = thoi_gian_ngay.get(d_str, 0) + dur
            except: continue

    ngay_hl = sorted([datetime.strptime(n, "%Y-%m-%d").date() for n, c in thong_ke_ngay.items() if c >= GIATRI_GOC["LAN_MIN_NGAY"]])
    
    if ngay_hl:
        # Tách mùa vụ dựa trên logic gap ngày
        danh_sach_vu = []
        start = ngay_hl[0]
        for i in range(1, len(ngay_hl)):
            if (ngay_hl[i] - ngay_hl[i-1]).days > GIATRI_GOC["GAP_NGAY"]:
                if (ngay_hl[i-1] - start).days + 1 >= GIATRI_GOC["MIN_VU"]:
                    danh_sach_vu.append((start, ngay_hl[i-1]))
                start = ngay_hl[i]
        danh_sach_vu.append((start, ngay_hl[-1]))

        chon_vu_str = st.selectbox("📅 Mùa vụ", [f"Khoảng {i+1}: {v[0]} -> {v[1]}" for i, v in enumerate(danh_sach_vu)])
        idx_v = int(chon_vu_str.split(':')[0].split()[1])-1
        v_hien_tai = danh_sach_vu[idx_v]
        
        tong_ngay_vu = (v_hien_tai[1] - v_hien_tai[0]).days + 1
        st.info(f"📊 **Thông tin vùng lọc:** Kéo dài **{tong_ngay_vu} ngày** (Từ {v_hien_tai[0]} đến {v_hien_tai[1]})")

        tabs = st.tabs([t for t, c in zip(["💧 Lần tưới", "🧪 TBEC", "📋 EC Req"], [chon_c1, chon_c2, chon_c3]) if c])
        tab_idx = 0
        
        if chon_c1:
            with tabs[tab_idx]:
                ngay_vu = sorted([d for d in thong_ke_ngay if v_hien_tai[0] <= datetime.strptime(d, "%Y-%m-%d").date() <= v_hien_tai[1]])
                data_c1 = {n: {'val': thong_ke_ngay[n], 'dur': thoi_gian_ngay[n]} for n in ngay_vu}
                ds_gd = chia_giai_doan_tu_dong(ngay_vu, data_c1, 'val', ss_c1)
                for gd in ds_gd:
                    avg = round(np.mean([data_c1[d]['val'] for d in gd]))
                    for d in gd: data_c1[d]['gia_tri_ao'] = avg
                
                ve_bieu_do_doc(data_c1, ds_gd, "Biểu đồ Lần tưới", 'val')
                
                table_data = []
                stt_ngay = 1
                for i, gd in enumerate(ds_gd):
                    for n in gd:
                        mins = int(data_c1[n]['dur'] // 60)
                        secs = int(data_c1[n]['dur'] % 60)
                        table_data.append({
                            "STT": stt_ngay, 
                            "Ngày": n, 
                            "Lần tưới": data_c1[n]['val'], 
                            "Tổng thời gian (phút:giây)": f"{mins:02d}:{secs:02d}",
                            "Giai đoạn": i+1
                        })
                        stt_ngay += 1
                st.write("**Bảng chi tiết dữ liệu tưới:**")
                st.table(table_data)
            tab_idx += 1

        if (chon_c2 or chon_c3) and tep_cham_phan:
            # Logic xử lý file châm phân (đã tích hợp lọc thời gian ở trên)
            data_cp_tho = []
            for t in tep_cham_phan: data_cp_tho.extend(json.load(t))
            thong_ke_cp = {}
            for item in data_cp_tho:
                if str(item.get('STT')) != khu_vuc: continue
                try:
                    dt = datetime.strptime(item['Thời gian'], "%Y-%m-%d %H-%M-%S")
                    curr_d = dt.date()
                    # Lọc theo Date Input và theo Mùa vụ đã chọn
                    if (ngay_bat_dau and curr_d < ngay_bat_dau) or (ngay_ket_thuc and curr_d > ngay_ket_thuc):
                        continue
                    if v_hien_tai[0] <= curr_d <= v_hien_tai[1]:
                        n_str = dt.strftime("%Y-%m-%d")
                        if n_str not in thong_ke_cp: thong_ke_cp[n_str] = {'tbec': [], 'ecreq': []}
                        v_t = chuyen_doi_so_thuc(item, ['TBEC', 'tbec'])
                        v_r = chuyen_doi_so_thuc(item, ['EC yêu cầu', 'ecreq'])
                        if v_t is not None: thong_ke_cp[n_str]['tbec'].append(v_t)
                        if v_r is not None: thong_ke_cp[n_str]['ecreq'].append(v_r)
                except: continue
            
            data_chot_cp = {n: {'tbec': np.mean(v['tbec']), 'ecreq': np.mean(v['ecreq'])} for n, v in thong_ke_cp.items() if v['tbec'] or v['ecreq']}
            ngay_cp = sorted(data_chot_cp.keys())

            if chon_c2 and ngay_cp:
                with tabs[tab_idx]:
                    ds_gd2 = chia_giai_doan_tu_dong(ngay_cp, data_chot_cp, 'tbec', ss_c2)
                    ve_bieu_do_doc(data_chot_cp, ds_gd2, "Biểu đồ TBEC", 'tbec')
                    table_data2 = []
                    stt_ngay = 1
                    for i, gd in enumerate(ds_gd2):
                        for n in gd:
                            table_data2.append({"STT": stt_ngay, "Ngày": n, "TBEC": round(data_chot_cp[n]['tbec'],2), "Giai đoạn": i+1})
                            stt_ngay += 1
                    st.write("**Bảng chi tiết TBEC:**")
                    st.table(table_data2)
                tab_idx += 1

            if chon_c3 and ngay_cp:
                with tabs[tab_idx]:
                    ds_gd3 = chia_giai_doan_tu_dong(ngay_cp, data_chot_cp, 'ecreq', ss_c3)
                    ve_bieu_do_doc(data_chot_cp, ds_gd3, "Biểu đồ EC Req", 'ecreq')
                    table_data3 = []
                    stt_ngay = 1
                    for i, gd in enumerate(ds_gd3):
                        for n in gd:
                            table_data3.append({"STT": stt_ngay, "Ngày": n, "EC Req": round(data_chot_cp[n]['ecreq'],2), "Giai đoạn": i+1})
                            stt_ngay += 1
                    st.write("**Bảng chi tiết EC Req:**")
                    st.table(table_data3)
    else: st.error("Không tìm thấy dữ liệu trong khoảng thời gian đã chọn.")
else: st.info("👋 Hãy tải file ở Giao diện 1.")
