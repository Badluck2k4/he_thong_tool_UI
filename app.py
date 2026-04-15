# =====================================================================
# PHẦN 3: HÀM VẼ BIỂU ĐỒ (MỖI GIAI ĐOẠN MỘT MÀU RIÊNG BIỆT)
# =====================================================================

def ve_bieu_do_chi_so_duoc_chon(du_lieu_tong_hop, danh_sach_cac_giai_doan, ten_chi_so_hien_thi, ten_bien_trong_so_cai):
    # Tạo 1 khung tranh duy nhất
    khung_tranh = plt.figure(figsize=(16, 6))
    truc_toa_do = plt.gca()
    
    # Bảng màu sắc chuẩn bị sẵn cho các giai đoạn (Hệ thống sẽ lặp lại nếu có quá nhiều giai đoạn)
    bang_mau = ['#66b3ff', '#99ff99', '#ff9999', '#ffcc99', '#c2c2f0', '#ffb3e6', '#c4e17f', '#ffdf80']
    
    danh_sach_ngay_thuc_te_de_ve = []
    truc_x_hien_tai = 0 # Biến theo dõi vị trí vẽ của trục X
    
    # Vẽ từng giai đoạn một để áp dụng màu và nhãn riêng
    for vi_tri_gd in range(len(danh_sach_cac_giai_doan)):
        giai_doan_dang_xet = danh_sach_cac_giai_doan[vi_tri_gd]
        mau_sac_cua_giai_doan = bang_mau[vi_tri_gd % len(bang_mau)]
        
        du_lieu_doc_truc_y = []
        for ngay in giai_doan_dang_xet:
            danh_sach_ngay_thuc_te_de_ve.append(ngay)
            gia_tri_trong_ngay = du_lieu_tong_hop[ngay][ten_bien_trong_so_cai]
            du_lieu_doc_truc_y.append(gia_tri_trong_ngay)
            
        so_ngay_trong_giai_doan = len(giai_doan_dang_xet)
        truc_x_cua_giai_doan = np.arange(truc_x_hien_tai, truc_x_hien_tai + so_ngay_trong_giai_doan)
        
        # Vẽ biểu đồ cột cho cụm ngày của giai đoạn này
        truc_toa_do.bar(
            truc_x_cua_giai_doan, 
            du_lieu_doc_truc_y, 
            color=mau_sac_cua_giai_doan, 
            edgecolor='black', 
            label=f'Giai đoạn {vi_tri_gd + 1}'
        )
        
        # Tịnh tiến trục X để chuẩn bị vẽ giai đoạn tiếp theo
        truc_x_hien_tai += so_ngay_trong_giai_doan
        
    truc_toa_do.set_ylabel(ten_chi_so_hien_thi, fontsize=12)
    truc_toa_do.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Hiển thị bảng chú giải (Legend) ở góc ngoài cùng bên phải
    truc_toa_do.legend(title="Chú giải Giai đoạn", loc='upper left', bbox_to_anchor=(1.01, 1))
    
    # Cấu hình nhãn ngày tháng trục X cho khỏi vướng
    truc_x_duoi_dang_so_dem = np.arange(len(danh_sach_ngay_thuc_te_de_ve))
    buoc_nhay_hien_thi_nhan = max(1, len(danh_sach_ngay_thuc_te_de_ve) // 30) 
    danh_sach_vi_tri_dat_nhan = truc_x_duoi_dang_so_dem[::buoc_nhay_hien_thi_nhan]
    
    # Cắt lấy ngày/tháng (bỏ năm) bằng vòng lặp for
    danh_sach_nhan_ngay_thang = []
    for vi_tri in danh_sach_vi_tri_dat_nhan:
        ngay_day_du = danh_sach_ngay_thuc_te_de_ve[vi_tri]
        ngay_thang_ngan_gon = ngay_day_du[-5:] # Cắt 5 ký tự cuối cùng
        danh_sach_nhan_ngay_thang.append(ngay_thang_ngan_gon)
    
    plt.xticks(danh_sach_vi_tri_dat_nhan, danh_sach_nhan_ngay_thang, rotation=45, ha='right', fontsize=10)
    plt.title(f"Biểu đồ phân tích Cắt Giai Đoạn dựa theo: {ten_chi_so_hien_thi}", fontsize=16)
    
    # Tự động căn chỉnh lại bố cục để bảng chú giải không bị lẹm ra ngoài khung
    plt.tight_layout()
    
    return khung_tranh
