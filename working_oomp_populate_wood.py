"""Screwfix Screw-Tite 2 individual-size packs, checked 2026-10-13.

Source: https://www.screwfix.com/c/screws-nails-fixings/woodscrews/cat840066?brand=screw_tite_2
Mixed trade packs are excluded. Codes are Screwfix codes, not TFST manufacturer
SKUs. Only verified diameter/length pairs are emitted.
"""

FINISH = "net_coat_yellow_plated"
FINISH_NAME = "Net-Coat Yellow-Plated"
PRODUCTS = {
    "3": [(12, "304FY", 200)],
    "3.5": [(16, "419FY", 200), (20, "710FY", 200), (25, "310FY", 200),
            (30, "488FY", 200), (35, "167FY", 200), (40, "130FY", 200), (50, "726FY", 200)],
    "4": [(20, "659FY", 200), (25, "592FY", 200), (30, "284FY", 200),
          (35, "107FY", 200), (40, "330FY", 200), (50, "127FY", 200),
          (60, "258FY", 100), (70, "131FY", 100)],
    "4.5": [(50, "731FY", 200), (60, "509FY", 200), (70, "280FY", 200),
            (75, "986FY", 100), (80, "713FY", 100)],
    "5": [(40, "819FY", 200), (50, "984FY", 200), (60, "784FY", 100),
          (70, "964FY", 100), (80, "426FY", 100), (90, "800FY", 100), (100, "486FY", 100)],
    "6": [(100, "101FY", 50), (120, "771FY", 50)],
}


def generate(**kwargs):
    options = []
    for diameter, products in PRODUCTS.items():
        for length, code, pack_size in products:
            url = ("https://www.screwfix.com/p/screw-tite-2-pz-double-countersunk-thread-cutting-screws-"
                   f"{diameter.replace('.', '-')}mm-x-{length}mm-{pack_size}-pack/{code.lower()}")
            options.append(dict(
                taxonomy_3="wood", taxonomy_4="pozidriv", taxonomy_5=FINISH,
                taxonomy_6=f"m{diameter.replace('.', '_')}_diameter",
                taxonomy_7=f"{length}_mm_length", taxonomy_14="screwtite", taxonomy_15=code,
                manufacturer="screwtite", part_number=code, finish=FINISH_NAME,
                supplier_data={"screwfix": dict(supplier="screwfix", supplier_id=code,
                    supplier_part_number=code, supplier_website=url, pack_size=pack_size,
                    brand="Screw-Tite 2", finish=FINISH_NAME, checked_on="2026-10-13")}))
    return options


if __name__ == "__main__":
    for option in generate():
        print(option)
