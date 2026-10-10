$fn = 50;

use <../scad_reference/github_belfryscad_bosl2_screw_raw.scad>;

difference() {
	union() {
		color(alpha = 1.0, c = "#444444") {
			github_belfryscad_bosl2_screw_raw(anchor = "center", atype = "screw", blunt_start = true, details = false, drive = "philips", head = "self tapping", length = 16.0, spec = "M1.7,16", thread = "coarse");
		}
	}
	union();
}
