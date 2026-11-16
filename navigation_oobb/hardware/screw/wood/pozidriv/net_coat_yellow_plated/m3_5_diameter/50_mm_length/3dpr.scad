$fn = 50;

use <../scad_reference/github_belfryscad_bosl2_screw_raw.scad>;

difference() {
	union() {
		color(alpha = 1.0, c = "net_coat_yellow_plated") {
			github_belfryscad_bosl2_screw_raw(anchor = "center", atype = "screw", blunt_start = true, details = false, drive = "pozidriv", head = "wood", length = 50.0, spec = "M3.5,50", thread = "coarse");
		}
	}
	union();
}
