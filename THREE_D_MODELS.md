# Parametric screw models and generation

Reference repository: `C:\gh\oomp_hardware_screw_version_5`.
The generator is independent of the legacy OOBB/OpenSCAD geometry. It uses Python,
NumPy, trimesh and manifold3d for watertight mesh solids, and Blender/Cycles for
the product studio. Source inspection dates: 2026-10-11 through 2026-10-13.

## Current coverage and generation order

| Priority | Catalogue family | Parts | Definition | State |
|---|---|---:|---|---|
| 5 (existing) | countersunk, hex | 32 | DIN 7991; sourced M2 extension | Ready |
| 1 | socket_cap | 92 | ISO 4762:2004 reference geometry / DIN 912 family | Ready |
| 2 | socket_cap_low_head | 92 | DIN 7984 supplier dimension table | Ready |
| 3 | button_head | 79 | ISO 7380-1; M2/M2.5 manufacturer extensions | Ready |
| 4 | grub | 148 | Cup point, DIN 916 / ISO 4029 supplier dimensions | Ready |
| 5 | countersunk, cross recess | 88 | DIN 965 A, H/Z; separate M1.4 supplier reference | Ready |
| 6 | flat_head | 79 | Countersunk DIN 965 A, confirmed by user | Ready |
| 7 | machine_screw | 72 | Pan head DIN 7985 A, confirmed by user | Ready |
| 8 | socket_cap_low_head_ultra | 92 | DIN 7984, confirmed by user | Ready; same profile as low head |
| 9 | wood | 30 | Screwfix Screw-Tite codes and Net-Coat Yellow-Plated finish; HSB/Motu geometry | Ready as labelled visualization proxies |
| 10 | self_tapping | 26 | Supplied head/pitch dimensions; user-authorized core, point and recess estimates | Ready as labelled visual approximations |
| Excluded | thread_forming | 3 | User requested skipping this family | Excluded |

Totals: **830 ready, 0 needing specification, 3 explicitly excluded** (833 parts). A ready
recipe describes sourced nominal visualization geometry, not manufacturing
certification or proof that a catalogue item was manufactured to the standard.
Unlisted catalogue lengths remain drawable but carry `catalogue_length_extension`.
Miniature extensions and supplier dimensions are distinguished from standard rows.

The generator orders families by priority, starting with socket caps. The
dedicated socket-cap batch restricts generation to the 92 socket
caps, so that family can be produced first without starting the whole catalogue.

## Run on Windows

Install Python 3.12 and Blender 4.5 or newer, then from this repository:

```bat
python -m pip install -r requirements-three-d-model.txt
action_check_three_d_model.bat
action_prepare_three_d_model.bat
action_make_socket_cap_three_d_model.bat
```

Preparation refreshes missing/pending recipes, writes model inputs and copies the
standalone Python source into each ready part's `three_d_model` folder. It starts
no mesh generation or renders. Specification requests are written into the same
folder for pending/excluded parts. `action_check_three_d_model.bat` checks inputs
without Blender and writes `three_d_model_coverage.json` with every part and gap.

To recreate all ready models, renders, SVGs and studios:

```bat
action_make_three_d_model.bat
```

That batch forces regeneration of ready assets. Pending and excluded entries are
reported and skipped; their request files are retained. Blender runs headlessly
and the batch stays open until it finishes, returning a nonzero error code on
failure. The default is one worker to limit GPU memory pressure. Override it or
restrict the selection as needed:

```bat
action_make_three_d_model.bat --jobs 3
action_make_three_d_model.bat --filter "hardware_screw_button_head_*"
python working_three_d_model.py --ensure-metadata --filter "hardware_screw_grub_*"
```

The Python command without `--force` checks the complete artifact hashes and
reuses intact cached builds. All shortcuts use their own repository directory,
so they can be launched from another working directory. Set `OOMP_BLENDER_EXE`
when Blender is installed outside its usual folder. An available GPU is selected
automatically; CPU is the fallback.

Delete just the generated `three_d_model` folders of all products:

```bat
action_delete_three_d_model.bat -WhatIf
action_delete_three_d_model.bat
```

The PowerShell implementation checks absolute paths and rejects linked folders.
Recipes in `working.yaml` are retained. Regeneration recreates the output folders,
including the requests for unresolved entries.

Generated metadata is serialized completely and published atomically by
`working_metadata.py`. `working_oomp.py` completes each OOMP registration before
publishing its YAML, instead of starting unjoined background writers. Parse errors
in the 3D batch identify the actual file and line. To recover damaged generated
working metadata from an intact, matching `thing.yaml`, run this explicit
maintenance command:

```bat
python working_metadata.py --repair-generated
```

It leaves valid files and source definitions unchanged, checks companion part IDs,
and retains original bytes and a report under `metadata_recovery_backups/`.
Recovery does not generate meshes or renders.

## Per-part outputs

Every ready `parts/<part_id>/three_d_model` folder has these portable inputs after
preparation: `model.py`, `parameters.json`, `requirements.txt`. A complete build adds:

- `model_full.stl`, `model_full.glb`, `model_display.stl`, `model_display.glb`.
- `render_low.png` (512 square display mesh) and `render_high.png` (2048 square full
  mesh), both at the original true isometric direction `(1, -1, 1)`.
- `render_product_low.png`, `render_product_high.png`: matching resolutions with
  the screw resting on its side, socket presented toward the product camera.
- `full/` and `display/`: `isometric.svg`, `front.svg`, `back.svg`, `left.svg`,
  `right.svg`, `top.svg`, `bottom.svg`, with hidden lines removed from the solid.
- `studio.blend`, `render_scene.json`, `manifest.json`.

There are 27 hashed artifacts plus the manifest. Full detail includes a right-hand
metric helix with nominal 60-degree flanks and rounded roots. Display detail keeps
the nominal thread envelope, real head and drive cavity. STL is in millimetres;
GLB is in metres and Y-up with a PBR material. The tip/point is Z=0. Countersunk
and headless lengths include the head/point; other lengths are measured under
the head. There is no STEP/B-rep export.

Standalone mesh generation requires no Blender or repository imports:

```bat
python parts\hardware_screw_socket_cap_hex_head_black_m3_diameter_12_mm_length\three_d_model\model.py --variant both
python parts\hardware_screw_socket_cap_hex_head_black_m3_diameter_12_mm_length\three_d_model\model.py --length 20 --output custom_model
```

Use `working_three_d_model.py` for renders and SVGs. Geometry derives thread
coverage and coordinates again after a length edit, so stored derived values do
not override the new length. Parametric inputs are editable in working YAML or
the standalone JSON. Source references describe nominal dimensions, tolerances
where available, model choices and length availability.

## Materials and studio

The shared Blender studio uses AgX, three rectangular softboxes, a neutral world,
a matte seamless white floor, contact shadows, adaptive Cycles sampling and
denoising. Side pose tilt and floor height are solved from the full mesh; display
and full variants are individually grounded. Black oxide, bright zinc, stainless
and white nylon each have appropriate metallic/roughness settings. Nylon is
non-metallic. Unknown material/finish labels get a clearly identified satin steel
visual placeholder. The self-tapping reference identifies black zinc; that
identity is stored while dimensional work remains pending.

Material base colours, metalness, roughness and clearcoat are transferred to the
GLB. Procedural microtexture and the lighting rig remain in the Blender scene.
The web viewer must supply its own environment. Edit recipe `material`, `studio`
and `renders` to customize samples, pixels, camera, lights or finish. Preparation
and `--ensure-metadata` preserve existing ready recipes and custom settings;
`--update-metadata` intentionally restores sourced defaults.

## Standards and choices

Tables live in `source_file/standards`. Each carries sources and the role of those
sources. `screw_model_catalogue.py` selects a table without loading mesh libraries.
`working_three_d_model.add_definition` retains the original DIN 7991 path and
dispatches other families through that registry. Normal population embeds recipes
in source metadata and the OOMP build propagates them into generated metadata.

ISO 4762 socket caps use the published reference partial-thread thresholds and
thread lengths. Real commercial socket caps can be fully threaded; explicitly
select `thread_coverage: full` for a known fully threaded product. Low heads,
button heads and cross-head machine screws use their documented nominal/full
thread choice; this choice is identified rather than claiming a particular supplier.
Button spherical transitions, selected chamfers and manufacturer marks are also
identified as modeling choices.

Pan heads use a spherical crown with the approximate published radius over a
cylindrical skirt. The interrupted crown can finish below theoretical k after
cutting the recess. Phillips H and Pozidriv Z have independently sourced m/t and
ISO 4757 wing/taper references; Z adds diagonal identification grooves. Punch
die-flow radii and gauge penetration are simplified for visualization, so these
cavities are not certified screwdriver gauges.

Cup-point grub screws use an annular cup, a nominal 120-degree concavity, a
45-degree outer bevel and a chamfered socket end. Socket depth changes with
length. Model choices and the conflicting M2/M2.5 socket ranges in the supplier
sheet are recorded. The nominal key is used for those two sizes. Extremely short
parameters that would join the cup and socket are rejected.

The withdrawn DIN machine-screw dimensions are retained instead of silently
substituting the different ISO head profiles. Standards, supplier extensions and
catalogue length extensions do not imply manufacturer identity or material grade.

## Persistent selections and missing specifications

Edit `source_file/standards/catalogue_selections.yaml` for family defaults or
`part_filters` for a subset. These choices survive normal population. A
`three_d_model_selection` block in a source part's working YAML overrides the
family/filter defaults and is also preserved through population. For example:

```yaml
three_d_model_selection:
  standard_file: iso_4762.yaml
  thread_coverage: full
```

After changing a selection on an already ready recipe, use `--update-metadata`
with a narrow `--filter` to reselect it. This intentionally replaces geometry
defaults; `--ensure-metadata` adds missing recipes and rechecks pending entries.

The 2026-10-12 research resolves six M1.4 Phillips countersunk entries at lengths
3, 4, 5, 6, 8 and 10 mm. `jcis_type_3_countersunk.yaml` records the Japanese Screws
supplier's Type 3 profile: 0.3 mm pitch, 2.5 mm nominal head diameter, 0.7 mm head
height, 90 degree cone, recess mouth limits 1.50-1.65 mm and penetration limits
0.56-0.84 mm. The table was visually checked on PDF page 3 (printed page 5) of the
[supplier brochure](https://prokcssmedia.blob.core.windows.net/sys-master-images/h22/hd6/9138373263390/JAP%20SCREWS%20Brochure.pdf),
retained under `source_file/standards/references`. The cavity uses the published
midpoints and the existing H0 visual construction; it is not a JCIS gauge model.
This is an explicitly selected nominal supplier reference, not DIN 965 or proof
of the stocked item's manufacturer. Its production length range does not prove
each length is a stock SKU, so individual lengths retain the extension label.

On 2026-10-13, the user corrected the six M1.5 Phillips countersunk entries to
M1.6. All six lengths (3, 4, 5, 6, 8 and 10 mm) already existed at M1.6, so the
obsolete M1.5 entries were removed without duplicating the M1.6 range. These use
the sourced M1.6 DIN 965 supplier dimensions. To rebuild their models and renders,
run `action_make_countersunk_m1_6_three_d_model.bat` (forces just these six parts).

The 26 previously unresolved self-tappers are now ready as visual approximations:

- 26 miniature self-tappers: the user's references are
  [AliExpress 1005004774076999](https://www.aliexpress.com/item/1005004774076999.html)
  and [eBay 383102775525](https://www.ebay.co.uk/itm/383102775525). The latter's
  seller description identifies Phillips pan head and black zinc carbon steel,
  including M2/M2.3 sizes. It supplies no pitch, core or head dimension table.
  The inspected product text supplies no pitch, core or head dimension table.
  The inspected gallery's size diagram names dimensions but provides no numeric
  table. AliExpress could not be retrieved on 2026-10-12. Its M labels are supplier diameter labels, not evidence of ISO metric threads.
  Miniature tapping pitches must not be replaced with metric machine-screw pitch.

All 26 now use `generation_status: ready` and `dimension_status: image_based_visualization`.
Each prepared model records the supplied values and estimated features in
`parameters.json` and its README. The 3 thread-forming entries remain `excluded` by user choice.

On 2026-10-13, the user supplied [eBay 377271086738](https://www.ebay.co.uk/itm/377271086738).
Gallery image 6 gives comparative head diameter/height for 1, 1.2, 1.4, 1.7 and
2 mm screws (19 catalogue entries), and pitch for 1.4, 1.7 and 2 mm (14 entries).
The 1/1.2 mm pitches are blank and there is no 2.3 mm row. The table is transcribed
in `specification_research.yaml`, with the diagram retained in `references`.
The seller describes manual batch measurements for an A4/316 stainless product;
applicability to the catalogue black-zinc screws is not established. Core, point
and recess dimensions are not measured; the user subsequently authorized visual estimates.

The user subsequently specified **0.3 mm pitch for both 1 and 1.2 mm screws** on
2026-10-13. This is applied to all five affected recipes and retained separately
from the original supplier-table blanks.

The user also corrected all seven 2.3 mm self-tappers to **2.2 mm**, at lengths
5, 6, 8, 10, 12, 16 and 20 mm. Their selected diagram row gives 0.8 mm pitch,
3.8 mm head diameter and 1.5 mm head height. All 26 self-tappers now have selected
head dimensions and pitch; these feed the part recipes and schematic SVGs.
The user confirmed full thread to the head and authorized educated visual estimates
for the remaining features. `self_tapping_visualization.yaml` defines a 0.65d core,
60 degree sharp thread flanks with 0.02P crest land, a one-diameter tapered point,
and a Phillips recess 0.52 head diameters wide and 0.60 head heights deep. A short
0.12P blend meets the tiny head fillet without a plain neck. All lengths retain full
thread coverage. These choices are editable and do not claim manufacturing conformity.

Run `action_make_self_tapping_three_d_model.bat` to build all 26 models, isometric
and product renders, SVG views and Blender studios. Preparation and mesh tests do
not launch Blender. Existing finished assets are reused; add `--force` to rebuild.

### Wood screws: modern chipboard/plywood style (2026-10-13)

All 30 wood recipes use `wood_similar_product.yaml`, with
`dimension_status: similar_product_visualization`. The user requested the modern
style used for plywood, with a bare section below every head. The geometry uses
a slender shank, 40-degree thread flanks and a countersunk Pozidriv head. It is a
sourced comparable-product model, not an exact Screw-Tite reconstruction.
Recipes, READMEs, manifests and SVG metadata identify this status. Catalogue
identities now use Screwfix's verified individual-size packs: `manufacturer` and
`taxonomy_14` are `screwtite`; `part_number` and `taxonomy_15` contain the Screwfix
code (for example `127FY` for 4 x 50 mm). The source mapping lives in
`working_oomp_populate_wood.py`, called by `working_oomp_populate.py`.
The finish is `net_coat_yellow_plated` (Screwfix: Net-Coat Yellow-Plated), with a
warm yellow-gold metallic material shared by Blender and GLB exports. Unlisted
sizes and mixed trade packs are excluded. The 61 previous bright-zinc entries
and their cached assets were moved out of the active catalogue into
`metadata_recovery_backups/wood_screwtite_migration_2026_10_13` after recursive
deletion was blocked by automatic approval review.

| Diameter, mm | Pitch, mm | Core, mm | Plain shank, mm | Head diameter, mm |
|---|---:|---:|---:|---:|
| 2* | 0.90 | 1.20 | 1.44 | 3.90 |
| 2.5 | 1.10 | 1.50 | 1.80 | 4.875 |
| 3 | 1.35 | 1.90 | 2.15 | 5.80 |
| 3.5 | 1.60 | 2.10 | 2.45 | 6.80 |
| 4 | 1.80 | 2.375 | 2.72 | 7.75 |
| 4.5 | 2.00 | 2.575 | 3.15 | 8.75 |
| 5 | 2.20 | 2.85 | 3.40 | 9.75 |
| 6 | 2.60 | 3.55 | 4.20 | 11.80 |

[HSB ETA-24/0222, Annex A page 11](https://hsb-schrauben.de/wp-content/uploads/media/ETA240222-HSB-Chipboard-Screw-and-HSB-Wood-Construction-Screw.pdf)
supplies the modern 3-6 mm head/core limits, slender shank minima, head-to-thread
clearances, pitches and 40 +/-3 degree flanks. The archived PDF was visually
checked: web text extraction mixes dimensions from adjacent drawings.
[Hebei Motu's catalogue, PDF page 6](https://pub-mediabox-storage.rxweb-prd.com/exhibitor/document/exh-350e0970-c3e5-4252-b9da-5ebd0ff435aa/010dea8b-a20f-4303-98fa-753c89aa4363.pdf)
supplies the 2.5 mm profile and Pozidriv mouth/depth dimensions for 2.5-6 mm.
The selected values are nominal values or midpoints, with the exceptions stated
in the YAML source table. Shank at 2.5 mm uses Motu's wire diameter.

*The retained 2 mm reference profile is an explicitly scaled modern extension from the 2.5 mm
profile; their 0.9 mm pitch comes from the
[Killich small wood-thread table](https://www.i-fasteners.com/thread-of-the-woodscrew),
and their Z1 recess remains the separately sourced DIN 965 similar-head proxy.
The 2 and 2.5 mm profiles are no longer emitted by the catalogue.

Every default recipe retains a plain shank beneath the head, including short
catalogue extensions. The selected thread target is 0.6L, capped at 72 mm, with a
one-pitch runout. A plain section of at least min(0.5d, 25% of available shaft) is
reserved, reducing thread length on tiny screws. The actual supplier products
have different coverage options; this is the user's selected visual convention.
All coordinates recompute after portable model length edits.

Core and crests taper together to a point. Point length is a selected 1.25d,
limited to 60% of the threaded envelope, with a 0.0001 mm radius end face to
avoid degenerate vertices. The head uses a selected 90-degree cone, 0.10d rim
and small fillet. The 0.02P crest land, runout and simplified ISO 4757 cavity are
modelling choices. Brand-specific cutting flutes, ribs, Tri-Lock and twin-start
transitions are not claimed. No metric machine-thread core is substituted.

The earlier 61-part geometry validation checked all 61
watertight display solids and plain shanks, plus full-detail solids at all seven
diameters, actual core/crest sections, point geometry, recessed drives and length
edits. Test exports cover 2 x 4, 4 x 16 and 4 x 50 mm, including STL/GLB, seven
SVG views per variant and both studio poses. The remaining family render run is
not started. Final verification: 163 tests passed; all 84 artifacts across the
three sample sets passed hash/format checks, rendered previews and SVG views were
visually inspected, and the wood batch passed its `--check` run.

After the Screwfix identity migration, all 30 replacement recipes, diagrams,
drawer labels and portable model inputs were regenerated. Active product render
caches are empty as requested. A separate 4.5 x 50 mm preview under
`temporary/screwtite_finish_preview` checks the new material in both studio poses.
The 4.5 mm geometry uses the visually checked HSB and Motu rows, not interpolation.

Run the prepared family batch when ready:

```bat
action_make_wood_three_d_model.bat
```

It processes only the 61 wood entries and uses one worker by default. Completed
sample renders are retained. Use `--jobs 2` for two workers or `--force` to replace
existing renders deliberately. `action_make_three_d_model.bat` processes the
whole catalogue, including all 61 wood screws; the separate wood batch is optional.
The 26 miniature self-tapping entries are ready using user-authorized visual estimates.

### Screw-Tite reference reconciliation (2026-10-12)

`specification_research.yaml` stores partial evidence separately from CAD inputs.
Ready wood recipes retain it under `preferred_product_comparison`; its missing
measurements concern exact brand matching and do not block the authorized proxy.
`references/screw_tite_product_table.json` preserves the 46 manufacturer rows read
from the [Tite-Fix technical table](https://www.tite-fix.co.uk/product/screw-tite-multipurpose-screw/).
Of the current 61 catalogue entries, 21 diameter/length combinations are listed,
26 have an unlisted length, and 14 have an unlisted diameter (2 and 2.5 mm).
Unlisted means absent from this reference, not proof that no supplier makes it.

| Diameter, mm | Current catalogue lengths listed by Tite-Fix, mm | Published head diameter, mm | Drive |
|---|---|---|---|
| 2 / 2.5 | None | Not supplied | Not supplied |
| 3 | 12, 16, 20, 25 | 5.7-6.0 | PZ1 |
| 3.5 | 16 | 6.6-7.0 | PZ2 |
| 4 | 16, 20, 25, 30, 40, 50, 60 | 7.6-8.0 | PZ2 |
| 5 | 30, 40, 50, 60, 70, 80, 100 | 9.5-10.0 | PZ2 |
| 6 | 100, 120 | 11.5-12.0 | PZ3 |

The preferred Screw-Tite reference's published yellow CR3/Net-Coat finish conflicts with every current wood entry's
`bright_zinc_plated` label. That conflict is recorded without renaming parts.
[Screwfix 127FY](https://www.screwfix.com/p/screw-tite-2-pz-double-countersunk-thread-cutting-screws-4mm-x-50mm-200-pack/127fy)
confirms the Screw-Tite 2 ribbed double-countersunk head, yellow finish and
single/twin thread. The manufacturer page is labelled Screw-Tite, so revision
equivalence still needs confirmation. For example, its 4 x 50 row gives
28.5-31.5 mm thread length. Accu's separate zinc-plated TFSTZ4050 page corroborates
the head diameter and minimum thread length, but is not silently merged into the
Screw-Tite 2 definition. The manufacturer table repeats TFST04530 for 5 x 40;
the duplicate SKU is explicitly flagged. Published unusual thread-length rows
are retained rather than corrected by guesswork.

For the miniature self-tappers, the Screw Express plastic-screw table and Japanese
Screws P/B/S profiles provide research leads, but do not identify the pointed
sheet-metal screws in the user's listing. Their pitches must not be copied into
the current parts without a product match. The selected pitches instead use the
user-supplied diagram and explicit 0.3 mm overrides. The ready model recipes and
READMEs distinguish these dimensions from the authorized visual estimates.

## Add compatible models in another repository

Read the files in the reference repository above, especially
`working_three_d_model.py`, `screw_model_geometry.py`, `screw_model_views.py`,
`screw_model_render.py`, `screw_model_blender.py`, `screw_model_catalogue.py` and
the standards tables. Copy the common presentation/export workflow and adapt the
family definition and geometry to the new part. Preserve output filenames,
variants, mm/metre conventions, camera directions, render sizes, SVG view names,
recipe schema and artifact-hash validation. Do not substitute a new render style.

Research primary standard documents and supplier drawings. Record exact source
URLs and which dimensions they supply. Distinguish standard sizes, supplier
extensions and unavailable product dimensions. Include a per-part recipe under
`three_d_model_details` in population before generating anything. Use a dedicated
geometry builder for non-metric threads or non-screw parts: the current metric
helix must not be reused for wood/tapping profiles solely because a new table has
a diameter and pitch. A new standard table alone does not add an unsupported
thread form or point geometry. The wood family now has its own radial profile
and tapered point in the shared builder, separate from the metric profile.

Add meaningful checks for actual bounding dimensions, length conventions,
recesses/holes, single-solid watertightness, GLB scale/orientation and both studio
poses. Export portable model.py/parameters.json/requirements.txt into each part's
three_d_model folder. Prepare all inputs without launching bulk renders; leave
full builds to the matching batch file. For this repository run:

```bat
python -m pytest tests webserver/tests -q
action_check_three_d_model.bat
```

The tests include small temporary Blender smoke renders, rather than a catalogue
render run. The initial implementation also verified display solids for all 768
ready catalogue entries; full-detail representative checks cover sizes and heads.
