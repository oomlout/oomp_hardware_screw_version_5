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
        band_3 = {}
        band_3["m2"] = "brown"
        band_3["m2_5"] = "red"
        band_3["m2_7"] = "orange"
        band_3["m3"] = "yellow"
        band_3["m4"] = "green"
        band_3["m5"] = "blue"
        band_3["m6"] = "purple"
        band_3["m8"] = "grey"
        band_3["m10"] = "white"
        styles["countersunk"]["band_3"] = band_3
    for option in styles:
        style = option
        band_1 = styles[option]["band_1"]
        for option2 in styles[option]["band_2"]:
            band_2 = styles[option]["band_2"][option2]
            for option3 in styles[option]["band_3"]:
                band_3 = styles[option]["band_3"][option3]
                oomp_id = f"hardware_screw_{style}_hex_head_black_{option3}_diameter_{option2}"
                if oomp_id in extras_dict:
                    extras_dict[oomp_id]["color_band_1_project_bolt"] = band_1
                    extras_dict[oomp_id]["color_band_1_taxonomy_3"] = band_1
                    extras_dict[oomp_id]["color_band_2_project_bolt"] = band_2
                    extras_dict[oomp_id]["color_band_2_taxonomy_7"] = band_2                    
                    extras_dict[oomp_id]["color_band_3_project_bolt"] = band_3
                    extras_dict[oomp_id]["color_band_3_taxonomy_6"] = band_3
                    extras_dict[oomp_id]["color_band_string_project_bolt"] = f"colour_band_{band_1}_{band_2}_{band_3}"
    pass
                
        
    