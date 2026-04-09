import streamlit as st
import json
from datetime import datetime

st.set_page_config(page_title="Hệ thống Phân tích EC", layout="wide")

# --- 1. LOGIC CHIA GIAI ĐOẠN (Dùng List/Dict thuần) ---
def get_seasons(data, mode, freq_threshold=3):
    fmt = "%Y-%m-%d %H-%M-%S"
    if not data: return []
    
    # Sắp xếp dữ liệu theo thời gian
    data = sorted(data, key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    
    # Tính tần suất cho chế độ Biến động Tần suất
    daily_counts = {}
    for d in data:
        dt = datetime.strptime(d['Thời gian'], fmt).date()
        daily_counts[dt] = daily_counts.get(dt, 0) + 1

    seasons = []
    current_batch = [data[0]]

    for i in range(1, len(data)):
        prev, curr = data[i-1], data[i]
        t_p = datetime.strptime(prev['Thời gian'], fmt)
        t_c = datetime.strptime(curr['Thời gian'], fmt)
        
        is_break = False
        if mode == "Biến động Tần suất":
            if abs(daily_counts[t_c.date()] - daily_counts[t_p.date()]) >= freq_threshold:
                is_break = True
            elif (t_c - t_p).days > 2: is_break = True
        elif mode == "EC Kế hoạch":
            if curr.get("EC yêu cầu") != prev.get("EC yêu cầu"): is_break = True
        elif mode == "EC Thực tế":
            v_p = float(prev.get('TBEC', 0))
            v_c = float(curr.get('TBEC', 0))
            if abs(v_c - v_p) > 30: is_break = True

        if is_break:
            seasons.append(current_batch)
            current_batch = [curr]
        else:
            current_batch.append(curr)
    
    seasons.append(current_batch)
    return seasons

# --- 2. GIAO DIỆN CHÍNH ---
st.title("📊 Kết quả Phân tích EC (Xử lý List thuần)")

uploaded_files = st.sidebar.file_uploader("Tải các file JSON", type=["json"], accept_multiple_files=True)

all_data = []
if uploaded_files:
    for f in uploaded_files:
        try:
            content = json.load(f)
            if isinstance(content, list): all_data.extend(content)
            else: all_data.append(content)
        except Exception as e:
            st.sidebar.error(f"Lỗi đọc file {f.name}: {e}")

    if all_data:
        # Tự động lọc các STT có dữ liệu TBEC để tránh màn hình trống
        ids_with_ec = sorted(list(set(str(d.get('STT')) for d in all_data if 'TBEC' in d)))
        
        if not ids_with_ec:
            st.warning("Không tìm thấy thiết bị nào có dữ liệu EC (trường TBEC).")
        else:
            with st.sidebar:
                st.success(f"Đã nhận {len(all_data)} bản ghi.")
                mode = st.selectbox("Cách chia giai đoạn", ["Biến động Tần suất", "EC Kế hoạch", "EC Thực tế"])
                selected_id = st.selectbox("Chọn STT Máy châm phân", ids_with_ec)
                threshold = st.slider("Ngưỡng lệch tần suất", 1, 10, 3)

            # Lọc dữ liệu theo STT được chọn
            filtered = [d for d in all_data if str(d.get('STT')) == selected_id]
            
            if filtered:
                seasons = get_seasons(filtered, mode, threshold)
                
                # Hiển thị tiêu đề
                st.subheader(f"Dữ liệu chia theo: {mode}")
                
                # Tạo header cho bảng (Dùng Markdown thay cho st.table/pandas)
                header = "| GĐ | Bắt đầu | Kết thúc | Số bản ghi | EC Yêu cầu | TBEC Thực tế | Độ lệch |\n"
                header += "|---|---|---|---|---|---|---|\n"
                
                rows = ""
                for idx, group in enumerate(seasons):
                    reals = [float(d.get('TBEC', 0)) for d in group]
                    targets = [float(d.get('EC yêu cầu', 0)) for d in group]
                    
                    avg_r = sum(reals)/len(reals) if reals else 0
                    avg_t = sum(targets)/len(targets) if targets else 0
                    diff = ((avg_r - avg_t)/avg_t * 100) if avg_t > 0 else 0
                    
                    rows += f"| {idx+1} | {group[0]['Thời gian']} | {group[-1]['Thời gian']} | {len(group)} | {round(avg_t, 1)} | {round(avg_r, 1)} | {round(diff, 1)}% |\n"
                
                st.markdown(header + rows)
    else:
        st.info("Hãy tải file JSON để bắt đầu.")
