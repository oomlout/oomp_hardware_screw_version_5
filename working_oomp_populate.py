import copy
import itertools

from requests import options

from oomp_populate_helper import write_extras


def main(**kwargs):
    # Define default input dict with all required fields
    default_input = {
        "taxonomy_1": "hardware",
        "taxonomy_2": "screw",
        "taxonomy_3": "",
        "taxonomy_4": "",
        "taxonomy_5": "",
        "taxonomy_6": "",
        "taxonomy_7": "",
        "taxonomy_8": "",
        # Add any additional details here
    }
     
    
    #### define extra entries
    #taxonomy_3 style           countersunk, grub, machine_screw, self_tapping, socket_cap, wood    
    #taxonomy_4 drive type      hex_head, philips, pozidriv, slotted, torx
    #taxonomy_5 colour          black
    #taxonomy_6 thread size     m3, m4, m5
    #taxonomy_7 length         10mm, 20mm, 30mm
    #taxonomy_14 manufacturer
    #taxonomy_15 manufacturer_part_number
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
        options.append({"taxonomy_4": "80_gsm",       "taxonomy_5": "green_flourescent",  "taxonomy_14": "papago",    "taxonomy_15": "21403"})
        

    #################### for this project
    #countersunk hex head black
    if True:        
        current_taxonomy_3 = "countersunk"
        current_taxonomy_4 = "hex_head"
        current_taxonomy_5 = "black"
        extras_sizes = {}
        extras_sizes["m2"] = [3,5,6,8,10,12,14,16,20,22,25]
        extras_sizes["m3"] = [4,5,6,8,10,12,16,20,25,30,35]
        extras_sizes["m4"] = [6,8,10,12,16,20,25,30,35,40]   

        for extra_size in extras_sizes:
            for extra_size2 in extras_sizes[extra_size]:
                option = {}
                option["taxonomy_3"] = current_taxonomy_3
                option["taxonomy_4"] = current_taxonomy_4
                option["taxonomy_5"] = current_taxonomy_5
                option["taxonomy_6"] = f"{extra_size}_diameter"
                option["taxonomy_7"] = f"{extra_size2}_mm_length"
                options.append(copy.deepcopy(option))
    
    #socket_cap hex head black
    if True:        
        current_taxonomy_3 = "socket_cap"
        current_taxonomy_4 = "hex_head"
        current_taxonomy_5 = "black"
        extras_sizes = {}
        extras_sizes["m2"] = [3,4,5,6,8,10,12,14,16,18,20,25]
        extras_sizes["m2_5"] = [4,5,6,8,10,12,16,20,25]
        extras_sizes["m3"] = [5,6,8,10,12,18,16,20,25,30,35,40,45,50,60]
        extras_sizes["m4"] = [4,6,8,10,12,14,16,20,25,30,35,40,45,50,60,65,70,75]
        extras_sizes["m5"] = [6,8,10,12,14,16,20,25,30,35,40,45,50,60,65,70,75,80,90,100,110,120]
        extras_sizes["m6"] = [8,12,16,20,25,30,35,40,45,50,60,65,70,80,90,100]  

        for extra_size in extras_sizes:
            for extra_size2 in extras_sizes[extra_size]:
                option = {}
                option["taxonomy_3"] = current_taxonomy_3
                option["taxonomy_4"] = current_taxonomy_4
                option["taxonomy_5"] = current_taxonomy_5
                option["taxonomy_6"] = f"{extra_size}_diameter"
                option["taxonomy_7"] = f"{extra_size2}_mm_length"
                #### extra specific ones
                if True:
                    option["thread_size"] = extra_size
                    option["length"] = extra_size2
                    screw_style = f"{default_input['taxonomy_2']}_{option['taxonomy_3']}"
                    option["screw_style"] = screw_style                    
                options.append(copy.deepcopy(option))


    #add oobb_details
    if True:
        for option in options:
            #option = options[option_id]
            oobb_details = {}
            oobb_details["oobb_name"] = "screw"
            oobb_details["thread_size"] = option.get("taxonomy_6", "default")
            oobb_details["length"] = option.get("taxonomy_7", "default")
            oobb_details["drive_style"] = option.get("taxonomy_4", "default")
            oobb_details["screw_style"] = option.get("taxonomy_3", "default")
            oobb_details["screw_colour"] = option.get("taxonomy_5", "default")
            option["oobb_details"] = oobb_details

    #define loop parts here
    if False:
        options = looping_options(default_input, options)

    #define oobb parts here
    if False:
        option = {}
        option["oobb"] = True
        option["width"] = 5
        option["height"] = 6
        option["depth"] = 21
        #name oobb_holder
        option["oobb_name"] = "holder"
        options.append(option)

    extras = []
    for option in options:
        extra = copy.deepcopy(default_input)
        extra.update(option)
        
        
        extras.append(extra)



    write_extras(extras, default_input)



# Call main automatically
if __name__ == "__main__":
    main()