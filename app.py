# --- LOGIC CHIA GIAI ĐOẠN TINH CHỈNH ---
    nguong_bien_dong_tinh = 4  # Tăng lên 4 để bỏ qua các dao động nhỏ
    ngay_toi_thieu_gd = 3      # Giai đoạn phải >= 3 ngày mới được ngắt
    
    ngay_sap_xep = sorted(vu_hien_tai['daily_stats'].keys())
    danh_sach_gd = [] 
    
    if ngay_sap_xep:
        tap_hop_ngay = [ngay_sap_xep[0]]
        
        for i in range(1, len(ngay_sap_xep)):
            ngay_hien_tai = ngay_sap_xep[i]
            so_lan_hien_tai = vu_hien_tai['daily_stats'][ngay_hien_tai]['count']
            
            # Tính trung bình của những ngày đang có trong tập hợp
            trung_binh_gd = sum(vu_hien_tai['daily_stats'][d]['count'] for d in tap_hop_ngay) / len(tap_hop_ngay)
            
            # Kiểm tra: lệch > 4 VÀ đã đủ 3 ngày chưa
            if abs(so_lan_hien_tai - trung_binh_gd) > nguong_bien_dong_tinh and len(tap_hop_ngay) >= ngay_toi_thieu_gd:
                danh_sach_gd.append(tap_hop_ngay)
                tap_hop_ngay = [ngay_hien_tai]
            else:
                tap_hop_ngay.append(ngay_hien_tai)
        
        if tap_hop_ngay:
            danh_sach_gd.append(tap_hop_ngay)

    # --- BƯỚC GỘP CƯỠNG BỨC (Nếu vẫn quá nhiều) ---
    if len(danh_sach_gd) > 15:
        danh_sach_gd_rut_gon = [danh_sach_gd[0]]
        for i in range(1, len(danh_sach_gd)):
            # Nếu đoạn này quá ngắn (<3 ngày), gộp vào đoạn trước đó
            if len(danh_sach_gd[i]) < ngay_toi_thieu_gd:
                danh_sach_gd_rut_gon[-1].extend(danh_sach_gd[i])
            else:
                danh_sach_gd_rut_gon.append(danh_sach_gd[i])
        danh_sach_gd = danh_sach_gd_rut_gon
