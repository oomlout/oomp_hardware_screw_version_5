import copy


def generate(**kwargs):
    options = []

    current_taxonomy_3 = "countersunk"
    current_taxonomy_4 = "philips"
    current_taxonomy_5 = "black"

    extras_sizes = {}
    extras_sizes["m1_4"] = [3, 4, 5, 6, 8, 10]
    extras_sizes["m1_5"] = [3, 4, 5, 6, 8, 10]
    extras_sizes["m1_6"] = [3, 4, 5, 6, 8, 10]
    extras_sizes["m2"] = [3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22, 25, 30]

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
