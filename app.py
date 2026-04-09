import streamlit as st
import json
from datetime import datetime

# Cấu hình trang nằm ở dòng đầu tiên của code
st.set_page_config(page_title="Phân tích Mùa vụ", layout="wide")

# --- HÀM XỬ LÝ DỮ LIỆU (Đã bọc kiểm lỗi) ---
def get_tier_seasons(all_data, id_tuoi, tier_step=5, min_days=4, max_cap=40):
    try:
        fmt = "%Y-%m-%d %H-%M-%S"
        # Lọc dữ liệu theo STT
        data_tuoi = [d for d in all_data if str(d.get('STT')) == str(id_tuoi)]
        if not data_tuoi:
            return []

        # Đếm tần suất ngày
        daily_counts = {}
        for d in data_tuoi:
            try:
                dt = datetime.strptime(d['Thời gian'], fmt).date()
                daily_counts[dt] = daily_counts.get(dt, 0) + 1
            except:
                continue
        
        sorted_days = sorted(daily_counts.keys())
        if not sorted_days:
            return []

        # Hàm tính bậc (Tier)
        def get_tier(d):
            v = daily_counts[d]
            v = v if v <= max_cap else max_cap
            return (v // tier_step) * tier_step

        seasons = []
        curr_start = sorted_days[0]
        curr_tier = get_tier(curr_start)
        
        for i in range(1, len(sorted_days)):
            d_p = sorted_days[i-1]
            d_c = sorted_days[i]
            tier_c = get_tier(d_c)
            gap = (d_c - d_p).days
            
            # Điều kiện ngắt giai đoạn
            if tier_c != curr_tier or gap > 3:
                duration = (d_p - curr_start).days + 1
                if duration >= min_days:
                    # Tính trung bình an toàn
                    vals = [daily_counts[d] for d in sorted_days if curr_start <= d <= d_p]
                    avg_v = sum(vals) / len(vals) if vals else 0
                    seasons.append({
                        "Bắt đầu": curr_start,
                        "Kết thúc": d_p,
                        "Tần suất": round(avg_v)
                    })
                    curr_start = d_c
                    curr_tier = tier_c

        # Giai đoạn cuối
        last_vals = [daily_counts[d] for d in sorted_days if curr_start <= d <= sorted_days[-1]]
        if last_vals:
            seasons.append({
                "Bắt đầu": curr_start,
                "Kết thúc": sorted_days[-1],
                "Tần suất": round(sum(last_vals)/len(last_vals))
            })
        return seasons
    except Exception as e:
        st.error(f"Lỗi logic: {e}")
        return []

# --- GIAO DIỆN CHÍNH ---
st.title("📊 Hệ thống Phân chia Mùa vụ")

# Sidebar luôn hiện để nạp file
st.sidebar.header("📁 Cài đặt Nguồn dữ liệu")
uploaded_files = st.sidebar.file_uploader("Tải file JSON", type=["json"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for f in uploaded_files:
        try:
            content = json.load(f)
            if isinstance(content, list):
                all_data.extend(content)
            else:
                all_data.append(content)
        except Exception as e:
            st.sidebar.error(f"Lỗi đọc file {f.name}: {e}")

    if all_data:
        # Lấy danh sách STT để chọn
        all_ids = sorted(list(set(str(d.get('STT')) for d in all_data if 'STT' in d)))
        
        with st.sidebar:
            st.divider()
            id_target = st.selectbox("Chọn STT Nhỏ giọt (Lịch tưới)", all_ids, index=0)
            st.subheader("Cân chỉnh Giai đoạn")
            t_step = st.slider("Độ nhạy (Lệch bao nhiêu lần thì chia GĐ)", 2, 10, 5)
            m_days = st.slider("Số ngày tối thiểu 1 giai đoạn", 2, 10, 4)
            m_cap = st.number_input("Trần lọc nhiễu", value=35)

        # Chạy tính toán
        results = get_tier_seasons(all_data, id_target, t_step, m_days, m_cap)

        if results:
            st.subheader(f"✅ Đã phân tách thành {len(results)} giai đoạn")
            
            # Tạo bảng Markdown thuần
            table_head = "| Giai đoạn | Ngày bắt đầu | Ngày kết thúc | Tần suất trung bình |\n|---|---|---|---|\n"
            table_rows = ""
            for idx, r in enumerate(results):
                table_rows += f"| {idx+1} | {r['Bắt đầu']} | {r['Kết thúc']} | ~{r['Tần suất']} lần/ngày |\n"
            
            st.markdown(table_head + table_rows)
        else:
            st.warning("⚠️ Không tìm thấy dữ liệu tưới cho STT này. Hãy chọn lại STT ở Sidebar.")
    else:
        st.info("Dữ liệu trong file trống.")
else:
    st.info("👈 Hãy bắt đầu bằng cách tải các file JSON vào thanh bên trái.")
