This catalogue entry is needs_specification.

Head dimensions and pitches use the user-selected diagram plus explicit 0.3 mm pitch overrides for 1 and 1.2 mm. Black catalogue finish is retained. Core, point and recess geometry remain unspecified; no solid is generated yet.

Verified reference information (not model inputs):

- head_style: pan
- drive_style: philips
- reference_finish: black zinc
- material: carbon steel
- application: sheet metal (seller description)
- comparative_supplier_table: {'source': 'https://www.ebay.co.uk/itm/377271086738', 'units': 'mm', 'length_convention': 'excludes_head', 'reference_material': 'A4/316 stainless steel', 'measurement_basis': 'Seller reports manual batch measurements with possible error.', 'columns': ['diameter_mm', 'pitch_mm', 'head_diameter_mm', 'head_height_mm'], 'rows': {'1': [1.0, None, 1.75, 0.65], '1.2': [1.2, None, 1.9, 0.6], '1.4': [1.4, 0.5, 2.3, 0.8], '1.7': [1.7, 0.5, 3.1, 1.0], '2': [2.0, 0.6, 3.4, 1.3], '2.2': [2.2, 0.8, 3.8, 1.5], '2.6': [2.6, 0.9, 4.2, 1.7], '3': [3.0, 1.1, 5.3, 1.9], '3.5': [3.5, 1.3, 6.4, 2.1], '4': [4.0, 1.3, 6.9, 2.3], '4.2': [4.2, 1.4, 7.8, 2.4], '5': [5.0, 1.6, 9.0, 2.8], '6': [6.0, 1.8, 11.9, 4.0], '8': [8.0, 2.1, 13.0, 5.0]}, 'limitations': ['Null pitch means a dash in the diagram, not zero.', 'No 2.3 mm row; user explicitly corrected catalogue entries to 2.2 mm on 2026-10-13.', 'No core diameter/profile, point dimensions or numeric recess dimensions.', 'Diagram rows do not establish stock lengths or a match to the black-zinc screws.']}
- diameter_mm: 1.0
- head_diameter_mm: 1.75
- head_height_mm: 0.65
- pitch_mm: 0.3
- pitch_source: {'pitch_mm': 0.3, 'specified_on': '2026-10-13', 'basis': 'User specified 0.3 mm pitch; the supplier diagram leaves this blank.'}

Still required:

- Tapping core diameter and flank/root profile
- Point/taper, threaded length and recess dimensions

Geometry implementation required:

- A dedicated non-metric tapping profile and point builder after dimensions are confirmed.

Sources:

- [User reference eBay 383102775525](https://www.ebay.co.uk/itm/383102775525)
- [User reference AliExpress 1005004774076999](https://www.aliexpress.com/item/1005004774076999.html)
- [Screw Express micro plastic screw 1.4 x 5](https://www.screw-express.com/micro-screw-self-tapping-pan-head-phillips-steel/61840-530259-self-tapping-screw-linch-pin-plastic-pan-head-phillips-0-14x5-black-zinc-plated-micro-screw.html)
- [Japanese Screws supplier brochure, printed pages 6-7](https://prokcssmedia.blob.core.windows.net/sys-master-images/h22/hd6/9138373263390/JAP%20SCREWS%20Brochure.pdf)
- [User reference eBay 377271086738, gallery image 6](https://www.ebay.co.uk/itm/377271086738)
