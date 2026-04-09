import streamlit as st
import json
from datetime import datetime

st.set_page_config(page_title="Phân tích Đa Mùa Vụ", layout="wide")

def xu_ly_da_mua_vu(all_data, id_tuoi, jump_threshold=2, sustain_days=3, gap_tach_vu=10, max_cap=40):
    fmt = "%Y-%m-%d %H-%M-%S"
    data_tuoi = [d for d in all_data if str(d.get('STT')) == str(id_tuoi)]
    if not data_tuoi: return []

    # 1. Thống kê số lần theo ngày
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

    # 2. BƯỚC MỚI: TÁCH RIÊNG CÁC MÙA VỤ (Dựa trên khoảng nghỉ dài)
    mua_vu_list = []
    temp_vu = [sorted_days[0]]
    
    for i in range(1, len(sorted_days)):
        if (sorted_days[i] - sorted_days[i-1]).days >= gap_tach_vu:
            mua_vu_list.append(temp_vu)
            temp_vu = [sorted_days[i]]
        else:
            temp_vu.append(sorted_days[i])
    mua_vu_list.append(temp_vu) # Thêm vụ cuối cùng

    # 3. CHIA GIAI ĐOẠN TRONG TỪNG VỤ
    final_report = []
    for idx_vu, ngay_trong_vu in enumerate(mua_vu_list):
        n = len(ngay_trong_vu)
        curr_start_idx = 0
        vu_phases = []

        while curr_start_idx < n:
            j = curr_start_idx + 1
            while j < n:
                # Tính trung bình hiện tại để so sánh nhảy vọt
                current_group = ngay_trong_vu[curr_start_idx:j]
                avg_current = sum(get_val(d) for d in current_group) / len(current_group)
                
                val_j = get_val(ngay_trong_vu[j])
                if abs(val_j - avg_current) >= jump_threshold:
                    # Kiểm tra duy trì liên tiếp
                    sustain_count = 0
                    for k in range(j, min(j + sustain_days, n)):
                        if abs(get_val(ngay_trong_vu[k]) - avg_current) >= (jump_threshold - 0.5):
                            sustain_count += 1
                    if sustain_count >= sustain_days:
                        break
                j += 1
            
            group = ngay_trong_vu[curr_start_idx:j]
            vu_phases.append({
                "Bắt đầu": ngay_trong_vu[curr_start_idx],
                "Kết thúc": ngay_trong_vu[j-1],
                "Số lần TB": round(sum(get_val(d) for d in group) / len(group))
            })
            curr_start_idx = j
            
        final_report.append({"Ten_Vu": f"Mùa vụ {idx_vu + 1}", "Giai_Doan": vu_phases})
    
    return final_report

# --- GIAO DIỆN ---
st.title("📊 Phân tích Đa Mùa vụ & Giai đoạn")

uploaded = st.sidebar.file_uploader("Tải file JSON", type=["json"], accept_multiple_files=True)

if uploaded:
    all_data = []
    for f in uploaded:
        content = json.load(f)
        all_data.extend(content) if isinstance(content, list) else all_data.append(content)

    ids = sorted(list(set(str(d.get('STT')) for d in all_data if 'STT' in d)))
    
    with st.sidebar:
        id_tuoi = st.selectbox("Chọn STT Nhỏ giọt", ids, index=ids.index("2") if "2" in ids else 0)
        st.divider()
        st.write("**Cấu hình Tách Vụ**")
        gap_vu = st.slider("Số ngày nghỉ để coi là hết vụ", 5, 30, 10)
        st.write("**Cấu hình Giai Đoạn**")
        threshold = st.slider("Độ lệch nhảy vọt", 1, 5, 2)
        sustain = st.slider("Số ngày duy trì", 2, 5, 3)

    report = xu_ly_da_mua_vu(all_data, id_tuoi, threshold, sustain, gap_vu)

    if report:
        for vu in report:
            with st.expander(f"📂 {vu['Ten_Vu']} ({vu['Giai_Doan'][0]['Bắt đầu']} đến {vu['Giai_Doan'][-1]['Kết thúc']})", expanded=True):
                table = "| GĐ | Từ ngày | Đến ngày | Tần suất TB |\n|---|---|---|---|\n"
                for i, g in enumerate(vu['Giai_Doan']):
                    table += f"| {i+1} | {g['Bắt đầu']} | {g['Kết thúc']} | ~{g['Số lần TB']} lần/ngày |\n"
                st.markdown(table)
else:
    st.info("👈 Hãy tải file để tách vụ và chia giai đoạn.")
