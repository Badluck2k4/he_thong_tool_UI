import streamlit as st
import json
from datetime import datetime

st.set_page_config(page_title="Tối ưu Phân chia Mùa vụ", layout="wide")

def get_optimized_seasons(all_data, id_tuoi, freq_step=5, max_allowed=40):
    fmt = "%Y-%m-%d %H-%M-%S"
    # 1. Lấy dữ liệu tưới và đếm số lần theo ngày
    data_tuoi = [d for d in all_data if str(d.get('STT')) == str(id_tuoi)]
    if not data_tuoi: return []

    daily_counts = {}
    for d in data_tuoi:
        dt = datetime.strptime(d['Thời gian'], fmt).date()
        daily_counts[dt] = daily_counts.get(dt, 0) + 1
    
    sorted_days = sorted(daily_counts.keys())
    seasons = []
    if not sorted_days: return []

    # 2. Bắt đầu gom nhóm
    current_start = sorted_days[0]
    # Lọc nhiễu: Nếu số lần tưới > max_allowed, đưa về giá trị trần hoặc bỏ qua lỗi
    def get_clean_val(d):
        val = daily_counts[d]
        return val if val <= max_allowed else max_allowed

    group_val = get_clean_val(current_start)
    
    for i in range(1, len(sorted_days)):
        curr_d = sorted_days[i]
        prev_d = sorted_days[i-1]
        curr_val = get_clean_val(curr_d)
        
        # ĐIỀU KIỆN GỘP: 
        # - Số lần tưới chênh lệch không quá freq_step (ví dụ: 5 lần)
        # - Không bị ngắt quãng quá 3 ngày
        is_same_phase = abs(curr_val - group_val) <= freq_step and (curr_d - prev_d).days <= 3
        
        if not is_same_phase:
            # Chốt giai đoạn cũ
            seasons.append({
                "start": current_start,
                "end": prev_d,
                "avg_freq": group_val
            })
            # Bắt đầu giai đoạn mới
            current_start = curr_d
            group_val = curr_val
            
    # Thêm giai đoạn cuối
    seasons.append({
        "start": current_start,
        "end": sorted_days[-1],
        "avg_freq": group_val
    })
    return seasons

# --- GIAO DIỆN ---
st.sidebar.header("Cấu hình Tối ưu")
uploaded_files = st.sidebar.file_uploader("Tải file JSON", type=["json"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for f in uploaded_files:
        content = json.load(f)
        all_data.extend(content) if isinstance(content, list) else all_data.append(content)

    ids = sorted(list(set(str(d.get('STT')) for d in all_data if 'STT' in d)))
    id_tuoi = st.sidebar.selectbox("STT File Nhỏ giọt", ids)
    
    # Hai thông số quan trọng để giảm số giai đoạn
    freq_step = st.sidebar.slider("Độ lệch gộp (Số lần)", 2, 15, 8) 
    max_limit = st.sidebar.number_input("Giới hạn số lần tưới tối đa/ngày (Lọc nhiễu)", value=35)

    results = get_optimized_seasons(all_data, id_tuoi, freq_step, max_limit)

    if results:
        st.subheader(f"Bảng chia mùa vụ rút gọn (Tổng cộng: {len(results)} giai đoạn)")
        
        header = "| GĐ | Ngày bắt đầu | Ngày kết thúc | Tần suất trung bình |\n|---|---|---|---|\n"
        rows = ""
        for i, r in enumerate(results):
            rows += f"| {i+1} | {r['start']} | {r['end']} | ~{r['avg_freq']} lần/ngày |\n"
            
        st.markdown(header + rows)
