import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# --- 1. CẤU HÌNH HẰNG SỐ GỐC ---
GIATRI_GOC = {
    "LAN_TUOI": 1.0,  # Sai số 1 lần tưới
    "TBEC": 4.0,      # Sai số 4.0 đơn vị
    "EC_REQ": 2.0,    # Sai số 2.0 đơn vị
    "GIAY_MIN": 20,
    "GIAY_MAX": 3600,
    "LAN_MIN_NGAY": 5,
    "GAP_NGAY": 2,
    "MIN_VU": 7
}

st.set_page_config(page_title="Phân tích Mùa vụ Đa biến v5.2", layout="wide")

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
    if not danh_sach_ngay:
        return danh_sach_cac_gd

    if not cau_hinh_nguong:
        return [danh_sach_ngay]

    nhom_hien_tai = [danh_sach_ngay[0]]

    for i in range(1, len(danh_sach_ngay)):
        ngay_dang_xet = danh_sach_ngay[i]
        ngay_truoc_do = nhom_hien_tai[-1]  
        ket_qua_kiem_tra = []
        
        for khoa_chi_so, nguong_sai_so in cau_hinh_nguong.items():
            gia_tri_hien_tai = du_lieu_tong_hop[ngay_dang_xet].get(khoa_chi_so)
            gia_tri_truoc_do = du_lieu_tong_hop[ngay_truoc_do].get(khoa_chi_so)
            
            if gia_tri_hien_tai is not None and gia_tri_truoc_do is not None:
                sai_so = abs(gia_tri_hien_tai - gia_tri_truoc_do)
                vuot = sai_so > nguong_sai_so
                ket_qua_kiem_tra.append(vuot)

        if len(ket_qua_kiem_tra) == len(cau_hinh_nguong) and all(ket_qua_kiem_tra):
            danh_sach_cac_gd.append(nhom_hien_tai)
            nhom_hien_tai = [ngay_dang_xet]
        else:
            nhom_hien_tai.append(ngay_dang_xet)

    danh_sach_cac_gd.append(nhom_hien_tai)
    return danh_sach_cac_gd

def ve_bieu_do_dong_thoi(du_lieu_tong_hop, danh_sach_gd, chi_so_chon):
    ngay_co_so = sorted(du_lieu_tong_hop.keys())
    if not ngay_co_so or not chi_so_chon: 
        return

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
                if ngay == gd[0] and idx > 0:
                    ranh_gioi_gd.append(i + 1)
                break

    so_luong_tang = len(chi_so_chon)
    
    # ĐIỀU CHỈNH KÍCH THƯỚC Ở ĐÂY: Tăng chiều rộng cơ sở và hệ số chiều rộng, tăng chiều cao mỗi tầng lên 5
    chieu_rong = max(16, len(ngay_co_so) * 0.8)
    fig, axes = plt.subplots(so_luong_tang, 1, figsize=(chieu_rong, 5 * so_luong_tang), sharex=True)
    
    if so_luong_tang == 1:
        axes = [axes]
        
    tieu_de_chinh = f"Biến thiên Đồng thời: {' - '.join(chi_so_chon)}"
    fig.suptitle(tieu_de_chinh, fontsize=18, fontweight='bold', y=0.98) # Tăng font title lên một chút cho cân đối

    def ve_tung_tang(ax, data, title, color_list):
        ax.bar(x_labels, data, color=color_list, alpha=0.85)
        ax.set_ylabel(title, fontweight='bold', fontsize=12) # Tăng font label trục Y
        for i, v in enumerate(data):
            ax.text(x_labels[i], v + (max(data)*0.02), f" {v:.2f}", ha='center', va='bottom', fontsize=10, rotation=45) # Tăng font số liệu
        for rg in ranh_gioi_gd:
            ax.axvline(x=rg - 0.5, color='gray', linestyle='--', alpha=0.7)
        ax.grid(axis='y', linestyle=':', alpha=0.5)
        ax.set_ylim(0, max(data) * 1.25 if max(data) > 0 else 1)

    for idx, ten_chi_so in enumerate(chi_so_chon):
        data, title = map_data[ten_chi_so]
        ve_tung_tang(axes[idx], data, title, mau_cot)

    axes[-1].set_xticks(x_labels)
    axes[-1].set_xticklabels(x_labels, fontsize=11)
    axes[-1].set_xlabel("Số thứ tự Ngày", fontweight='bold', fontsize=12)

    plt.tight_layout()
    plt.subplots_adjust(top=0.92 if so_luong_tang > 1 else 0.88)
    st.pyplot(fig)

# --- 3. GIAO DIỆN CHÍNH ---
with st.sidebar:
    st.header("📂 Dữ liệu & Cấu hình")
    tep_nho_giot = st.file_uploader("Tải file Nhỏ giọt", type=['json'], accept_multiple_files=True)
    tep_cham_phan = st.file_uploader("Tải file Châm phân", type=['json'], accept_multiple_files=True)
    
    st.divider()
    st.subheader("📊 Chọn chỉ số phân tích")
    danh_sach_chi_so = ["Lần tưới", "TBEC", "EC Yêu cầu"]
    chi_so_chon = st.multiselect("Chỉ số cần xét", danh_sach_chi_so, default=danh_sach_chi_so)

    st.divider()
    st.subheader("⚙️ Ngưỡng ngắt GD (Đồng thời)")
    ss_lan = st.number_input("Sai số Lần tưới", value=GIATRI_GOC["LAN_TUOI"], step=0.1)
    ss_tbec = st.number_input("Sai số TBEC", value=GIATRI_GOC["TBEC"], step=0.1)
    ss_req = st.number_input("Sai số EC Req", value=GIATRI_GOC["EC_REQ"], step=0.1)

if tep_nho_giot:
    du_lieu_tho_ng = []
    for t in tep_nho_giot: du_lieu_tho_ng.extend(json.load(t))
    stt_list = sorted(list(set(str(d.get('STT')) for d in du_lieu_tho_ng if d.get('STT'))))
    khu_vuc = st.sidebar.selectbox("🎯 Chọn khu vực", stt_list)

    thong_ke_ngay = {}
    data_kv = sorted([d for d in du_lieu_tho_ng if str(d.get('STT')) == khu_vuc], key=lambda x: x['Thời gian'])
    for i in range(len(data_kv)-1):
        if data_kv[i].get('Trạng thái') == "Bật" and data_kv[i+1].get('Trạng thái') == "Tắt":
            t1 = datetime.strptime(data_kv[i]['Thời gian'], "%Y-%m-%d %H-%M-%S")
            t2 = datetime.strptime(data_kv[i+1]['Thời gian'], "%Y-%m-%d %H-%M-%S")
            if GIATRI_GOC["GIAY_MIN"] <= (t2 - t1).total_seconds() <= GIATRI_GOC["GIAY_MAX"]:
                d_str = t1.strftime("%Y-%m-%d")
                thong_ke_ngay[d_str] = thong_ke_ngay.get(d_str, 0) + 1

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
            
            du_lieu_tong_hop[n] = {
                'so_lan_tuoi': thong_ke_ngay[n],
                'tbec': float(f"{raw_tbec:.2f}"),
                'ecreq': float(f"{raw_req:.2f}")
            }

        if len(chi_so_chon) == 0:
            st.warning("⚠️ Vui lòng chọn ít nhất 1 chỉ số ở thanh bên trái để phân tích.")
        else:
            nguong_ngat = {}
            if "Lần tưới" in chi_so_chon: nguong_ngat['so_lan_tuoi'] = ss_lan
            if "TBEC" in chi_so_chon: nguong_ngat['tbec'] = ss_tbec
            if "EC Yêu cầu" in chi_so_chon: nguong_ngat['ecreq'] = ss_req

            ds_giai_doan = chia_giai_doan_bien_thien_dong_thoi(ngay_vu, du_lieu_tong_hop, nguong_ngat)

            st.write(f"### Kết quả phân tích: {len(ds_giai_doan)} giai đoạn")
            
            ve_bieu_do_dong_thoi(du_lieu_tong_hop, ds_giai_doan, chi_so_chon)

            st.divider()
            st.write("### Chi tiết số liệu")
            bang_hien_thi = []
            dem_ngay = 1
            for i, gd in enumerate(ds_giai_doan):
                for n in gd:
                    bang_hien_thi.append({
                        "STT Ngày": dem_ngay,
                        "Giai đoạn": i + 1,
                        "Ngày": n,
                        "Số lần tưới": int(du_lieu_tong_hop[n]['so_lan_tuoi']),
                        "TBEC": f"{du_lieu_tong_hop[n]['tbec']:.2f}",
                        "EC Yêu cầu": f"{du_lieu_tong_hop[n]['ecreq']:.2f}"
                    })
                    dem_ngay += 1
            st.table(bang_hien_thi)
else:
    st.info("👋 Vui lòng tải dữ liệu.")
