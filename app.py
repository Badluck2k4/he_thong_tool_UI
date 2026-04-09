import streamlit as st
import json
from datetime import datetime

st.set_page_config(page_title="Phân tích Mùa vụ Chính xác", layout="wide")

def xu_ly_du_lieu_chuan(all_data, id_tuoi, gap_tach_vu=10, jump_threshold=3, sustain_days=4):
    fmt = "%Y-%m-%d %H-%M-%S"
    # Lọc đúng STT và sắp xếp thời gian
    data_khu = sorted([d for d in all_data if str(d.get('STT')) == str(id_tuoi)],
                      key=lambda x: datetime.strptime(x['Thời gian'], fmt))
    
    # 1. LOGIC ĐẾM LẦN TƯỚI CHUẨN (Khớp với biểu đồ)
    daily_counts = {}
    i = 0
    while i < len(data_khu) - 1:
        h1 = data_khu[i]
        h2 = data_khu[i+1]
        
        # Chỉ đếm khi có cặp Bật -> Tắt
        if h1.get('Trạng thái') == "Bật" and h2.get('Trạng thái') == "Tắt":
            t1 = datetime.strptime(h1['Thời gian'], fmt)
            t2 = datetime.strptime(h2['Thời gian'], fmt)
            duration = (t2 - t1).total_seconds()
            
            # Chỉ đếm lần tưới thực sự (từ 20s đến 10 phút để loại nhiễu)
            if 20 <= duration <= 600:
                d_str = t1.date()
                daily_counts[d_str] = daily_counts.get(d_str, 0) + 1
                i += 2 # Nhảy qua cặp đã đếm
                continue
        i += 1

    sorted_days = sorted(daily_counts.keys())
    if not sorted_days: return []

    # 2. TÁCH MÙA VỤ (Dựa trên khoảng nghỉ giữa các ngày tưới)
    mua_vu_list = []
    if sorted_days:
        temp_vu = [sorted_days[0]]
        for i in range(1, len(sorted_days)):
            if (sorted_days[i] - sorted_days[i-1]).days >= gap_tach_vu:
                mua_vu_list.append(temp_vu)
                temp_vu = [sorted_days[i]]
            else:
                temp_vu.append(sorted_days[i])
        mua_vu_list.append(temp_vu)

    # 3. CHIA GIAI ĐOẠN (Gom nhóm ngày có tần suất tương đương)
    final_report = []
    for idx, ngay_trong_vu in enumerate(mua_vu_list):
        phases = []
        n = len(ngay_trong_vu)
        curr_idx = 0
        
        while curr_idx < n:
            start_day = ngay_trong_vu[curr_idx]
            # Lấy giá trị mốc của ngày bắt đầu
            ref_val = daily_counts[start_day]
            
            j = curr_idx + 1
            while j < n:
                val_j = daily_counts[ngay_trong_vu[j]]
                # Nếu lệch quá ngưỡng và sự lệch này duy trì liên tiếp
                if abs(val_j - ref_val) >= jump_threshold:
                    # Kiểm tra xem có phải biến động nhất thời hay đổi giai đoạn thật
                    sustain = True
                    for k in range(j, min(j + sustain_days, n)):
                        if abs(daily_counts[ngay_trong_vu[k]] - ref_val) < jump_threshold:
                            sustain = False
                            break
                    if sustain: break 
                j += 1
            
            # Chốt giai đoạn
            group = ngay_trong_vu[curr_idx:j]
            avg_v = sum(daily_counts[d] for d in group) / len(group)
            phases.append({
                "Từ": start_day,
                "Đến": ngay_trong_vu[j-1],
                "TB": round(avg_v, 1),
                "Số ngày": len(group)
            })
            curr_idx = j
            
        final_report.append({"Tên": f"Mùa vụ {idx+1}", "GĐ": phases})
    return final_report

# --- GIAO DIỆN ---
st.title("📊 Phân tích Mùa vụ & Giai đoạn (Số liệu Chuẩn)")
files = st.sidebar.file_uploader("Nạp file JSON", accept_multiple_files=True)

if files:
    all_raw = []
    for f in files:
        all_raw.extend(json.load(f))
    
    with st.sidebar:
        id_tuoi = st.selectbox("Chọn STT", ["2", "1"])
        st.divider()
        g_vu = st.slider("Ngày nghỉ tách vụ", 5, 20, 10)
        g_jump = st.slider("Độ lệch tách GĐ", 2, 10, 4) # Tăng lên 4-5 để gộp tốt hơn

    report = xu_ly_du_lieu_chuan(all_raw, id_tuoi, g_vu, g_jump)

    for vu in report:
        with st.expander(f"📂 {vu['Tên']}: {vu['GĐ'][0]['Từ']} -> {vu['GĐ'][-1]['Đến']}", expanded=True):
            txt = "| GĐ | Từ ngày | Đến ngày | Số ngày | Tần suất TB |\n|---|---|---|---|---|\n"
            for i, g in enumerate(vu['GĐ']):
                txt += f"| {i+1} | {g['Từ']} | {g['Đến']} | {g['Số ngày']} | {g['TB']} lần/ngày |\n"
            st.markdown(txt)
