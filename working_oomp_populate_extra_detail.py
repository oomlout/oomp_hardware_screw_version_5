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
        style_colors = {}
        style_colors["countersunk"] = "red"
        style_colors["socket_cap"] = "orange"                
        length_colors = {}
        length_colors["6_mm_length"] = "brown"
        length_colors["8_mm_length"] = "red"
        length_colors["10_mm_length"] = "orange"
        length_colors["12_mm_length"] = "yellow"
        length_colors["16_mm_length"] = "green"
        length_colors["20_mm_length"] = "blue"
        length_colors["25_mm_length"] = "purple"
        
        thread_colors = {}
        thread_colors["m2"] = "brown"
        thread_colors["m2_5"] = "red"
        thread_colors["m2_7"] = "orange"
        thread_colors["m3"] = "yellow"
        thread_colors["m4"] = "green"
        thread_colors["m5"] = "blue"
        thread_colors["m6"] = "purple"
        thread_colors["m8"] = "grey"
        thread_colors["m10"] = "white"
        
        styles = {}
        if True:
            styles["countersunk"] = {}
            styles["countersunk"]["band_2"] = thread_colors
            styles["countersunk"]["band_1"] = length_colors
        if True:
            styles["socket_cap"] = {}
            styles["socket_cap"]["band_2"] = thread_colors
            styles["socket_cap"]["band_1"] = length_colors
    
    for style in styles:
        band_1_color = style_colors[style]
        band_1_string = style.replace("_", " ")
        band_2_list = styles[style]["band_2"]
        for band_2 in band_2_list:
            band_2_color = styles[style]["band_2"][band_2]
            band_2_string = band_2.replace("_", " ")
            band_3_list = styles[style]["band_1"]
            for band_3 in band_3_list:
                band_3_color = styles[style]["band_1"][band_3]
                band_3_string = band_3.replace("_", " ")    
                oomp_id = f"hardware_screw_{style}_hex_head_black_{band_2}_diameter_{band_3}"
                if oomp_id in extras_dict:
                    extras_dict[oomp_id]["color_band_project_bolt_1"] = band_3_color
                    extras_dict[oomp_id]["color_band_project_bolt_1_string"] = band_3_string
                    extras_dict[oomp_id]["color_band_taxonomy_3"] = band_3_color
                    extras_dict[oomp_id]["color_band_project_bolt_2"] = band_2_color
                    extras_dict[oomp_id]["color_band_project_bolt_2_string"] = band_2_string
                    extras_dict[oomp_id]["color_band_taxonomy_7"] = band_2_color                    
                    extras_dict[oomp_id]["color_band_project_bolt_3"] = band_1_color
                    extras_dict[oomp_id]["color_band_project_bolt_3_string"] = band_1_string
                    extras_dict[oomp_id]["color_band_taxonomy_6"] = band_1_color
                    extras_dict[oomp_id]["color_band_string_project_bolt"] = f"colour_band_{band_1_color}_{band_2_color}_{band_3_color}"

    
    pass
                
        
    