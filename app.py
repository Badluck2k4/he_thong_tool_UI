def get_tier_seasons(all_data, id_tuoi, tier_step=5, min_days=5, max_cap=40):
    fmt = "%Y-%m-%d %H-%M-%S"
    data_tuoi = [d for d in all_data if str(d.get('STT')) == str(id_tuoi)]
    if not data_tuoi: return []

    daily_counts = {}
    for d in data_tuoi:
        dt = datetime.strptime(d['Thời gian'], fmt).date()
        daily_counts[dt] = daily_counts.get(dt, 0) + 1
    
    sorted_days = sorted(daily_counts.keys())
    if not sorted_days: return []

    seasons = []
    curr_start = sorted_days[0]
    
    # Hàm xác định "Bậc" tần suất (ví dụ: 23 lần -> bậc 20, 27 lần -> bậc 25)
    def get_tier(d):
        v = daily_counts[d]
        v = v if v <= max_cap else max_cap
        return (v // tier_step) * tier_step

    curr_tier = get_tier(curr_start)
    
    for i in range(1, len(sorted_days)):
        d_p, d_c = sorted_days[i-1], sorted_days[i]
        tier_c = get_tier(d_c)
        gap = (d_c - d_p).days
        
        # Ngắt khi nhảy bậc HOẶC nghỉ quá lâu
        if tier_c != curr_tier or gap > 3:
            duration = (d_p - curr_start).days + 1
            if duration >= min_days:
                # Tính trung bình thực tế của giai đoạn để hiển thị
                avg_val = sum(daily_counts[day] for day in sorted_days if curr_start <= day <= d_p) / duration
                seasons.append({
                    "Bắt đầu": curr_start,
                    "Kết thúc": d_p,
                    "Tần suất": round(avg_val)
                })
                curr_start = d_c
                curr_tier = tier_c
    
    # Giai đoạn cuối
    seasons.append({"Bắt đầu": curr_start, "Kết thúc": sorted_days[-1], 
                    "Tần suất": round(daily_counts[sorted_days[-1]])})
    return seasons
