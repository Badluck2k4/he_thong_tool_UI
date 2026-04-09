import streamlit as st
import json
from datetime import datetime

st.set_page_config(page_title="Phân chia Giai đoạn Canh tác", layout="wide")

# --- 1. LOGIC PHÂN TÍCH ---
def get_seasons_logic(all_data, mode, id_tuoi, id_cham_phan, thresholds):
    fmt = "%Y-%m-%d %H-%M-%S"
    
    # Tách dữ liệu theo vai trò
    data_tuoi = sorted([d for d in all_data if str(d.get('STT')) == str(id_tuoi)], 
                       key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    data_cp = sorted([d for d in all_data if str(d.get('STT')) == str(id_cham_phan)], 
                      key=lambda x: datetime.strptime(x['Thời gian'], fmt))

    seasons = []
    
    # --- CÁCH 1: THEO LỊCH TƯỚI (Chỉ dùng file nhỏ giọt) ---
    if mode == "Theo Lịch tưới":
        if not data_tuoi: return []
        daily_counts = {}
        for d in data_tuoi:
            dt = datetime.strptime(d['Thời gian'], fmt).date()
            daily_counts[dt] = daily_counts.get(dt, 0) + 1
        
        sorted_days = sorted(daily_counts.keys())
        current_batch = [sorted_days[0]]
        
        for i in range(1, len(sorted_days)):
            prev_d, curr_d = sorted_days[i-1], sorted_days[i]
            # Ngắt khi số lần tưới lệch quá ngưỡng (thresholds['tuoi'])
            if abs(daily_counts[curr_d] - daily_counts[prev_d]) >= thresholds['tuoi'] or (curr_d - prev_d).days > 2:
                seasons.append({"start": current_batch[0], "end": current_batch[-1], "info": f"{daily_counts[current_batch[0]]} lần/ngày"})
                current_batch = [curr_d]
            else:
                current_batch.append(curr_d)
        seasons.append({"start": current_batch[0], "end": current_batch[-1], "info": f"{daily_counts[current_batch[0]]} lần/ngày"})

    # --- CÁCH 2 & 3: THEO EC (Chỉ dùng file châm phân) ---
    else:
        if not data_cp: return []
        current_batch = [data_cp[0]]
        attr = "EC yêu cầu" if mode == "Theo EC Yêu cầu" else "TBEC"
        
        for i in range(1, len(data_cp)):
            prev, curr = data_cp[i-1], data_cp[i]
            val_p = float(prev.get(attr, 0))
            val_c = float(curr.get(attr, 0))
            
            # Ngắt khi giá trị EC lệch vượt ngưỡng (thresholds['ec'])
            if abs(val_c - val_p) >= thresholds['ec']:
                seasons.append({"start": current_batch[0]['Thời gian'], "end": prev['Thời gian'], "val": val_p})
                current_batch = [curr]
            else:
                current_batch.append(curr)
        seasons.append({"start": current_batch[0]['Thời gian'], "end": data_cp[-1]['Thời gian'], "val": float(current_batch[0].get(attr, 0))})

    return seasons

# --- 2. GIAO DIỆN ---
st.title("📋 Phân chia Giai đoạn Mùa vụ")

uploaded_files = st.sidebar.file_uploader("Tải 2 file JSON (Nhỏ giọt & Châm phân)", type=["json"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for f in uploaded_files:
        content = json.load(f)
        all_data.extend(content) if isinstance(content, list) else all_data.append(content)

    ids = sorted(list(set(str(d.get('STT')) for d in all_data if 'STT' in d)))
    
    with st.sidebar:
        mode = st.radio("Chọn tiêu chí chia:", ["Theo Lịch tưới", "Theo EC Yêu cầu", "Theo EC Thực tế"])
        id_tuoi = st.selectbox("STT File Nhỏ giọt (Lịch tưới)", ids, index=0)
        id_cp = st.selectbox("STT File Châm phân (EC)", ids, index=min(1, len(ids)-1))
        
        st.divider()
        st.write("**Ngưỡng lọc (Để tránh chia quá nhiều)**")
        t_tuoi = st.slider("Lệch số lần tưới để ngắt GĐ", 1, 10, 3)
        t_ec = st.slider("Lệch đơn vị EC để ngắt GĐ", 10, 100, 40)

    results = get_seasons_logic(all_data, mode, id_tuoi, id_cp, {'tuoi': t_tuoi, 'ec': t_ec})

    if results:
        st.subheader(f"Kết quả chia mùa vụ: {mode}")
        
        if mode == "Theo Lịch tưới":
            header = "| Giai đoạn | Ngày bắt đầu | Ngày kết thúc | Đặc điểm vận hành |\n|---|---|---|---|\n"
            rows = "".join([f"| {i+1} | {r['start']} | {r['end']} | {r['info']} |\n" for i, r in enumerate(results)])
        else:
            label = "Mức EC Yêu cầu" if mode == "Theo EC Yêu cầu" else "Mức TBEC thực tế"
            header = f"| Giai đoạn | Thời điểm bắt đầu | Thời điểm kết thúc | {label} |\n|---|---|---|---|\n"
            rows = "".join([f"| {i+1} | {r['start']} | {r['end']} | {round(r['val'], 1)} |\n" for i, r in enumerate(results)])
            
        st.markdown(header + rows)
    else:
        st.warning("Vui lòng kiểm tra lại STT thiết bị tương ứng với từng file.")
