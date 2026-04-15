import streamlit as st
import numpy as np
import json
import pandas as pd  # Đã thêm lại pandas để xử lý giao diện bảng
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# =====================================================================
# PHẦN 1: CẤU HÌNH CÁC QUY TẮC CHUNG
# =====================================================================
CAU_HINH_QUY_TAC = {
    "GIAY_TUOI_TOI_THIEU": 20,     
    "GIAY_TUOI_TOI_DA": 3600,      
    "SO_NGAY_NGHI_TOI_DA": 2,      
    "SO_NGAY_TOI_THIEU_MOT_VU": 7  
}

# =====================================================================
# PHẦN 2: CÁC HÀM XỬ LÝ DỮ LIỆU
# =====================================================================

def lay_gia_tri_so_thuc_tu_chuoi(dong_du_lieu, danh_sach_tu_khoa):
    for tu_khoa in danh_sach_tu_khoa:
        gia_tri_tim_thay = dong_du_lieu.get(tu_khoa)
        if gia_tri_tim_thay is not None:
            try:
                chuoi_gia_tri = str(gia_tri_tim_thay).replace(',', '.')
                return float(chuoi_gia_tri) / 100.0 
            except (ValueError, TypeError):
                continue
    return None

def ham_lay_thoi_gian_de_sap_xep(dong_du_lieu):
    return dong_du_lieu['Thời gian']

def tao_so_cai_du_lieu_tong_hop(danh_sach_tep_tin_nho_giot, danh_sach_tep_tin_cham_phan, khu_vuc_duoc_chon):
    du_lieu_tam_thoi_theo_ngay = {}

    if danh_sach_tep_tin_nho_giot:
        toan_bo_du_lieu_nho_giot = []
        for tep_tin in danh_sach_tep_tin_nho_giot:
            tep_tin.seek(0)
            du_lieu_trong_tep = json.load(tep_tin)
            for dong in du_lieu_trong_tep: toan_bo_du_lieu_nho_giot.append(dong)
        
        du_lieu_nho_giot_da_loc = [d for d in toan_bo_du_lieu_nho_giot if str(d.get('STT')) == khu_vuc_duoc_chon]
        du_lieu_nho_giot_da_loc.sort(key=ham_lay_thoi_gian_de_sap_xep)

        for dong_du_lieu in du_lieu_nho_giot_da_loc:
            try:
                thoi_diem = datetime.strptime(dong_du_lieu['Thời gian'], "%Y-%m-%d %H-%M-%S")
                ngay_str = thoi_diem.strftime("%Y-%m-%d")
            except: continue 
                
            if ngay_str not in du_lieu_tam_thoi_theo_ngay: 
                du_lieu_tam_thoi_theo_ngay[ngay_str] = {'so_lan_tuoi': 0, 'tong_so_giay_tuoi': 0, 'danh_sach_tbec': [], 'danh_sach_ec_yeu_cau': []}
                
            gia_tri_tbec = lay_gia_tri_so_thuc_tu_chuoi(dong_du_lieu, ['TBEC', 'tbec'])
            if gia_tri_tbec is not None: du_lieu_tam_thoi_theo_ngay[ngay_str]['danh_sach_tbec'].append(gia_tri_tbec)

        for vi_tri in range(len(du_lieu_nho_giot_da_loc) - 1):
            d1, d2 = du_lieu_nho_giot_da_loc[vi_tri], du_lieu_nho_giot_da_loc[vi_tri + 1]
            if d1.get('Trạng thái') == "Bật" and d2.get('Trạng thái') == "Tắt":
                t1, t2 = datetime.strptime(d1['Thời gian'], "%Y-%m-%d %H-%M-%S"), datetime.strptime(d2['Thời gian'], "%Y-%m-%d %H-%M-%S")
                so_giay = (t2 - t1).total_seconds()
                if CAU_HINH_QUY_TAC["GIAY_TUOI_TOI_THIEU"] <= so_giay <= CAU_HINH_QUY_TAC["GIAY_TUOI_TOI_DA"]:
                    ngay_s = t1.strftime("%Y-%m-%d")
                    if ngay_s in du_lieu_tam_thoi_theo_ngay:
                        du_lieu_tam_thoi_theo_ngay[ngay_s]['so_lan_tuoi'] += 1
                        du_lieu_tam_thoi_theo_ngay[ngay_s]['tong_so_giay_tuoi'] += so_giay

    if danh_sach_tep_tin_cham_phan:
        for tep_tin in danh_sach_tep_tin_cham_phan:
            tep_tin.seek(0)
            du_lieu_trong_tep = json.load(tep_tin)
            for dong_du_lieu in du_lieu_trong_tep:
                if str(dong_du_lieu.get('STT')) != khu_vuc_duoc_chon: continue 
                try: ngay_str = datetime.strptime(dong_du_lieu['Thời gian'], "%Y-%m-%d %H-%M-%S").strftime("%Y-%m-%d")
                except: continue
                if ngay_str not in du_lieu_tam_thoi_theo_ngay: 
                    du_lieu_tam_thoi_theo_ngay[ngay_str] = {'so_lan_tuoi': 0, 'tong_so_giay_tuoi': 0, 'danh_sach_tbec': [], 'danh_sach_ec_yeu_cau': []}
                gia_tri_ec_yc = lay_gia_tri_so_thuc_tu_chuoi(dong_du_lieu, ['EC yêu cầu', 'ecreq'])
                if gia_tri_ec_yc is not None: du_lieu_tam_thoi_theo_ngay[ngay_str]['danh_sach_ec_yeu_cau'].append(gia_tri_ec_yc)

    so_cai = {}
    for ngay, d in du_lieu_tam_thoi_theo_ngay.items():
        so_cai[ngay] = {
            'so_lan_tuoi': d['so_lan_tuoi'],
            'thoi_gian_tuoi_phut': int(round(d['tong_so_giay_tuoi'] / 60)),
            'tbec': float(f"{np.mean(d['danh_sach_tbec']):.2f}") if d['danh_sach_tbec'] else 0.0,
            'ec_yeu_cau': float(f"{np.mean(d['danh_sach_ec_yeu_cau']):.2f}") if d['danh_sach_ec_yeu_cau'] else 0.0
        }
    return so_cai

def tim_kiem_cac_mua_vu(so_cai_du_lieu, ten_chi_so_lam_goc, nguong_gia_tri_bat_dau):
    danh_sach_ngay = sorted([datetime.strptime(ngay, "%Y-%m-%d").date() for ngay, d in so_cai_du_lieu.items() if d[ten_chi_so_lam_goc] >= nguong_gia_tri_bat_dau])
    danh_sach_cac_mua_vu = []
    if not danh_sach_ngay: return []
    
    ngay_bat_dau_vu = danh_sach_ngay[0]
    for i in range(1, len(danh_sach_ngay)):
        if (danh_sach_ngay[i] - danh_sach_ngay[i-1]).days > CAU_HINH_QUY_TAC["SO_NGAY_NGHI_TOI_DA"]:
            if (danh_sach_ngay[i-1] - ngay_bat_dau_vu).days + 1 >= CAU_HINH_QUY_TAC["SO_NGAY_TOI_THIEU_MOT_VU"]:
                danh_sach_cac_mua_vu.append((ngay_bat_dau_vu, danh_sach_ngay[i-1]))
            ngay_bat_dau_vu = danh_sach_ngay[i]
    if (danh_sach_ngay[-1] - ngay_bat_dau_vu).days + 1 >= CAU_HINH_QUY_TAC["SO_NGAY_TOI_THIEU_MOT_VU"]:
        danh_sach_cac_mua_vu.append((ngay_bat_dau_vu, danh_sach_ngay[-1]))
    return danh_sach_cac_mua_vu

def chia_nho_mua_vu_thanh_cac_giai_doan(danh_sach_ngay_trong_vu, so_cai_du_lieu, ten_chi_so_lam_goc, sai_so_cho_phep):
    if not danh_sach_ngay_trong_vu: return []
    danh_sach_cac_giai_doan = []
    giai_doan_hien_tai = [danh_sach_ngay_trong_vu[0]]
    ngay_nghi_ngo = None 

    for i in range(1, len(danh_sach_ngay_trong_vu)):
        ngay_xet = danh_sach_ngay_trong_vu[i]
        val_xet = so_cai_du_lieu[ngay_xet][ten_chi_so_lam_goc]
        val_moc = so_cai_du_lieu[giai_doan_hien_tai[0]][ten_chi_so_lam_goc]
        
        if abs(val_xet - val_moc) >= sai_so_cho_phep:
            if ngay_nghi_ngo is None:
                ngay_nghi_ngo = ngay_xet
                giai_doan_hien_tai.append(ngay_xet)
            else: 
                giai_doan_hien_tai.pop() 
                danh_sach_cac_giai_doan.append(giai_doan_hien_tai)
                giai_doan_hien_tai = [ngay_nghi_ngo, ngay_xet]
                ngay_nghi_ngo = None
        else:
            ngay_nghi_ngo = None
            giai_doan_hien_tai.append(ngay_xet)
            
    danh_sach_cac_giai_doan.append(giai_doan_hien_tai)
    return danh_sach_cac_giai_doan

# =====================================================================
# PHẦN 3: HÀM VẼ BIỂU ĐỒ 
# =====================================================================

def ve_bieu_do_chi_so_duoc_chon(du_lieu_tong_hop, danh_sach_cac_giai_doan, ten_chi_so_hien_thi, ten_bien_trong_so_cai, vi_tri_gd_highlight=None):
    khung_tranh = plt.figure(figsize=(16, 6))
    truc_toa_do = plt.gca()
    bang_mau = ['#66b3ff', '#99ff99', '#ff9999', '#ffcc99', '#c2c2f0', '#ffb3e6', '#c4e17f', '#ffdf80']
    
    danh_sach_ngay_ve = []
    truc_x_hien_tai = 0
    
    for i, gd in enumerate(danh_sach_cac_giai_doan):
        mau = bang_mau[i % len(bang_mau)]
        do_trong_suot = 1.0 
        if vi_tri_gd_highlight is not None and vi_tri_gd_highlight != i:
            do_trong_suot = 0.2 
            
        du_lieu_y = []
        for n in gd:
            danh_sach_ngay_ve.append(n)
            du_lieu_y.append(du_lieu_tong_hop[n][ten_bien_trong_so_cai])
            
        x_gd = np.arange(truc_x_hien_tai, truc_x_hien_tai + len(gd))
        truc_toa_do.bar(x_gd, du_lieu_y, color=mau, edgecolor='black', alpha=do_trong_suot, label=f'GĐ {i+1}')
        truc_x_hien_tai += len(gd)
        
    truc_toa_do.set_ylabel(ten_chi_so_hien_thi)
    truc_toa_do.grid(axis='y', linestyle='--', alpha=0.5)
    truc_toa_do.legend(title="Giai đoạn", loc='upper left', bbox_to_anchor=(1, 1))
    
    buoc = max(1, len(danh_sach_ngay_ve) // 25)
    plt.xticks(np.arange(len(danh_sach_ngay_ve))[::buoc], [n[-5:] for n in danh_sach_ngay_ve[::buoc]], rotation=45)
    plt.title(f"Phân tích theo: {ten_chi_so_hien_thi}")
    plt.tight_layout()
    return khung_tranh

# =====================================================================
# PHẦN 4: GIAO DIỆN STREAMLIT 
# =====================================================================

def main():
    st.set_page_config(page_title="TOOL UI HỆ THỐNG TỰ ĐỘNG NÔNG NGHIỆP V1.6", layout="wide")
    st.title("📊 TOOL UI HỆ THỐNG TỰ ĐỘNG NÔNG NGHIỆP V1.6")
    
    with st.sidebar:
        st.header("📂 1. Tải lên & Phân loại dữ liệu")
        tat_ca_tep = st.file_uploader("Kéo thả TẤT CẢ các tệp JSON vào đây", accept_multiple_files=True, type=['json'])
        
        tep_nho_giot = []
        tep_cham_phan = []
        
        if tat_ca_tep:
            st.markdown("---")
            st.markdown("**Phân bổ tệp dữ liệu vừa tải lên:**")
            st.caption("Tick chọn file tương ứng với mỗi luồng dữ liệu (có thể chọn nhiều file).")
            danh_sach_ten = [f.name for f in tat_ca_tep]
            chon_tep_nho_giot = st.multiselect("💧 Dữ liệu Nhỏ Giọt (Lần tưới, TBEC):", options=danh_sach_ten)
            chon_tep_cham_phan = st.multiselect("🧪 Dữ liệu Châm Phân (EC Yêu cầu):", options=danh_sach_ten)
            tep_nho_giot = [f for f in tat_ca_tep if f.name in chon_tep_nho_giot]
            tep_cham_phan = [f for f in tat_ca_tep if f.name in chon_tep_cham_phan]
            
        st.markdown("---")
        khu_vuc = st.selectbox("Khu vực", ["1", "2", "3", "4"])
        
        st.markdown("---")
        st.header("⚙️ 2. Cài đặt thuật toán")
        tu_dien = {"Lần tưới": "so_lan_tuoi", "TBEC": "tbec", "EC Yêu cầu": "ec_yeu_cau"}
        ten_hien_thi = st.selectbox("🎯 Chỉ số làm mốc", list(tu_dien.keys()))
        bien_goc = tu_dien[ten_hien_thi]
        
        # Tên cột trong bảng tương ứng để highlight
        tu_dien_cot_bang = {"Lần tưới": "LẦN TƯỚI", "TBEC": "TBEC", "EC Yêu cầu": "EC YÊU CẦU"}
        ten_cot_highlight = tu_dien_cot_bang[ten_hien_thi]
        
        def_n, def_s = (8.1, 5.0) if bien_goc == "so_lan_tuoi" else (0.38, 0.14) if bien_goc == "tbec" else (0.90, 0.16)
        nguong = st.number_input(f"📈 Ngưỡng bắt đầu", value=def_n)
        sai_so = st.number_input(f"✂️ Sai số cắt GĐ", value=def_s)

    if tep_nho_giot or tep_cham_phan:
        so_cai = tao_so_cai_du_lieu_tong_hop(tep_nho_giot, tep_cham_phan, khu_vuc)
        if not so_cai: st.error("Không có dữ liệu hợp lệ trong các tệp đã chọn!"); return
            
        mua_vu = tim_kiem_cac_mua_vu(so_cai, bien_goc, nguong)
        if not mua_vu: st.warning("Không tìm thấy vụ mùa nào thỏa mãn ngưỡng!"); return

        # CHỌN MÙA VỤ
        st.markdown("---")
        ten_vu = [f"Vụ {i+1}: {v[0].strftime('%d/%m')} - {v[1].strftime('%d/%m')}" for i, v in enumerate(mua_vu)]
        vi_tri_vu = st.selectbox("🌾 3. Chọn Mùa Vụ Để Vẽ Biểu Đồ & Phân Tích Sâu", range(len(mua_vu)), format_func=lambda x: ten_vu[x])
        
        vu_chot = mua_vu[vi_tri_vu]
        cac_ngay_vu = sorted([n for n in so_cai.keys() if vu_chot[0] <= datetime.strptime(n, "%Y-%m-%d").date() <= vu_chot[1]])
        gd_list = chia_nho_mua_vu_thanh_cac_giai_doan(cac_ngay_vu, so_cai, bien_goc, sai_so)
        
        # THẺ CHỈ SỐ NHANH
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tổng thời gian vụ", f"{len(cac_ngay_vu)} ngày")
        m2.metric("Số giai đoạn", f"{len(gd_list)} GĐ")
        tb_tbec = np.mean([so_cai[n]['tbec'] for n in cac_ngay_vu])
        m3.metric("TBEC Trung bình", f"{tb_tbec:.2f}")
        tb_tuoi = np.mean([so_cai[n]['so_lan_tuoi'] for n in cac_ngay_vu])
        m4.metric("Tần suất tưới TB", f"{int(tb_tuoi)} lần/ngày")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # BỘ LỌC HIGHLIGHT GIAI ĐOẠN
        col1, col2 = st.columns([2, 1])
        with col1:
            st.success(f"✅ Đã phân tích được **{len(gd_list)} giai đoạn** cho {ten_vu[vi_tri_vu]}.")
        with col2:
            danh_sach_chon_gd = ["Tất cả"] + [f"Giai đoạn {i+1}" for i in range(len(gd_list))]
            gd_duoc_chon = st.selectbox("🔦 Làm nổi bật Giai đoạn:", danh_sach_chon_gd)
            
        vi_tri_gd_highlight = None
        if gd_duoc_chon != "Tất cả":
            vi_tri_gd_highlight = danh_sach_chon_gd.index(gd_duoc_chon) - 1

        # VẼ BIỂU ĐỒ 
        fig = ve_bieu_do_chi_so_duoc_chon(so_cai, gd_list, ten_hien_thi, bien_goc, vi_tri_gd_highlight)
        st.pyplot(fig, use_container_width=True)
        
        # BẢNG DỮ LIỆU VỚI PANDAS VÀ HIGHLIGHT
        st.markdown("### 📋 Bảng Số Liệu Chi Tiết")
        bang_data = []
        for i, gd in enumerate(gd_list):
            if vi_tri_gd_highlight is not None and vi_tri_gd_highlight != i:
                continue 
            for n in gd:
                bang_data.append({
                    "Giai đoạn": f"GĐ {i+1}", 
                    "Ngày": n,
                    "LẦN TƯỚI": so_cai[n]['so_lan_tuoi'],
                    "PHÚT TƯỚI": so_cai[n]['thoi_gian_tuoi_phut'],
                    "TBEC": round(so_cai[n]['tbec'], 2),
                    "EC YÊU CẦU": round(so_cai[n]['ec_yeu_cau'], 2)
                })
                
        if bang_data:
            df = pd.DataFrame(bang_data)
            
            # Hàm tô màu cột được chọn
            def to_mau_cot(s):
                if s.name == ten_cot_highlight:
                    return ['background-color: rgba(255, 204, 0, 0.3); font-weight: bold; color: #d35400'] * len(s)
                return [''] * len(s)
            
            st.dataframe(df.style.apply(to_mau_cot), use_container_width=True)
        else:
            st.info("Không có dữ liệu để hiển thị bảng.")

        # =================================================================
        # KÍNH LÚP TRA CỨU TOÀN CỤC (CUỐI TRANG)
        # =================================================================
        tu_dien_tra_cuu_toan_cuc = {}
        for vi_tri_vu_tc, vu_tc in enumerate(mua_vu):
            cac_ngay_vu_tc = sorted([n for n in so_cai.keys() if vu_tc[0] <= datetime.strptime(n, "%Y-%m-%d").date() <= vu_tc[1]])
            gd_list_tc = chia_nho_mua_vu_thanh_cac_giai_doan(cac_ngay_vu_tc, so_cai, bien_goc, sai_so)
            for vi_tri_gd_tc, gd_tc in enumerate(gd_list_tc):
                for ngay_str in gd_tc:
                    ngay_kieu_date = datetime.strptime(ngay_str, "%Y-%m-%d").date()
                    ngay_thu = (ngay_kieu_date - vu_tc[0]).days + 1
                    tu_dien_tra_cuu_toan_cuc[ngay_kieu_date] = {
                        "Vụ Mùa": f"Vụ {vi_tri_vu_tc + 1}",
                        "Ngày Thứ": ngay_thu,
                        "Giai Đoạn": f"Giai đoạn {vi_tri_gd_tc + 1}"
                    }

        st.markdown("---")
        st.subheader("🔍 Kính Lúp Tra Cứu Toàn Cục")
        st.caption("Tra cứu nhanh thông tin ngày bất kỳ (không ảnh hưởng biểu đồ bên trên).")
        
        col_k1, col_k2 = st.columns([1, 2])
        with col_k1:
            ngay_nho_nhat_data = min(tu_dien_tra_cuu_toan_cuc.keys())
            ngay_lon_nhat_data = max(tu_dien_tra_cuu_toan_cuc.keys())
            khoang_thoi_gian_tra_cuu = st.date_input("🗓️ Chọn khoảng thời gian:", value=[], min_value=ngay_nho_nhat_data, max_value=ngay_lon_nhat_data)
        
        with col_k2:
            if len(khoang_thoi_gian_tra_cuu) == 2:
                ngay_bd_tc, ngay_kt_tc = khoang_thoi_gian_tra_cuu
                ket_qua_tra_cuu = []
                tong_so_ngay = (ngay_kt_tc - ngay_bd_tc).days
                for i in range(tong_so_ngay + 1):
                    ngay_dang_xet = ngay_bd_tc + timedelta(days=i)
                    if ngay_dang_xet in tu_dien_tra_cuu_toan_cuc:
                        thong_tin = tu_dien_tra_cuu_toan_cuc[ngay_dang_xet]
                        ket_qua_tra_cuu.append({
                            "Ngày": ngay_dang_xet.strftime("%d/%m/%Y"),
                            "Thuộc Vụ": thong_tin["Vụ Mùa"],
                            "Tiến Độ": f"Ngày thứ {thong_tin['Ngày Thứ']}",
                            "Giai Đoạn": thong_tin["Giai Đoạn"]
                        })
                if ket_qua_tra_cuu: st.dataframe(ket_qua_tra_cuu, use_container_width=True)
                else: st.info("💡 Không có dữ liệu mùa vụ trong khoảng này.")

    else:
        st.info("👈 Vui lòng tải lên và chọn tệp JSON để bắt đầu.")

    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #888888; padding: 20px; font-weight: bold; font-style: italic;'>CODED BY QUANG SKIBIDI DOPYEYE-GEMINI 👽</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
