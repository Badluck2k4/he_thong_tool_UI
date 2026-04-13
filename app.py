import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# --- 1. CẤU HÌNH HẰNG SỐ GỐC ---
GIATRI_GOC = {
    "LAN_TUOI": 1.0, 
    "TBEC": 4.0,      
    "EC_REQ": 2.0,    
    "GIAY_MIN": 20,
    "GIAY_MAX": 3600,
    "LAN_MIN_NGAY": 5,
    "GAP_NGAY": 2,
    "MIN_VU": 7
}

st.set_page_config(page_title="Phân tích Mùa vụ Đa biến v5.8", layout="wide")

# --- KHỞI TẠO TRẠNG THÁI (SESSION STATE) CHO TÍNH NĂNG RESET ---
if 'ss_lan_key' not in st.session_state:
    st.session_state['ss_lan_key'] = GIATRI_GOC["LAN_TUOI"]
if 'ss_tbec_key' not in st.session_state:
    st.session_state['ss_tbec_key'] = GIATRI_GOC["TBEC"]
if 'ss_req_key' not in st.session_state:
    st.session_state['ss_req_key'] = GIATRI_GOC["EC_REQ"]

def phuc_hoi_sai_so_mac_dinh():
    st.session_state['ss_lan_key'] = GIATRI_GOC["LAN_TUOI"]
    st.session_state['ss_tbec_key'] = GIATRI_GOC["TBEC"]
    st.session_state['ss_req_key'] = GIATRI_GOC["EC_REQ"]

# --- 2. CÁC HÀM LOGIC ---

def chuyen_doi_so_thuc(du_lieu, danh_sach_khoa):
    for khoa in danh_sach_khoa:
        gia_tri = du_lieu.get(khoa)
        if gia_tri is not None:
            try:
                return float(str(gia_tri).replace(',', '.'))
            except (ValueError, TypeError):
                continue
    return None

def chia_giai_doan_bien_thien_dong_thoi(danh_sach_ngay, du_lieu_tong_hop, cau_hinh_nguong):
    danh_sach_cac_gd = []
    if not danh_sach_ngay: return danh_sach_cac_gd
    if not cau_hinh_nguong: return [danh_sach_ngay]

    nhom_hien_tai = [danh_sach_ngay[0]]
    for i in range(1, len(danh_sach_ngay)):
        ngay_dang_xet = danh_sach_ngay[i]
        ngay_truoc_do = nhom_hien_tai[-1]  
        ket_qua_kiem_tra = []
        for khoa_chi_so, nguong_sai_so in cau_hinh_nguong.items():
            v_now = du_lieu_tong_hop[ngay_dang_xet].get(khoa_chi_so)
            v_prev = du_lieu_tong_hop[ngay_truoc_do].get(khoa_chi_so)
            if v_now is not None and v_prev is not None:
                if abs(v_now - v_prev) > nguong_sai_so:
                    ket_qua_kiem_tra.append(True)
        
        # Chỉ ngắt giai đoạn nếu TẤT CẢ các chỉ số được chọn đều vượt ngưỡng
        if len(ket_qua_kiem_tra) == len(cau_hinh_nguong) and all(ket_qua_kiem_tra):
            danh_sach_cac_gd.append(nhom_hien_tai)
            nhom_hien_tai = [ngay_dang_xet]
        else:
            nhom_hien_tai.append(ngay_dang_xet)
    danh_sach_cac_gd.append(nhom_hien_tai)
    return danh_sach_cac_gd

def ve_bieu_do_dong_thoi(du_lieu_tong_hop, danh_sach_gd, chi_so_chon):
    ngay_co_so = sorted(du_lieu_tong_hop.keys())
    if not ngay_co_so or not chi_so_chon: return

    x_labels = list(range(1, len(ngay_co_so) + 1))
    map_data = {
        "Lần tưới": ([du_lieu_tong_hop[n]['so_lan_tuoi'] for n in ngay_co_so], "Lần tưới (Lần)"),
        "TBEC": ([du_lieu_tong_hop[n]['tbec'] for n in ngay_co_so], "TBEC"),
        "EC Yêu cầu": ([du_lieu_tong_hop[n]['ecreq'] for n in ngay_co_so], "EC Yêu cầu")
    }

    bang_mau = ['#2E7D32', '#1565C0', '#C62828', '#AD1457', '#6A1B9A', '#00838F', '#283593']
    mau_cot = []
    ranh_gioi_gd = [] 
    for i, ngay in enumerate(ngay_co_so):
        for idx, gd in enumerate(danh_sach_gd):
            if ngay in gd:
                mau_cot.append(bang_mau[idx % len(bang_mau)])
                if ngay == gd[0] and idx > 0: ranh_gioi_gd.append(i + 1)
                break

    so_luong_tang = len(chi_so_chon)
    
    fig, axes = plt.subplots(so_luong_tang, 1, figsize=(20, 7 * so_luong_tang), sharex=True)
    
    if so_luong_tang == 1: axes = [axes]
        
    fig.suptitle(f"PHÂN TÍCH BIẾN THIÊN: {' - '.join(chi_so_chon).upper()}", 
                 fontsize=24, fontweight='bold', y=0.96)

    def ve_tung_tang(ax, data, title, color_list):
        ax.bar(x_labels, data, color=color_list, alpha=0.85, edgecolor='black', linewidth=0.5)
        ax.set_ylabel(title, fontweight='bold', fontsize=16)
        
        for rg in ranh_gioi_gd:
            ax.axvline(x=rg - 0.5, color='red', linestyle='--', alpha=0.8, linewidth=2)
        
        ax.grid(axis='y', linestyle=':', alpha=0.6)
        ax.tick_params(axis='y', labelsize=14)
        max_val = max(data) if data and max(data) > 0 else 1
        ax.set_ylim(0, max_val * 1.1)

    for idx, ten_chi_so in enumerate(chi_so_chon):
        data, title = map_data[ten_chi_so]
        ve_tung_tang(axes[idx], data, title, mau_cot)

    axes[-1].set_xticks(x_labels)
    axes[-1].set_xticklabels(x_labels, fontsize=14, fontweight='bold')
    axes[-1].set_xlabel("SỐ THỨ TỰ NGÀY", fontweight='bold', fontsize=16, labelpad=15)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    st.pyplot(fig, use_container_width=True)

# --- 3. GIAO DIỆN CHÍNH ---
with st.sidebar:
    st.header("📂 Dữ liệu & Cấu hình")
    tep_nho_giot = st.file_uploader("Tải file Nhỏ giọt", type=['json'], accept_multiple_files=True)
    tep_cham_phan = st.file_uploader("Tải file Châm phân", type=['json'], accept_multiple_files=True)
    
    st.divider()
    st.subheader("📊 Chọn chỉ số hiển thị & phân tích")
    tick_lan = st.checkbox("Lần tưới", value=True)
    tick_tbec = st.checkbox("TBEC", value=True)
    tick_req = st.checkbox("EC Yêu cầu", value=True)
    
    chi_so_chon = []
    if tick_lan: chi_so_chon.append("Lần tưới")
    if tick_tbec: chi_so_chon.append("TBEC")
    if tick_req: chi_so_chon.append("EC Yêu cầu")

    st.divider()
    st.subheader("⚙️ Ngưỡng ngắt giai đoạn")
    
    st.button("🔄 Đặt lại mặc định", on_click=phuc_hoi_sai_so_mac_dinh, use_container_width=True)
    
    ss_lan = st.number_input("Sai số Lần tưới", key="ss_lan_key", step=0.1)
    ss_tbec = st.number_input("Sai số TBEC", key="ss_tbec_key", step=0.1)
    ss_req = st.number_input("Sai số EC Req", key="ss_req_key", step=0.1)

if tep_nho_giot:
    du_lieu_tho_ng = []
    for t in tep_nho_giot: du_lieu_tho_ng.extend(json.load(t))
    stt_list = sorted(list(set(str(d.get('STT')) for d in du_lieu_tho_ng if d.get('STT'))))
    khu_vuc = st.sidebar.selectbox("🎯 Chọn khu vực", stt_list)

    thong_ke_ngay = {}
    thoi_gian_ngay = {} 
    
    data_kv = sorted([d for d in du_lieu_tho_ng if str(d.get('STT')) == khu_vuc], key=lambda x: x['Thời gian'])
    for i in range(len(data_kv)-1):
        if data_kv[i].get('Trạng thái') == "Bật" and data_kv[i+1].get('Trạng thái') == "Tắt":
            t1 = datetime.strptime(data_kv[i]['Thời gian'], "%Y-%m-%d %H-%M-%S")
            t2 = datetime.strptime(data_kv[i+1]['Thời gian'], "%Y-%m-%d %H-%M-%S")
            thoi_gian_tuoi = (t2 - t1).total_seconds()
            
            if GIATRI_GOC["GIAY_MIN"] <= thoi_gian_tuoi <= GIATRI_GOC["GIAY_MAX"]:
                d_str = t1.strftime("%Y-%m-%d")
                thong_ke_ngay[d_str] = thong_ke_ngay.get(d_str, 0) + 1
                thoi_gian_ngay[d_str] = thoi_gian_ngay.get(d_str, 0) + thoi_gian_tuoi

    ngay_ok = sorted([datetime.strptime(n, "%Y-%m-%d").date() for n, c in thong_ke_ngay.items() if c >= GIATRI_GOC["LAN_MIN_NGAY"]])
    
    if ngay_ok:
        danh_sach_vu = []
        start = ngay_ok[0]
        for i in range(1, len(ngay_ok)):
            if (ngay_ok[i] - ngay_ok[i-1]).days > GIATRI_GOC["GAP_NGAY"]:
                if (ngay_ok[i-1] - start).days + 1 >= GIATRI_GOC["MIN_VU"]:
                    danh_sach_vu.append((start, ngay_ok[i-1]))
                start = ngay_ok[i]
        danh_sach_vu.append((start, ngay_ok[-1]))

        chon_vu = st.selectbox("📅 Chọn mùa vụ", [f"Vụ {i+1}: {v[0]} đến {v[1]}" for i, v in enumerate(danh_sach_vu)])
        v_hien_tai = danh_sach_vu[int(chon_vu.split(':')[0].split()[1])-1]

        data_cp_ngay = {}
        if tep_cham_phan:
            for t in tep_cham_phan:
                for item in json.load(t):
                    if str(item.get('STT')) != khu_vuc: continue
                    dt = datetime.strptime(item['Thời gian'], "%Y-%m-%d %H-%M-%S")
                    if v_hien_tai[0] <= dt.date() <= v_hien_tai[1]:
                        n_str = dt.strftime("%Y-%m-%d")
                        if n_str not in data_cp_ngay: data_cp_ngay[n_str] = {'tbec': [], 'req': []}
                        v1 = chuyen_doi_so_thuc(item, ['TBEC', 'tbec'])
                        v2 = chuyen_doi_so_thuc(item, ['EC yêu cầu', 'ecreq'])
                        if v1 is not None: data_cp_ngay[n_str]['tbec'].append(v1)
                        if v2 is not None: data_cp_ngay[n_str]['req'].append(v2)

        du_lieu_tong_hop = {}
        ngay_vu = sorted([n for n in thong_ke_ngay if v_hien_tai[0] <= datetime.strptime(n, "%Y-%m-%d").date() <= v_hien_tai[1]])
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

        if not chi_so_chon:
            st.warning("⚠️ Hãy chọn ít nhất một chỉ số để hiển thị biểu đồ.")
        else:
            # SỬA LỖI Ở ĐÂY: Xây dựng dictionary cấu hình ngưỡng linh hoạt dựa trên chỉ số đang tick
            nguong_ngat_thuc_te = {}
            if "Lần tưới" in chi_so_chon:
                nguong_ngat_thuc_te['so_lan_tuoi'] = ss_lan
            if "TBEC" in chi_so_chon:
                nguong_ngat_thuc_te['tbec'] = ss_tbec
            if "EC Yêu cầu" in chi_so_chon:
                nguong_ngat_thuc_te['ecreq'] = ss_req

            ds_giai_doan = chia_giai_doan_bien_thien_dong_thoi(ngay_vu, du_lieu_tong_hop, nguong_ngat_thuc_te)

            st.write(f"### Phân tích: {len(ds_giai_doan)} giai đoạn")
            ve_bieu_do_dong_thoi(du_lieu_tong_hop, ds_giai_doan, chi_so_chon)

            st.divider()
            st.write("### Bảng chi tiết")
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
    st.info("👋 Vui lòng tải dữ liệu.")
