import copy


def generate(**kwargs):
    options = []

    current_taxonomy_3 = "socket_cap_low_head_ultra"
    current_taxonomy_4 = "hex_head"
    current_taxonomy_5 = "black"

    extras_sizes = {}
    extras_sizes["m2"] = [3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 25]
    extras_sizes["m2_5"] = [4, 5, 6, 8, 10, 12, 16, 20, 25]
    extras_sizes["m3"] = [5, 6, 8, 10, 12, 18, 16, 20, 25, 30, 35, 40, 45, 50, 60]
    extras_sizes["m4"] = [4, 6, 8, 10, 12, 14, 16, 20, 25, 30, 35, 40, 45, 50, 60, 65, 70, 75]
    extras_sizes["m5"] = [6, 8, 10, 12, 14, 16, 20, 25, 30, 35, 40, 45, 50, 60, 65, 70, 75, 80, 90, 100, 110, 120]
    extras_sizes["m6"] = [8, 12, 16, 20, 25, 30, 35, 40, 45, 50, 60, 65, 70, 80, 90, 100]

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
