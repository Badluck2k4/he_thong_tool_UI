import streamlit as st
import json
from datetime import datetime

def get_smart_seasons(all_data, id_tuoi, sensitivity=12, min_days=7, max_cap=35):
    fmt = "%Y-%m-%d %H-%M-%S"
    data_tuoi = [d for d in all_data if str(d.get('STT')) == str(id_tuoi)]
    if not data_tuoi: return []

    # 1. Đếm và Lọc nhiễu ngay từ đầu
    daily_counts = {}
    for d in data_tuoi:
        dt = datetime.strptime(d['Thời gian'], fmt).date()
        daily_counts[dt] = daily_counts.get(dt, 0) + 1
    
    sorted_days = sorted(daily_counts.keys())
    
    # Hàm lấy giá trị sạch (Ép trần nhiễu)
    def clean_v(d):
        v = daily_counts[d]
        return v if v <= max_cap else max_cap

    # 2. Thuật toán Gộp giai đoạn dựa trên Xu hướng
    seasons = []
    if not sorted_days: return []

    curr_start = sorted_days[0]
    # Lấy giá trị trung bình đại diện cho giai đoạn hiện tại
    curr_phase_val = clean_v(curr_start)
    
    for i in range(1, len(sorted_days)):
        d_p, d_c = sorted_days[i-1], sorted_days[i]
        val_c = clean_v(d_c)
        gap = (d_c - d_p).days
        
        # ĐIỀU KIỆN NGẮT CHẶT CHẼ HƠN:
        # Chỉ ngắt nếu lệch quá sensitivity VÀ gap quá 3 ngày 
        # HOẶC sự thay đổi cực lớn (gấp đôi tần suất)
        is_break = (abs(val_c - curr_phase_val) > sensitivity and gap > 1) or gap > 4
        
        if is_break:
            duration = (d_p - curr_start).days + 1
            # Bỏ qua các giai đoạn rác quá ngắn (dưới min_days)
            if duration >= min_days:
                seasons.append({
                    "Bắt đầu": curr_start,
                    "Kết thúc": d_p,
                    "Tần suất": round(curr_phase_val)
                })
                curr_start = d_c
                curr_phase_val = val_c
            else:
                # Nếu quá ngắn, gộp luôn vào giai đoạn sau, cập nhật lại giá trị trung bình
                curr_phase_val = (curr_phase_val + val_c) / 2

    # Giai đoạn cuối cùng
    seasons.append({"Bắt đầu": curr_start, "Kết thúc": sorted_days[-1], "Tần suất": round(curr_phase_val)})
    return seasons

# --- GIAO DIỆN ---
st.title("Phân chia Mùa vụ Thực tế (Lọc nhiễu & Gộp)")
# ... (Phần upload file giữ nguyên) ...

with st.sidebar:
    st.header("Bộ lọc Mùa vụ")
    # Tăng Sensitivity lên để gộp mạnh hơn
    sens = st.slider("Độ nhạy ngắt GĐ (Lệch bao nhiêu lần)", 5, 25, 15)
    min_d = st.slider("Số ngày tối thiểu của 1 vụ", 3, 15, 7)
    cap = st.number_input("Trần số lần tưới (Lọc nhiễu)", value=35)

# Hiển thị kết quả (Markdown Table)
# res = get_smart_seasons(all_raw, "2", sens, min_d, cap)
