import working_oomp_populate

def main(**kwargs):
    extras = kwargs.get("extras", [])
    extras_dict = {}
    for extra in extras:
        oomp_id =  working_oomp_populate.build_oomp_id(extra)
        extras_dict[oomp_id] = extra

    ######add colour bands to tray
    types = []
    current_band_1 = "red"
    styles = {}
    #countersunk
    if True:
        styles["countersunk"] = {}
        styles["countersunk"]["band_1"] = "red"
        band_2 = {}
        band_2["6_mm_length"] = "brown"
        band_2["8_mm_length"] = "red"
        band_2["10_mm_length"] = "orange"
        band_2["12_mm_length"] = "yellow"
        band_2["16_mm_length"] = "green"
        band_2["20_mm_length"] = "blue"
        band_2["25_mm_length"] = "purple"
        styles["countersunk"]["band_2"] = band_2
    
    for option in styles:
        style = option
        band_1 = styles[option]["band_1"]
        for option2 in styles[option]["band_2"]:
            band_2 = styles[option]["band_2"][option2]
            oomp_id = f"hardware_screw_{style}_hex_head_black_m3_diameter_{option2}"
            if oomp_id in extras_dict:
                extras_dict[oomp_id]["band_1"] = band_1
                extras_dict[oomp_id]["band_2"] = band_2
                extras_dict[oomp_id]["band_string"] = f"colour_band_{band_1}_{band_2}"
    pass
                
        
    