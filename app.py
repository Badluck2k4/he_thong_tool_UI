import streamlit as st
import json
from datetime import datetime

def phan_chia_giai_doan_tinh_gon(all_data, id_tuoi, id_cp, mode, step_tuoi=6, step_ec=40):
    fmt = "%Y-%m-%d %H-%M-%S"
    
    # 1. Xử lý dữ liệu Lịch tưới
    data_tuoi = sorted([d for d in all_data if str(d.get('STT')) == str(id_tuoi)], 
                       key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    
    # 2. Xử lý dữ liệu EC (từ file châm phân)
    data_cp = sorted([d for d in all_data if str(d.get('STT')) == str(id_cp)], 
                      key=lambda x: datetime.strptime(x['Thời gian'], fmt))

    seasons = []

    # --- CHIA THEO LỊCH TƯỚI ---
    if mode == "Theo Lịch tưới":
        daily_counts = {}
        for d in data_tuoi:
            dt = datetime.strptime(d['Thời gian'], fmt).date()
            daily_counts[dt] = daily_counts.get(dt, 0) + 1
        
        sorted_days = sorted(daily_counts.keys())
        if not sorted_days: return []

        curr_start = sorted_days[0]
        curr_val = daily_counts[curr_start]
        
        for i in range(1, len(sorted_days)):
            d_p, d_c = sorted_days[i-1], sorted_days[i]
            v_c = daily_counts[d_c]
            
            # Ngắt khi: Lệch số lần > step_tuoi HOẶC nghỉ > 2 ngày
            if abs(v_c - curr_val) > step_tuoi or (d_c - d_p).days > 2:
                seasons.append({
                    "Bắt đầu": curr_start, 
                    "Kết thúc": d_p, 
                    "Giá trị": f"~{curr_val} lần/ngày"
                })
                curr_start, curr_val = d_c, v_c
        seasons.append({"Bắt đầu": curr_start, "Kết thúc": sorted_days[-1], "Giá trị": f"~{curr_val} lần/ngày"})

    # --- CHIA THEO EC (Thực tế hoặc Yêu cầu) ---
    else:
        if not data_cp: return []
        attr = "EC yêu cầu" if mode == "Theo EC Yêu cầu" else "TBEC"
        curr_start_node = data_cp[0]
        curr_val = float(curr_start_node.get(attr, 0))

        for i in range(1, len(data_cp)):
            prev, curr = data_cp[i-1], data_cp[i]
            v_c = float(curr.get(attr, 0))
            
            # Chỉ ngắt nếu giá trị EC nhảy vọt vượt ngưỡng step_ec
            if abs(v_c - curr_val) >= step_ec:
                seasons.append({
                    "Bắt đầu": curr_start_node['Thời gian'], 
                    "Kết thúc": prev['Thời gian'], 
                    "Giá trị": f"{round(curr_val, 1)} (EC)"
                })
                curr_start_node, curr_val = curr, v_c
        seasons.append({"Bắt đầu": curr_start_node['Thời gian'], "Kết thúc": data_cp[-1]['Thời gian'], "Giá trị": f"{round(curr_val, 1)} (EC)"})

    return seasons

# --- GIAO DIỆN STREAMLIT ---
st.title("Phân chia Mùa vụ & Giai đoạn")
uploaded = st.sidebar.file_uploader("Tải File JSON", accept_multiple_files=True)

if uploaded:
    all_raw = []
    for f in uploaded:
        content = json.load(f)
        all_raw.extend(content) if isinstance(content, list) else all_raw.append(content)

    with st.sidebar:
        mode = st.radio("Chia theo:", ["Theo Lịch tưới", "Theo EC Yêu cầu", "Theo EC Thực tế"])
        id_tuoi = st.text_input("STT Nhỏ giọt", "2")
        id_cp = st.text_input("STT Châm phân", "1")
        st.divider()
        st.write("Cài đặt độ nhạy (Gộp giai đoạn)")
        sens_tuoi = st.slider("Độ lệch lần tưới để tách GĐ", 2, 15, 6)
        sens_ec = st.slider("Độ lệch EC để tách GĐ", 10, 100, 40)

    res = phan_chia_giai_doan_tinh_gon(all_raw, id_tuoi, id_cp, mode, sens_tuoi, sens_ec)

    if res:
        header = "| Giai đoạn | Ngày bắt đầu | Ngày kết thúc | Thông số chính |\n|---|---|---|---|\n"
        rows = "".join([f"| {i+1} | {r['Bắt đầu']} | {r['Kết thúc']} | {r['Giá trị']} |\n" for i, r in enumerate(res)])
        st.markdown(header + rows)
