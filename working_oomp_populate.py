import copy

from oomp_populate_helper import write_extras
from working_oomp_populate_countersunk import generate as generate_countersunk
from working_oomp_populate_countersunk_pozi import generate as generate_countersunk_pozi
from working_oomp_populate_countersunk_philips import generate as generate_countersunk_philips
from working_oomp_populate_socket_cap import generate as generate_socket_cap
from working_oomp_populate_socket_cap_low_head import generate as generate_socket_cap_low_head
from working_oomp_populate_socket_cap_low_head_ultra import generate as generate_socket_cap_low_head_ultra
from working_oomp_populate_flat_head import generate as generate_flat_head
from working_oomp_populate_button_head import generate as generate_button_head
from working_oomp_populate_grub import generate as generate_grub
from working_oomp_populate_machine_screw import generate as generate_machine_screw
from working_oomp_populate_self_tapping import generate as generate_self_tapping
from working_oomp_populate_thread_forming import generate as generate_thread_forming
from working_oomp_populate_wood import generate as generate_wood


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
    options += generate_countersunk()
    options += generate_countersunk_pozi()
    options += generate_countersunk_philips()
    options += generate_socket_cap()
    options += generate_socket_cap_low_head()
    options += generate_socket_cap_low_head_ultra()
    options += generate_flat_head()
    options += generate_button_head()
    options += generate_grub()
    options += generate_machine_screw()
    options += generate_self_tapping()
    options += generate_thread_forming()
    options += generate_wood()


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