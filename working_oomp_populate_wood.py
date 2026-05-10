import copy


def generate(**kwargs):
    options = []

    current_taxonomy_3 = "wood"
    current_taxonomy_4 = "pozidriv"
    current_taxonomy_5 = "bright_zinc_plated"

    extras_sizes = {}
    extras_sizes["m2"] = [4, 5, 6, 8, 10, 12, 16]
    extras_sizes["m2_5"] = [5, 6, 8, 10, 12, 16, 20]
    extras_sizes["m3"] = [5, 6, 8, 10, 12, 16, 20, 25]
    extras_sizes["m3_5"] = [8, 10, 12, 16]
    extras_sizes["m4"] = [6, 8, 10, 12, 16, 20, 25, 30, 40, 50, 60]
    extras_sizes["m5"] = [8, 10, 12, 14, 16, 20, 25, 30, 35, 40, 50, 60, 70, 80, 100]
    extras_sizes["m6"] = [10, 12, 16, 20, 25, 30, 40, 100, 120]

    for extra_size in extras_sizes:
        for extra_size2 in extras_sizes[extra_size]:
            option = {}
            option["taxonomy_3"] = current_taxonomy_3
            option["taxonomy_4"] = current_taxonomy_4
            option["taxonomy_5"] = current_taxonomy_5
            option["taxonomy_6"] = f"{extra_size}_diameter"
            option["taxonomy_7"] = f"{extra_size2}_mm_length"
            options.append(copy.deepcopy(option))

    return options


if __name__ == "__main__":
    for o in generate():
        print(o)
