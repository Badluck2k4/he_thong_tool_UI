import streamlit as st
import json
from datetime import datetime

st.set_page_config(page_title="Phân tích Mùa vụ Canh tác", layout="wide")

# --- 1. LOGIC GỘP GIAI ĐOẠN THÔNG MINH ---
def get_smart_seasons(all_data, id_tuoi, sensitivity=15, min_days=7, max_cap=35):
    fmt = "%Y-%m-%d %H-%M-%S"
    # Lọc dữ liệu theo STT nhỏ giọt
    data_tuoi = [d for d in all_data if str(d.get('STT')) == str(id_tuoi)]
    if not data_tuoi: return []

    # Đếm số lần tưới theo ngày
    daily_counts = {}
    for d in data_tuoi:
        dt = datetime.strptime(d['Thời gian'], fmt).date()
        daily_counts[dt] = daily_counts.get(dt, 0) + 1
    
    sorted_days = sorted(daily_counts.keys())
    if not sorted_days: return []

    # Hàm lọc nhiễu
    def get_val(d):
        v = daily_counts[d]
        return v if v <= max_cap else max_cap

    seasons = []
    curr_start = sorted_days[0]
    curr_phase_val = get_val(curr_start)
    
    for i in range(1, len(sorted_days)):
        d_p, d_c = sorted_days[i-1], sorted_days[i]
        val_c = get_val(d_c)
        gap = (d_c - d_p).days
        
        # ĐIỀU KIỆN NGẮT GIAI ĐOẠN:
        # 1. Tần suất lệch quá ngưỡng nhạy (sensitivity)
        # 2. Hoặc có khoảng nghỉ quá 4 ngày (gap > 4)
        if abs(val_c - curr_phase_val) > sensitivity or gap > 4:
            duration = (d_p - curr_start).days + 1
            # Chỉ ghi nhận giai đoạn nếu nó đủ dài (tránh các ngày lẻ tẻ)
            if duration >= min_days:
                seasons.append({
                    "Bắt đầu": curr_start,
                    "Kết thúc": d_p,
                    "Tần suất": round(curr_phase_val)
                })
                curr_start = d_c
                curr_phase_val = val_c
            else:
                # Nếu quá ngắn, tự động gộp vào giá trị trung bình để đi tiếp
                curr_phase_val = (curr_phase_val + val_c) / 2

    # Giai đoạn cuối
    seasons.append({"Bắt đầu": curr_start, "Kết thúc": sorted_days[-1], "Tần suất": round(curr_phase_val)})
    return seasons

# --- 2. GIAO DIỆN NẠP FILE VÀ HIỂN THỊ ---
st.title("📊 Phân chia Giai đoạn Mùa vụ")

# CỔNG NẠP FILE Ở ĐÂY
uploaded_files = st.sidebar.file_uploader(
    "Tải file JSON (Bạn có thể chọn cả 2 file cùng lúc)", 
    type=["json"], 
    accept_multiple_files=True
)

if uploaded_files:
    all_data = []
    for f in uploaded_files:
        try:
            content = json.load(f)
            if isinstance(content, list): all_data.extend(content)
            else: all_data.append(content)
        except:
            st.error(f"Lỗi đọc file {f.name}")

    # Lấy danh sách STT để người dùng chọn
    ids = sorted(list(set(str(d.get('STT')) for d in all_data if 'STT' in d)))
    
    with st.sidebar:
        st.divider()
        st.header("Cài đặt bộ lọc")
        id_tuoi = st.selectbox("Chọn STT Nhỏ giọt", ids)
        
        # Các tham số để bạn ép số giai đoạn về mức 5-10
        sens = st.slider("Độ nhạy lệch tần suất (Nên để cao: 12-18)", 5, 30, 15)
        min_d = st.slider("Số ngày tối thiểu một vụ (Nên để: 7-10)", 3, 20, 7)
        max_v = st.number_input("Trần số lần tưới (Lọc nhiễu)", value=35)

    # Thực hiện phân chia
    results = get_smart_seasons(all_data, id_tuoi, sens, min_d, max_v)

    if results:
        st.subheader(f"Kết quả phân chia (Tổng cộng: {len(results)} giai đoạn)")
        
        # Hiển thị bảng bằng Markdown thuần
        header = "| Giai đoạn | Từ ngày | Đến ngày | Đặc điểm vận hành |\n|---|---|---|---|\n"
        rows = ""
        for i, r in enumerate(results):
            rows += f"| {i+1} | {r['Bắt đầu']} | {r['Kết thúc']} | ~{r['Tần suất']} lần/ngày |\n"
            
        st.markdown(header + rows)
    else:
        st.warning("Không tìm thấy dữ liệu phù hợp để chia giai đoạn.")
else:
    st.info("👈 Hãy tải các file JSON từ thanh bên trái để bắt đầu phân tích.")
