import streamlit as st
import json
from datetime import datetime

st.set_page_config(page_title="Phân tích Mùa vụ Logic Nhảy vọt", layout="wide")

def get_jump_seasons(all_data, id_tuoi, jump_threshold=2, sustain_days=3, max_cap=40):
    fmt = "%Y-%m-%d %H-%M-%S"
    data_tuoi = [d for d in all_data if str(d.get('STT')) == str(id_tuoi)]
    if not data_tuoi: return []

    # 1. Thống kê số lần tưới sạch theo ngày
    daily_counts = {}
    for d in data_tuoi:
        try:
            dt = datetime.strptime(d['Thời gian'], fmt).date()
            daily_counts[dt] = daily_counts.get(dt, 0) + 1
        except: continue
    
    sorted_days = sorted(daily_counts.keys())
    if not sorted_days: return []

    def get_val(d):
        v = daily_counts[d]
        return v if v <= max_cap else max_cap

    # 2. Thuật toán dò tìm điểm nhảy vọt liên tiếp
    seasons = []
    curr_start_idx = 0
    n = len(sorted_days)

    while curr_start_idx < n:
        j = curr_start_idx + 1
        found_break = False
        
        while j < n:
            # Kiểm tra gap ngày (nếu nghỉ quá 3 ngày thì ngắt vụ luôn)
            gap = (sorted_days[j] - sorted_days[j-1]).days
            if gap > 3:
                found_break = True
                break

            # Tính trung bình của giai đoạn hiện tại để làm mốc so sánh
            current_group = sorted_days[curr_start_idx:j]
            avg_current = sum(get_val(d) for d in current_group) / len(current_group)
            
            # Kiểm tra xem ngày j có phải điểm nhảy vọt không
            val_j = get_val(sorted_days[j])
            if abs(val_j - avg_current) >= jump_threshold:
                # Kiểm tra xem sự nhảy vọt này có duy trì liên tiếp không
                sustain_count = 0
                for k in range(j, min(j + sustain_days, n)):
                    if abs(get_val(sorted_days[k]) - avg_current) >= (jump_threshold - 1):
                        sustain_count += 1
                
                if sustain_count >= sustain_days: # Nếu duy trì đủ lâu
                    found_break = True
                    break
            j += 1
        
        # Lưu giai đoạn
        end_idx = j - 1
        group = sorted_days[curr_start_idx:j]
        avg_v = sum(get_val(d) for d in group) / len(group)
        
        seasons.append({
            "Bắt đầu": sorted_days[curr_start_idx],
            "Kết thúc": sorted_days[end_idx],
            "Số lần TB": round(avg_v)
        })
        curr_start_idx = j

    return seasons

# --- GIAO DIỆN ---
st.title("📊 Phân chia GĐ theo Logic Nhảy vọt")

uploaded = st.sidebar.file_uploader("Tải file JSON", type=["json"], accept_multiple_files=True)

if uploaded:
    all_data = []
    for f in uploaded:
        content = json.load(f)
        all_data.extend(content) if isinstance(content, list) else all_data.append(content)

    ids = sorted(list(set(str(d.get('STT')) for d in all_data if 'STT' in d)))
    
    with st.sidebar:
        st.header("Cấu hình Logic")
        id_tuoi = st.selectbox("STT Nhỏ giọt", ids, index=ids.index("2") if "2" in ids else 0)
        threshold = st.slider("Độ lệch nhảy vọt (Lần tưới)", 1, 5, 2)
        sustain = st.slider("Số ngày duy trì để tách GĐ", 2, 5, 3)
        cap = st.number_input("Trần lọc nhiễu", value=35)

    res = get_jump_seasons(all_data, id_tuoi, threshold, sustain, cap)

    if res:
        st.subheader(f"Kết quả: {len(res)} giai đoạn")
        table = "| GĐ | Từ ngày | Đến ngày | Số lần TB |\n|---|---|---|---|\n"
        for i, r in enumerate(res):
            table += f"| {i+1} | {r['Bắt đầu']} | {r['Kết thúc']} | ~{r['Số lần TB']} lần/ngày |\n"
        st.markdown(table)
else:
    st.info("👈 Vui lòng tải file để hệ thống bắt đầu gom nhóm.")
