import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# --- 1. CẤU HÌNH HẰNG SỐ (TỪ CODE GỐC CỦA BẠN) ---
MIN_DURATION_SECONDS = 20
THOI_GIAN_TOI_DA_GIAY = 3600
MIN_PUMP_PER_DAY = 5
MAX_GAP_DAYS = 2
MIN_SEASON_DURATION = 7
NGUONG_BIEN_DONG_TINH = 2.5 # Cho Cách 1
NGAY_TOI_THIEU_GD = 3

# Ngưỡng cho Châm phân (Đã chốt)
NGUONG_TBEC = 8.0
NGUONG_EC_REQ = 5.0

st.set_page_config(page_title="Hệ thống Phân tích Tưới & Dinh dưỡng", layout="wide")

# --- 2. HÀM VẼ BIỂU ĐỒ (GIỮ NGUYÊN LOGIC ĐA SẮC CỦA BẠN) ---
def ve_bieu_do_ngang_da_sac(du_lieu_bieu_do, danh_sach_gd, tieu_de):
    dates = sorted(du_lieu_bieu_do.keys(), reverse=True)
    counts_visual = [du_lieu_bieu_do[d].get('count_visual', du_lieu_bieu_do[d].get('count', 0)) for d in dates]
    counts_real = [du_lieu_bieu_do[d].get('count', 0) for d in dates]
    
    palette = ['#2E7D32', '#1565C0', '#C62828', '#AD1457', '#6A1B9A', '#0277BD', '#00695C', '#EF6C00', '#D84315', '#4E342E']
    bar_colors = []
    for d in dates:
        color = palette[0]
        for idx, gd in enumerate(danh_sach_gd):
            if d in gd:
                color = palette[idx % len(palette)]
                break
        bar_colors.append(color)

    chart_height = min(15, max(5, len(dates) * 0.4))
    fig, ax = plt.subplots(figsize=(10, chart_height))
    ax.barh(dates, counts_visual, color=bar_colors, alpha=0.8)
    ax.axvline(x=MIN_PUMP_PER_DAY, color='red', linestyle='--', alpha=0.5)
    ax.set_title(tieu_de, fontsize=12, fontweight='bold')
    
    for i, (v_vis, v_real) in enumerate(zip(counts_visual, counts_real)):
        ax.text(v_vis + 0.2, i, f"{v_real}", va='center', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    st.pyplot(fig)

# --- 3. LOGIC CHIA GIAI ĐOẠN (DÙNG CHUNG CHO CÁC CÁCH) ---
def chia_giai_doan_tong_quat(ngay_list, data, key, nguong):
    danh_sach_gd = []
    if not ngay_list: return danh_sach_gd
    
    nhom_ht = [ngay_list[0]]
    for i in range(1, len(ngay_list)):
        val_ht = data[ngay_list[i]][key]
        avg_nhom = np.mean([data[d][key] for d in nhom_ht])
        
        sai_so = abs(val_ht - avg_nhom)
        # Ngắt nếu vượt ngưỡng (hoặc vượt gấp 3 lần ngưỡng thì ngắt luôn)
        if (sai_so > nguong and len(nhom_ht) >= NGAY_TOI_THIEU_GD) or (sai_so > nguong * 3):
            danh_sach_gd.append(nhom_ht)
            nhom_ht = [ngay_list[i]]
        else:
            nhom_ht.append(ngay_list[i])
    danh_sach_gd.append(nhom_ht)
    return danh_sach_gd

# --- 4. GIAO DIỆN CHÍNH ---
with st.sidebar:
    st.header("📂 Tải tệp dữ liệu")
    files_nho_giot = st.file_uploader("1. File Nhỏ giọt (Lấy mùa vụ làm gốc)", type=['json'], accept_multiple_files=True)
    files_cham_phan = st.file_uploader("2. File Châm phân", type=['json'], accept_multiple_files=True)

st.title("📊 Phân tích Giai đoạn Mùa vụ")

# Kiểm tra file nhỏ giọt
if files_nho_giot:
    data_ng = []
    for f in files_nho_giot:
        content = json.load(f)
        if isinstance(content, list): data_ng.extend(content)
    
    stt_list = sorted(list(set(str(d.get('STT')) for d in data_ng if d.get('STT'))))
    khu_vuc = st.sidebar.selectbox("🎯 Chọn khu vực (STT):", stt_list)

    # --- BƯỚC 1: XÁC ĐỊNH MÙA VỤ ---
    fmt = "%Y-%m-%d %H-%M-%S"
    daily_raw_ng = {}
    du_lieu_khu = sorted([d for d in data_ng if str(d.get('STT')) == khu_vuc],
                        key=lambda x: datetime.strptime(x['Thời gian'], fmt))

    for i in range(len(du_lieu_khu) - 1):
        h1, h2 = du_lieu_khu[i], du_lieu_khu[i+1]
        if h1.get('Trạng thái') == "Bật" and h2.get('Trạng thái') == "Tắt":
            t1, t2 = datetime.strptime(h1['Thời gian'], fmt), datetime.strptime(h2['Thời gian'], fmt)
            dur = (t2 - t1).total_seconds()
            if MIN_DURATION_SECONDS <= dur <= THOI_GIAN_TOI_DA_GIAY:
                d_str = t1.strftime("%Y-%m-%d")
                if d_str not in daily_raw_ng: daily_raw_ng[d_str] = {'count': 0, 'total_time': 0}
                daily_raw_ng[d_str]['count'] += 1
                daily_raw_ng[d_str]['total_time'] += dur

    ngay_hop_le = sorted([datetime.strptime(n, "%Y-%m-%d").date() 
                         for n, c in daily_raw_ng.items() if c['count'] >= MIN_PUMP_PER_DAY])
    
    if ngay_hop_le:
        danh_sach_vu = []
        bat_dau = ngay_hop_le[0]
        for i in range(1, len(ngay_hop_le)):
            if (ngay_hop_le[i] - ngay_hop_le[i-1]).days > MAX_GAP_DAYS:
                if (ngay_hop_le[i-1] - bat_dau).days + 1 >= MIN_SEASON_DURATION:
                    danh_sach_vu.append({'start': bat_dau, 'end': ngay_hop_le[i-1]})
                bat_dau = ngay_hop_le[i]
        danh_sach_vu.append({'start': bat_dau, 'end': ngay_hop_le[-1]})

        options_vu = [f"Vụ {i+1}: {v['start']} -> {v['end']}" for i, v in enumerate(danh_sach_vu)]
        vu_chon_label = st.selectbox("📅 Chọn mùa vụ:", options_vu)
        vu_ht = danh_sach_vu[options_vu.index(vu_chon_label)]

        # --- BƯỚC 2: CHỌN CÁCH CHIA (DẠNG CHECKBOX) ---
        st.markdown("### 🛠 Chọn phương thức phân chia giai đoạn")
        c1, c2, c3 = st.columns(3)
        with c1: check_c1 = st.checkbox("Cách 1: Theo Lần tưới", value=True)
        with c2: check_c2 = st.checkbox("Cách 2: Theo TBEC")
        with c3: check_c3 = st.checkbox("Cách 3: Theo EC Yêu cầu")

        # --- BƯỚC 3: HIỂN THỊ DỮ LIỆU ---
        
        # CÁCH 1: LỊCH TƯỚI
        if check_c1:
            st.divider()
            st.subheader("💧 Cách 1: Phân chia theo Tần suất tưới (Nhỏ giọt)")
            ngay_trong_vu = sorted([d for d in daily_raw_ng 
                                   if vu_ht['start'] <= datetime.strptime(d, "%Y-%m-%d").date() <= vu_ht['end']])
            ds_gd_c1 = chia_giai_doan_tong_quat(ngay_trong_vu, daily_raw_ng, 'count', NGUONG_BIEN_DONG_TINH)
            
            # Tạo dữ liệu visual để biểu đồ đẹp (giống code cũ của bạn)
            stats_visual = {}
            for gd in ds_gd_c1:
                avg_val = round(sum(daily_raw_ng[d]['count'] for d in gd) / len(gd))
                for d in gd:
                    stats_visual[d] = {'count': daily_raw_ng[d]['count'], 'count_visual': avg_val}
            
            ve_bieu_do_ngang_da_sac(stats_visual, ds_gd_c1, "Biểu đồ giai đoạn dựa trên lần tưới")

        # CÁCH 2 & 3: CHÂM PHÂN
        if (check_c2 or check_c3):
            if not files_cham_phan:
                st.warning("⚠️ Bạn chưa tải file Châm phân để thực hiện Cách 2 hoặc Cách 3.")
            else:
                data_cp = []
                for f in files_cham_phan:
                    content = json.load(f)
                    if isinstance(content, list): data_cp.extend(content)
                
                # Lọc dữ liệu châm phân theo mùa vụ
                stats_cp = {}
                for item in data_cp:
                    if str(item.get('STT')) != khu_vuc: continue
                    dt_obj = datetime.strptime(item['Thời gian'], fmt)
                    if vu_ht['start'] <= dt_obj.date() <= vu_ht['end']:
                        d_str = dt_obj.strftime("%Y-%m-%d")
                        if d_str not in stats_cp: stats_cp[d_str] = {'tbec_l': [], 'req_l': []}
                        stats_cp[d_str]['tbec_l'].append(float(str(item.get('TBEC',0)).replace(',','.')))
                        stats_cp[d_str]['req_l'].append(float(str(item.get('EC yêu cầu',0)).replace(',','.')))
                
                daily_cp = {d: {'tbec': np.mean(v['tbec_l']), 'ecreq': np.mean(v['req_l'])} for d, v in stats_cp.items()}
                ngay_cp_sorted = sorted(daily_cp.keys())

                if check_c2:
                    st.divider()
                    st.subheader("🧪 Cách 2: Phân chia theo TBEC (Thực tế)")
                    ds_gd_c2 = chia_giai_doan_tong_quat(ngay_cp_sorted, daily_cp, 'tbec', NGUONG_TBEC)
                    # Vẽ biểu đồ TBEC (dùng giá trị thực tế)
                    ve_bieu_do_ngang_da_sac(daily_cp, ds_gd_c2, "Biểu đồ giai đoạn dựa trên TBEC")

                if check_c3:
                    st.divider()
                    st.subheader("📋 Cách 3: Phân chia theo EC Yêu cầu (Cài đặt)")
                    ds_gd_c3 = chia_giai_doan_tong_quat(ngay_cp_sorted, daily_cp, 'ecreq', NGUONG_EC_REQ)
                    ve_bieu_do_ngang_da_sac(daily_cp, ds_gd_c3, "Biểu đồ giai đoạn dựa trên EC Yêu cầu")
    else:
        st.error("Không tìm thấy mùa vụ hợp lệ trong file nhỏ giọt.")
else:
    st.info("👋 Chào mừng! Hãy tải file Nhỏ giọt ở thanh bên để bắt đầu.")
