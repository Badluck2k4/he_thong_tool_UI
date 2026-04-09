import streamlit as st
import json
import pandas as pd
from datetime import datetime

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Phân tích Đa File EC", layout="wide")

# --- 2. LOGIC PHÂN TÍCH (Giữ nguyên các hàm get_data_seasons đã tối ưu) ---
def get_data_seasons(all_combined_data, mode, selected_id):
    fmt = "%Y-%m-%d %H-%M-%S"
    
    # Lọc dữ liệu theo STT ngay sau khi gộp
    filtered = [d for d in all_combined_data if str(d.get('STT')) == str(selected_id)]
    if not filtered: return []
    
    cp_data = sorted(filtered, key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    
    # ... (Logic chia giai đoạn theo 3 cách đã tóm tắt ở trên) ...
    # Chèn logic chia giai đoạn vào đây
    return cp_data # Trả về kết quả sau khi chia

# --- 3. PHẦN XỬ LÝ TẢI FILE QUAN TRỌNG ---
st.sidebar.header("📁 Tải dữ liệu nguồn")
# Đảm bảo accept_multiple_files=True để chọn được cả 2 file cùng lúc
uploaded_files = st.sidebar.file_uploader(
    "Chọn 2 file JSON (Tưới & Châm phân)", 
    type=["json"], 
    accept_multiple_files=True
)

all_data = []

if uploaded_files:
    # Gộp dữ liệu từ TẤT CẢ các file được chọn
    for f in uploaded_files:
        try:
            file_content = json.load(f)
            if isinstance(file_content, list):
                all_data.extend(file_content)
            else:
                all_data.append(file_content)
        except Exception as e:
            st.error(f"Lỗi khi đọc file {f.name}: {e}")

    if all_data:
        st.sidebar.success(f"Đã gộp thành công {len(all_data)} bản ghi từ {len(uploaded_files)} file.")
        
        # Lấy danh sách STT tổng hợp từ tất cả các file
        ids = sorted(list(set(str(d.get('STT')) for d in all_data if 'STT' in d)))
        
        with st.sidebar:
            mode = st.selectbox("Cách chia giai đoạn", ["Biến động Tần suất", "EC Kế hoạch", "EC Thực tế"])
            selected_id = st.selectbox("Chọn STT thiết bị cần soi", ids)

        # Chạy phân tích trên kho dữ liệu tổng all_data
        # results = get_data_seasons(all_data, mode, selected_id)
        # ... (Hiển thị bảng dữ liệu) ...
    else:
        st.info("Vui lòng chọn cả 2 file để hệ thống có đủ dữ liệu đối chiếu.")
