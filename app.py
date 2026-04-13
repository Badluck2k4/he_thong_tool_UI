import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# --- 1. CẤU HÌNH HẰNG SỐ (GIỮ NGUYÊN VÀ BỔ SUNG) ---
MIN_DURATION_SECONDS = 20
THOI_GIAN_TOI_DA_GIAY = 3600
MIN_PUMP_PER_DAY = 5
MAX_GAP_DAYS = 2
MIN_SEASON_DURATION = 7

# Thông số chia giai đoạn theo yêu cầu mới
NGUONG_TBEC = 8.0
NGUONG_EC_REQ = 5.0
SO_NGAY_MIN_GD = 3

st.set_page_config(page_title="Hệ thống Phân tích Dinh dưỡng & Tưới", layout="wide")

# --- 2. HÀM TIỆN ÍCH PHÁT SINH (VIỆT HÓA) ---
def lam_sach_du_lieu(gia_tri):
    try:
        return float(str(gia_tri).replace(',', '.'))
    except:
        return 0.0

# --- 3. LOGIC CHIA GIAI ĐOẠN (ƯU TIÊN GOM NHÓM SAI SỐ THẤP) ---
def chia_giai_doan_thong_minh(danh_sach_ngay, du_lieu_ngay, kieu_chia):
    nguong = NGUONG_TBEC if kieu_chia == 'tbec' else NGUONG_EC_REQ
    danh_sach_gd = []
    if not danh_sach_ngay: return danh_sach_gd

    nhom_ht = [danh_sach_ngay[0]]
    for i in range(1, len(danh_sach_ngay)):
        ngay_ht = danh_sach_ngay[i]
        val_ht = du_lieu_ngay[ngay_ht][kieu_chia]
        avg_nhom = np.mean([du_lieu_ngay[d][kieu_chia] for d in nhom_ht])
        
        sai_so = abs(val_ht - avg_nhom)
        # Ngắt nếu sai số vượt ngưỡng và đủ ngày, hoặc đột biến gấp 3 lần ngưỡng
        if (sai_so > nguong and len(nhom_ht) >= SO_NGAY_MIN_GD) or (sai_so > nguong * 3):
            danh_sach_gd.append(nhom_ht)
            nhom_ht = [ngay_ht]
        else:
            nhom_ht.append(ngay_ht)
            
    danh_sach_gd.append(nhom_ht)
    return danh_sach_gd

# --- 4. GIAO DIỆN CHÍNH ---
st.title("🌱 Hệ thống Quản lý Mùa vụ & Dinh dưỡng")

with st.sidebar:
    st.header("📂 Nhập dữ liệu")
    file_nho_giot = st.file_uploader("Tải file Nhỏ giọt (Gốc)", type=['json'], accept_multiple_files=True)
    file_cham_phan = st.file_uploader("Tải file Châm phân", type=['json'], accept_multiple_files=True)
    
    st.divider()
    st.header("⚙️ Cấu hình phân tích")
    cach_chia_chon = st.multiselect(
        "Chọn cách chia giai đoạn:",
        ["Cách 1: Lần tưới (Nhỏ giọt)", "Cách 2: TBEC (Châm phân)", "Cách 3: EC Yêu cầu (Châm phân)"],
        default=["Cách 2: TBEC (Châm phân)"]
    )

# --- 5. XỬ LÝ LOGIC TỔNG HỢP ---
if file_nho_giot:
    # Gom dữ liệu nhỏ giọt
    data_ng = []
    for f in file_nho_giot:
        content = json.load(f)
        if isinstance(content, list): data_ng.extend(content)
    
    # Lấy danh sách STT
    stt_list = sorted(list(set(str(d.get('STT')) for d in data_ng if d.get('STT'))))
    khu_vuc_chon = st.sidebar.selectbox("🎯 Chọn khu vực:", stt_list)

    # A. XÁC ĐỊNH MÙA VỤ TỪ FILE NHỎ GIỌT (LÀM GỐC)
    fmt = "%Y-%m-%d %H-%M-%S"
    lich_tuoi_ngay = {}
    du_lieu_khu = sorted([d for d in data_ng if str(d.get('STT')) == khu_vuc_chon],
                        key=lambda x: datetime.strptime(x['Thời gian'], fmt))

    for i in range(len(du_lieu_khu) - 1):
        h1, h2 = du_lieu_khu[i], du_lieu_khu[i+1]
        if h1.get('Trạng thái') == "Bật" and h2.get('Trạng thái') == "Tắt":
            t1, t2 = datetime.strptime(h1['Thời gian'], fmt), datetime.strptime(h2['Thời gian'], fmt)
            dur = (t2 - t1).total_seconds()
            if MIN_DURATION_SECONDS <= dur <= THOI_GIAN_TOI_DA_GIAY:
                d_str = t1.strftime("%Y-%m-%d")
                lich_tuoi_ngay[d_str] = lich_tuoi_ngay.get(d_str, 0) + 1

    ngay_hop_le = sorted([datetime.strptime(n, "%Y-%m-%d").date() 
                         for n, c in lich_tuoi_ngay.items() if c >= MIN_PUMP_PER_DAY])
    
    danh_sach_vu = []
    if ngay_hop_le:
        bat_dau = ngay_hop_le[0]
        for i in range(1, len(ngay_hop_le)):
            if (ngay_hop_le[i] - ngay_hop_le[i-1]).days > MAX_GAP_DAYS:
                if (ngay_hop_le[i-1] - bat_dau).days + 1 >= MIN_SEASON_DURATION:
                    danh_sach_vu.append({'start': bat_dau, 'end': ngay_hop_le[i-1]})
                bat_dau = ngay_hop_le[i]
        danh_sach_vu.append({'start': bat_dau, 'end': ngay_hop_le[-1]})

        # Chọn mùa vụ
        options_vu = [f"Vụ {i+1}: {v['start']} -> {v['end']}" for i, v in enumerate(danh_sach_vu)]
        vu_chon_label = st.selectbox("📅 Chọn mùa vụ phân tích:", options_vu)
        vu_hien_tai = danh_sach_vu[options_vu.index(vu_chon_label)]

        # B. HIỂN THỊ CÁC CÁCH CHIA
        tab_list = st.tabs(cach_chia_chon) if cach_chia_chon else []

        for i, tab in enumerate(tab_list):
            ten_cach = cach_chia_chon[i]
            
            with tab:
                if "Cách 1" in ten_cach:
                    st.info("Logic hiển thị biểu đồ lần tưới (Sử dụng code gốc của bạn)")
                    # Tích hợp hàm vẽ biểu đồ của bạn vào đây...

                elif ("Cách 2" in ten_cach or "Cách 3" in ten_cach) and file_cham_phan:
                    # Xử lý dữ liệu châm phân
                    data_cp = []
                    for f in file_cham_phan:
                        content = json.load(f)
                        if isinstance(content, list): data_cp.extend(content)
                    
                    # Tính trung bình ngày trong khung mùa vụ
                    stats_phan = {}
                    for item in data_cp:
                        if str(item.get('STT')) != khu_vuc_chon: continue
                        ngay_dt = datetime.strptime(item['Thời gian'], fmt).date()
                        if vu_hien_tai['start'] <= ngay_dt <= vu_hien_tai['end']:
                            n_str = ngay_dt.strftime("%Y-%m-%d")
                            if n_str not in stats_phan: stats_phan[n_str] = {'tbec': [], 'ecreq': []}
                            stats_phan[n_str]['tbec'].append(lam_sach_du_lieu(item.get('TBEC', 0)))
                            stats_phan[n_str]['ecreq'].append(lam_sach_du_lieu(item.get('EC yêu cầu', 0)))
                    
                    du_lieu_ngay_cp = {d: {'tbec': np.mean(v['tbec']), 'ecreq': np.mean(v['ecreq'])} 
                                      for d, v in stats_phan.items()}
                    ngay_sap_xep = sorted(du_lieu_ngay_cp.keys())
                    
                    kieu_key = 'tbec' if "Cách 2" in ten_cach else 'ecreq'
                    ds_giai_doan = chia_giai_doan_thong_minh(ngay_sap_xep, du_lieu_ngay_cp, kieu_key)

                    # Hiển thị bảng kết quả
                    st.subheader(f"Phân tích theo {kieu_key.upper()}")
                    col_m1, col_m2 = st.columns(2)
                    col_m1.metric("Tổng giai đoạn", len(ds_giai_doan))
                    col_m2.metric("Số ngày trong vụ", len(ngay_sap_xep))

                    for idx, gd in enumerate(ds_giai_doan):
                        with st.expander(f"Giai đoạn {idx+1}: {gd[0]} đến {gd[-1]} ({len(gd)} ngày)"):
                            val_avg = np.mean([du_lieu_ngay_cp[d][kieu_key] for d in gd])
                            st.write(f"**Giá trị trung bình giai đoạn:** {val_avg:.2f}")
                            st.table([{"Ngày": d, "Giá trị": f"{du_lieu_ngay_cp[d][kieu_key]:.2f}"} for d in gd])
                
                elif ("Cách 2" in ten_cach or "Cách 3" in ten_cach) and not file_cham_phan:
                    st.warning("Vui lòng tải file Châm phân để xem dữ liệu này.")

else:
    st.info("Vui lòng tải ít nhất file Nhỏ giọt để xác định khung mùa vụ.")
