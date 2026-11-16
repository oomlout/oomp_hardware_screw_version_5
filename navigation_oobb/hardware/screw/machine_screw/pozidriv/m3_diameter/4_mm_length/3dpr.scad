$fn = 50;

use <../scad_reference/github_belfryscad_bosl2_screw_raw.scad>;

difference() {
	union() {
		color(alpha = 1.0, c = "silver") {
			github_belfryscad_bosl2_screw_raw(anchor = "center", atype = "screw", blunt_start = true, details = false, drive = "pozidriv", head = "machine screw", length = 4.0, spec = "M3,4", thread = "coarse");
		}
	}
	union();
}
