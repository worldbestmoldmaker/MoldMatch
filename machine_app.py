def check(machine):
    reasons = []

    # Length check
    platen_x = machine.get("Platen X (mm)")
    if pd.notna(platen_x) and mold_length > platen_x:
        reasons.append("Too long")

    # Width check
    tie_y = machine.get("Tie Bar Y (mm)")
    platen_y = machine.get("Platen Y (mm)")
    if pd.notna(tie_y):
        if mold_width > tie_y:
            reasons.append("Too wide")
    elif pd.notna(platen_y):
        if mold_width > platen_y:
            reasons.append("Too wide")

    # Thickness / opening check
    mold_min = machine.get("Mold Min (mm)", 0)
    daylight_max = machine.get("Daylight Max (mm)", 9999)

    if pd.notna(mold_min) and mold_height < mold_min:
        reasons.append("Too thin")

    if pd.notna(daylight_max) and required_opening > daylight_max:
        reasons.append("Too thick")

    # ✅ Optional clamp check
    if clamp_required is not None:
        if machine.get("Clamp Force (ton)", 0) < clamp_required:
            reasons.append("Insufficient clamp")

    # Daylight check (avoid duplicate message)
    daylight = machine.get("Daylight Max (mm)", 0)
    if pd.notna(daylight) and required_opening > daylight:
        if "Too thick" not in reasons:
            reasons.append("Insufficient daylight")

    return "PASS" if not reasons else "FAIL", ", ".join(reasons)