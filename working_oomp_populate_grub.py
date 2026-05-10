import copy


def generate(**kwargs):
    options = []

    current_taxonomy_3 = "grub"
    current_taxonomy_4 = "hex_head"

    extras_sizes = {}
    extras_sizes["m1_6"] = [2, 2.5, 3, 4, 5, 8]
    extras_sizes["m2"] = [2, 2.5, 3, 4, 5, 6, 8, 10, 12, 14]
    extras_sizes["m2_5"] = [2, 2.5, 3, 4, 5, 6, 8, 10, 12, 14]
    extras_sizes["m3"] = [2, 2.5, 3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20]
    extras_sizes["m4"] = [3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20]
    extras_sizes["m5"] = [3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 25, 30, 35]
    extras_sizes["m6"] = [6, 8, 10, 12, 14, 16, 18, 20, 30, 40]

    colors = ["black", "stainless_steel"]

    for current_taxonomy_5 in colors:
        for extra_size in extras_sizes:
            for extra_size2 in extras_sizes[extra_size]:
                length_str = str(extra_size2).replace(".", "_")
                option = {}
                option["taxonomy_3"] = current_taxonomy_3
                option["taxonomy_4"] = current_taxonomy_4
                option["taxonomy_5"] = current_taxonomy_5
                option["taxonomy_6"] = f"{extra_size}_diameter"
                option["taxonomy_7"] = f"{length_str}_mm_length"
                options.append(copy.deepcopy(option))

    return options


if __name__ == "__main__":
    for o in generate():
        print(o)
