import streamlit as st
import json
import pandas as pd
from datetime import datetime

# --- CẤU HÌNH ---
st.set_page_config(page_title="Lọc dữ liệu EC", layout="wide")

def get_data_seasons(cp_data, mode, freq_threshold=3):
    fmt = "%Y-%m-%d %H-%M-%S"
    if not cp_data: return []
    
    # Sắp xếp theo thời gian
    cp_data = sorted(cp_data, key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    
    # Tính tần suất tưới theo ngày cho chế độ "Lịch tưới"
    daily_counts = {}
    for d in cp_data:
        dt = datetime.strptime(d['Thời gian'], fmt).date()
        daily_counts[dt] = daily_counts.get(dt, 0) + 1

    seasons = []
    current_batch = [cp_data[0]]

    for i in range(1, len(cp_data)):
        prev, curr = cp_data[i-1], cp_data[i]
        t_p = datetime.strptime(prev['Thời gian'], fmt)
        t_c = datetime.strptime(curr['Thời gian'], fmt)
        
        is_break = False
        
        # 1. Lọc theo Biến động tần suất (Thay đổi số lần tưới/ngày)
        if mode == "Biến động Tần suất":
            if abs(daily_counts[t_c.date()] - daily_counts[t_p.date()]) >= freq_threshold:
                is_break = True
            elif (t_c - t_p).days > 2: # Vẫn giữ điều kiện ngắt mùa vụ cơ bản
                is_break = True
                
        # 2. Lọc theo EC Kế hoạch (Thay đổi con số cài đặt)
        elif mode == "EC Kế hoạch":
            if curr.get("EC yêu cầu") != prev.get("EC yêu cầu"):
                is_break = True
                
        # 3. Lọc theo EC Thực tế (Biến động TBEC > 30 đơn vị)
        elif mode == "EC Thực tế":
            if abs(float(curr.get("TBEC", 0)) - float(prev.get("TBEC", 0))) > 30:
                is_break = True

        if is_break:
            seasons.append(current_batch)
            current_batch = [curr]
        else:
            current_batch.append(curr)
            
    seasons.append(current_batch)
    return seasons

# --- GIAO DIỆN ---
uploaded = st.sidebar.file_uploader("Tải file JSON", type=["json"])

if uploaded:
    raw = json.load(uploaded)
    data = raw if isinstance(raw, list) else [raw]
    
    st.sidebar.divider()
    mode = st.sidebar.selectbox("Cách chia giai đoạn", ["Biến động Tần suất", "EC Kế hoạch", "EC Thực tế"])
    ids = sorted(list(set(str(d['STT']) for d in data if 'STT' in d)))
    selected_id = st.sidebar.selectbox("Chọn STT thiết bị", ids)
    
    # Lọc dữ liệu theo STT đã chọn
    filtered_data = [d for d in data if str(d.get('STT')) == selected_id]
    
    if filtered_data:
        results = get_data_seasons(filtered_data, mode)
        
        summary_table = []
        for idx, group in enumerate(results):
            reals = [float(d.get('TBEC', 0)) for d in group]
            targets = [float(d.get('EC yêu cầu', 0)) for d in group]
            
            avg_r = sum(reals)/len(reals)
            avg_t = sum(targets)/len(targets)
            
            summary_table.append({
                "Giai đoạn": idx + 1,
                "Bắt đầu": group[0]['Thời gian'],
                "Kết thúc": group[-1]['Thời gian'],
                "Số bản ghi": len(group),
                "EC Yêu cầu (TB)": round(avg_t, 1),
                "TBEC Thực tế (TB)": round(avg_r, 1),
                "Độ lệch (%)": f"{round(((avg_r - avg_t)/avg_t*100), 1)}%" if avg_t > 0 else "0%"
            })
            
        st.subheader(f"Bảng tổng hợp: Chia theo {mode}")
        st.table(pd.DataFrame(summary_table))
    else:
        st.warning("Không tìm thấy dữ liệu cho STT này.")
