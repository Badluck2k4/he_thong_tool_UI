import streamlit as st
import json
import matplotlib.pyplot as plt
from datetime import datetime

# --- 1. CẤU HÌNH HẰNG SỐ ---
MIN_DURATION_SECONDS = 20
THOI_GIAN_TOI_DA_GIAY = 3600
MIN_PUMP_PER_DAY = 5       
SO_LAN_TOI_DA_NGAY = 50       
MAX_GAP_DAYS = 2           
MIN_SEASON_DURATION = 7    

# Tối ưu ngưỡng biến động theo yêu cầu (2-3 lần)
NGUONG_BIEN_DONG_TINH = 2.5   
NGAY_TOI_THIEU_GD = 3         
MAX_GIAI_DOAN = 20

st.set_page_config(page_title="Hệ thống Phân tích Tưới", layout="wide")

# --- 2. CSS ÉP MÀU CHỈ SỐ (METRIC) ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #A0A0A0 !important; }
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 15px !important;
        border-radius: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIC CHIA GIAI ĐOẠN & LÀM MỊN & TẠO ĐỘ LỆCH ẢO ---
def thuc_thi_chia_va_lam_min(ngay_sap_xep, daily_stats):
    danh_sach_gd = []
    if not ngay_sap_xep: return danh_sach_gd, daily_stats

    # Bước 1: Chia nhóm dựa trên biến động thực tế
    tap_hop_ngay = [ngay_sap_xep[0]]
    for i in range(1, len(ngay_sap_xep)):
        ngay_hien_tai = ngay_sap_xep[i]
        so_lan_hien_tai = daily_stats[ngay_hien_tai]['count']
        trung_binh_nhom = sum(daily_stats[d]['count'] for d in tap_hop_ngay) / len(tap_hop_ngay)
        
        if abs(so_lan_hien_tai - trung_binh_nhom) > NGUONG_BIEN_DONG_TINH and len(tap_hop_ngay) >= NGAY_TOI_THIEU_GD:
            danh_sach_gd.append(tap_hop_ngay)
            tap_hop_ngay = [ngay_hien_tai]
        else:
            tap_hop_ngay.append(ngay_hien_tai)
    if tap_hop_ngay: danh_sach_gd.append(tap_hop_ngay)

    # Bước 2: San phẳng dữ liệu và xử lý trùng lặp thị giác
    new_stats = {}
    last_avg_rounded = -1
    
    for i, gd in enumerate(danh_sach_gd):
        avg_raw = sum(daily_stats[d]['count'] for d in gd) / len(gd)
        avg_rounded = round(avg_raw)
        
        # Logic tạo độ lệch ảo: Nếu trùng số lần với giai đoạn trước, lệch 0.3 để phân tách màu
        avg_for_chart = avg_rounded
        if avg_rounded == last_avg_rounded:
            avg_for_chart = avg_rounded + 0.3 
            
        for d in gd:
            new_stats[d] = {
                'count': avg_rounded,           # Số thực tế để hiển thị chữ/bảng
                'count_visual': avg_for_chart,  # Số ảo để vẽ độ dài cột biểu đồ
                'total_time': daily_stats[d]['total_time']
            }
        last_avg_rounded = avg_rounded
            
    return danh_sach_gd, new_stats

# --- 4. HÀM VẼ BIỂU ĐỒ ĐA SẮC NỀN TRẮNG ---
def ve_bieu_do_ngang_da_sac(du_lieu_bieu_do, danh_sach_gd, tieu_de, is_toan_vu=True):
    dates = sorted(du_lieu_bieu_do.keys(), reverse=True) 
    counts_visual = [du_lieu_bieu_do[d]['count_visual'] for d in dates]
    counts_real = [du_lieu_bieu_do[d]['count'] for d in dates]
    
    palette = ['#2E7D32', '#1565C0', '#C62828', '#AD1457', '#6A1B9A', '#0277BD', '#00695C', '#EF6C00', '#D84315', '#4E342E']
    bar_colors = []
    
    for d in dates:
        color_found = palette[0]
        if is_toan_vu:
            for idx, gd in enumerate(danh_sach_gd):
                if d in gd:
                    color_found = palette[idx % len(palette)]
                    break
        bar_colors.append(color_found)

    chart_height = min(15, max(5, len(dates) * 0.38))
    fig, ax = plt.subplots(figsize=(10, chart_height))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    # Vẽ bằng giá trị visual (có độ lệch ảo)
    ax.barh(dates, counts_visual, color=bar_colors, alpha=0.85, edgecolor='white', linewidth=0.5)
    ax.axvline(x=MIN_PUMP_PER_DAY, color='red', linestyle='--', alpha=0.5)
    
    ax.set_title(tieu_de, fontsize=12, fontweight='bold', color='black', pad=15)
    ax.tick_params(axis='both', labelsize=10, colors='black')
    for spine in ax.spines.values(): spine.set_edgecolor('#333333')
    
    # Hiển thị số thực (số nguyên) trên đầu cột
    for i, (v_vis, v_real) in enumerate(zip(counts_visual, counts_real)):
        ax.text(v_vis + 0.5, i, f"{v_real}", color='black', va='center', fontsize=9, fontweight='bold')

    plt.tight_layout()
    st.pyplot(fig)

# --- 5. XỬ LÝ DỮ LIỆU TỔNG HỢP ---
def thuc_thi_tong_hop(data_tong_hop, kv_id):
    stt_s = str(kv_id)
    fmt = "%Y-%m-%d %H-%M-%S"
    daily_raw = {} 
    
    # Xử lý log tắt/mở
    du_lieu_khu = sorted([d for d in data_tong_hop if d.get('STT') == stt_s],
                        key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    for i in range(len(du_lieu_khu) - 1):
        h1, h2 = du_lieu_khu[i], du_lieu_khu[i+1]
        if h1.get('Trạng thái') == "Bật" and h2.get('Trạng thái') == "Tắt":
            try:
                t1, t2 = datetime.strptime(h1['Thời gian'], fmt), datetime.strptime(h2['Thời gian'], fmt)
                dur = (t2 - t1).total_seconds()
                if MIN_DURATION_SECONDS <= dur <= THOI_GIAN_TOI_DA_GIAY:
                    d_str = t1.strftime("%Y-%m-%d")
                    if d_str not in daily_raw: daily_raw[d_str] = {'count': 0, 'total_time': 0}
                    daily_raw[d_str]['count'] += 1
                    daily_raw[d_str]['total_time'] += dur
            except: continue

    ngay_loc = sorted([datetime.strptime(n, "%Y-%m-%d").date() for n, info in daily_raw.items() 
                      if MIN_PUMP_PER_DAY <= info['count'] <= SO_LAN_TOI_DA_NGAY])
    
    if not ngay_loc: return st.warning("Dữ liệu không đạt ngưỡng lọc.")

    # Phân vụ
    danh_sach_vu = []
    b_idx = 0
    for i in range(1, len(ngay_loc)):
        if (ngay_loc[i] - ngay_loc[i-1]).days > MAX_GAP_DAYS:
            if (ngay_loc[i-1] - ngay_loc[b_idx]).days + 1 >= MIN_SEASON_DURATION:
                s = {n.strftime("%Y-%m-%d"): daily_raw[n.strftime("%Y-%m-%d")] for n in ngay_loc[b_idx:i]}
                danh_sach_vu.append({'start': ngay_loc[b_idx], 'end': ngay_loc[i-1], 'stats': s})
            b_idx = i
    s_end = {n.strftime("%Y-%m-%d"): daily_raw[n.strftime("%Y-%m-%d")] for n in ngay_loc[b_idx:]}
    danh_sach_vu.append({'start': ngay_loc[b_idx], 'end': ngay_loc[-1], 'stats': s_end})

    # UI Chọn vụ
    opt = [f"Vụ {i+1}: {v['start']} -> {v['end']}" for i, v in enumerate(danh_sach_vu)]
    v_chon = st.selectbox("📅 Chọn mùa vụ cần xem:", opt)
    vu_ht = danh_sach_vu[opt.index(v_chon)]
    
    # Chia giai đoạn & Làm mịn
    ds_gd, stats_smooth = thuc_thi_chia_va_lam_min(sorted(vu_ht['stats'].keys()), vu_ht['stats'])

    # Sidebar chọn giai đoạn
    st.sidebar.markdown("### 🔍 Phạm vi dữ liệu")
    che_do = st.sidebar.radio("Chọn giai đoạn:", ["Toàn mùa vụ"] + [f"Giai đoạn {i+1}" for i in range(len(ds_gd))])

    if che_do == "Toàn mùa vụ":
        hien_thi = stats_smooth
        tieu_de = f"BÁO CÁO TỔNG QUAN {v_chon.split(':')[0]}"
        is_toan = True
    else:
        g_idx = int(che_do.split()[-1]) - 1
        hien_thi = {d: stats_smooth[d] for d in ds_gd[g_idx]}
        tieu_de = f"CHI TIẾT {che_do.upper()}"
        is_toan = False

    # Layout Dashboard
    col1, col2 = st.columns([6, 4], gap="large")
    with col1:
        st.subheader(tieu_de)
        m1, m2 = st.columns(2)
        m1.metric("Số ngày", f"{len(hien_thi)} ngày")
        m2.metric("Tổng lần tưới", f"{sum(i['count'] for i in hien_thi.values())} lần")
        ve_bieu_do_ngang_da_sac(hien_thi, ds_gd, "Tần suất tưới trung bình theo giai đoạn", is_toan)

    with col2:
        st.markdown("### 📅 Nhật ký tưới chi tiết")
        st.write("---")
        for n in sorted(hien_thi.keys(), reverse=True):
            raw = vu_ht['stats'][n] # Hiện số gốc để đối chiếu
            st.write(f"**{n}** | ✅ `{raw['count']} lần` | ⏱️ {int(raw['total_time']//60)}p {int(raw['total_time']%60)}s")

# --- KHỞI CHẠY ---
st.sidebar.title("💧 Cấu hình")
FILES = st.sidebar.file_uploader("Tải file JSON", type=['json'], accept_multiple_files=True)

if FILES:
    full_data = []
    for f in FILES:
        content = json.load(f)
        if isinstance(content, list): full_data.extend(content)
    
    if full_data:
        k_list = sorted(list(set(str(d.get('STT')) for d in full_data if d.get('STT'))))
        khu_vuc = st.sidebar.selectbox("🎯 Chọn khu vực:", k_list)
        thuc_thi_tong_hop(full_data, khu_vuc)
else:
    st.title("💧 Hệ thống Phân tích Mùa vụ & Giai đoạn")
    st.info("Vui lòng tải tệp dữ liệu JSON ở thanh bên để bắt đầu phân tích.")
