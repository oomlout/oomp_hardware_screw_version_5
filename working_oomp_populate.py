
import copy
import itertools

from requests import options

from oomp_populate_helper import write_extras


def main(**kwargs):
    # Define default input dict with all required fields
    default_input = {
        "taxonomy_1": "decoration",
        "taxonomy_2": "party",
        "taxonomy_3": "",
        "taxonomy_4": "",
        "taxonomy_5": "",
        "taxonomy_6": "",
        "taxonomy_7": "",
        "taxonomy_8": "",
        "taxonomy_9": "",
        "taxonomy_10": "",
        # Add any additional details here
    }
     
    
    #### define extra entries
    #taxonomy_3 
    #taxonomy_4 
    #taxonomy_5 diameter
    #taxonomy_6 depth
    #taxonomy_7 hole_top_diameter
    #taxonomy_14 manufacturer
    #taxonomy_15 manufacturer_part_number
    oobb_details_add = []
    
    options = []
    #define single parts (take the default options add one with the extra details)
    option = {}
    

    ############################# examples
    #flourescent green # multiline example
    if False:        
        #taxonomy_4 80 gsm        
        option["taxonomy_4"] = "80_gsm"
        option["taxonomy_5"] = "green_flourescent"
        option["taxonomy_14"] = "papago"
        option["taxonomy_15"] = "21403"
        options.append(copy.deepcopy(option))
    
    #flourescent green # singleline example
    if False:
            # taxonomy_4 80 gsm                
        options.append({"taxonomy_4": "80_gsm",       "taxonomy_5": "green_flourescent",  "taxonomy_14": "papago",    "taxonomy_15": "21403"})
    if False:    
        #furniture
        if True:
            #shelf
            if True:
                #ikea
                if True:
                    #billy
                    options.append({"taxonomy_1": "furniture", "taxonomy_2": "shelf", "taxonomy_3": "ikea", "taxonomy_4": "billy", "taxonomy_5": "400_mm_width_1060_mm_height_280_mm_depth", "taxonomy_14": "ikea", "taxonomy_15": "802_638_32", "url_source": "https://www.ikea.com/gb/en/p/billy-bookcase-white-80263832/"})
                    options.append({"taxonomy_1": "furniture", "taxonomy_2": "shelf", "taxonomy_3": "ikea", "taxonomy_4": "billy", "taxonomy_5": "400_mm_width_2020_mm_height_280_mm_depth", "taxonomy_14": "ikea", "taxonomy_15": "502_638_38", "url_source": "https://www.ikea.com/gb/en/p/billy-bookcase-white-50263838/"})
                    options.append({"taxonomy_1": "furniture", "taxonomy_2": "shelf", "taxonomy_3": "ikea", "taxonomy_4": "billy", "taxonomy_5": "800_mm_width_1060_mm_height_280_mm_depth", "taxonomy_14": "ikea", "taxonomy_15": "302_638_44", "url_source": "https://www.ikea.com/gb/en/p/billy-bookcase-white-30263844/"})
                    options.append({"taxonomy_1": "furniture", "taxonomy_2": "shelf", "taxonomy_3": "ikea", "taxonomy_4": "billy", "taxonomy_5": "800_mm_width_2020_mm_height_280_mm_depth", "taxonomy_14": "ikea", "taxonomy_15": "002_638_50", "url_source": "https://www.ikea.com/gb/en/p/billy-bookcase-white-00263850/"})
                    options.append({"taxonomy_1": "furniture", "taxonomy_2": "shelf", "taxonomy_3": "ikea", "taxonomy_4": "billy", "taxonomy_5": "800_mm_width_2020_mm_height_400_mm_depth", "taxonomy_14": "ikea", "taxonomy_15": "904_019_32", "url_source": "https://www.ikea.com/gb/en/p/billy-bookcase-white-90401932/"})
                    options.append({"taxonomy_1": "furniture", "taxonomy_2": "shelf", "taxonomy_3": "ikea", "taxonomy_4": "billy", "taxonomy_5": "800_mm_width_2370_mm_height_280_mm_depth", "taxonomy_14": "ikea", "taxonomy_15": "591_822_01", "url_source": "https://www.ikea.com/gb/en/p/billy-bookcase-white-s59182201/"})
                    
    ########################### real
    if True:
          
        option["person"] = "maya"
        option["reason"] = "birthday"
        option["age"] = "6"
        option["theme_1"] = "star"
        option["theme_2"] = ""
        option["theme_3"] = ""
        option["theme_4"] = ""
        option["theme_5"] = ""
        options.append(copy.deepcopy(option))
        
    #load from working_manual.yaml
    if False:
        with open("working_manual.yaml", 'r', encoding='utf-8') as file:
            import yaml
            data = yaml.safe_load(file)
            options_yaml = data.get("options", [])
            for option_yaml in options_yaml:
                options.append(option_yaml)

    
    ###### populate taxonomy details and oobb details
    if True:
        for option in options:            
            option["taxonomy_3"] = f"{option.get('reason', '')}_reason"
            option["taxonomy_4"] = f"{option.get('age', '')}_age"
            theme_string = ""
            for i in range(1, 6):
                theme_string += f"{option.get(f'theme_{i}', '')}_"
            theme_string = theme_string.rstrip("_")          
            option["taxonomy_5"] = f"{theme_string}_theme"
            option["taxonomy_6"] = f"{option.get('person', '')}_person"
            if False:
                pass
                oobb_details = {}
                #taxonomy_4 hole_cover
                oobb_details["oobb_name"] = option_type
                oobb_details["diameter"] = option.get("diameter", None)            
                oobb_details["depth"] = option.get("depth", None)
                option["oobb_details"] = oobb_details
    

    #load the options into full list
    extras = []
    for option in options:
        extra = copy.deepcopy(default_input)
        extra.update(option)
        extras.append(extra)



    write_extras(extras, default_input)



# Call main automatically
if __name__ == "__main__":
    main()
