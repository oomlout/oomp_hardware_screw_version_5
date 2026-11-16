import copy


def generate(**kwargs):
    options = []

    current_taxonomy_3 = "machine_screw"

    # pozidrive, no colour
    pozi_sizes = {}
    pozi_sizes["m2"] = [4, 6, 8, 10, 12]
    pozi_sizes["m3"] = [4, 5, 6, 8, 10, 12, 16, 20, 25, 30, 35, 40]
    pozi_sizes["m3_5"] = [5, 8, 10, 12, 16, 20, 25]
    pozi_sizes["m4"] = [5, 6, 8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100]
    pozi_sizes["m5"] = [6, 8, 10, 12, 14, 16, 20, 25, 30, 35, 40, 50, 60, 80, 100]
    pozi_sizes["m6"] = [8, 10, 12, 16, 20, 25, 30, 35, 40, 100, 120]

    for extra_size in pozi_sizes:
        for extra_size2 in pozi_sizes[extra_size]:
            option = {}
            option["taxonomy_3"] = current_taxonomy_3
            option["taxonomy_4"] = "pozidriv"
            option["taxonomy_5"] = ""
            option["taxonomy_6"] = f"{extra_size}_diameter"
            option["taxonomy_7"] = f"{extra_size2}_mm_length"
            options.append(copy.deepcopy(option))

    # philips, nylon_white
    philips_nylon_sizes = {}
    philips_nylon_sizes["m3"] = [12, 16, 20, 25]

    for extra_size in philips_nylon_sizes:
        for extra_size2 in philips_nylon_sizes[extra_size]:
            option = {}
            option["taxonomy_3"] = current_taxonomy_3
            option["taxonomy_4"] = "philips"
            option["taxonomy_5"] = "nylon_white"
            option["taxonomy_6"] = f"{extra_size}_diameter"
            option["taxonomy_7"] = f"{extra_size2}_mm_length"
            options.append(copy.deepcopy(option))

    return options


if __name__ == "__main__":
    for o in generate():
        print(o)
