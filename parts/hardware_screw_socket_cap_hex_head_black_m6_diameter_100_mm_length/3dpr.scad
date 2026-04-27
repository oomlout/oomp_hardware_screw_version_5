$fn = 50;

use <github_belfryscad_bosl2_screw_raw.scad>;

difference() {
	union() {
		color(alpha = 1.0, c = "#444444") {
			github_belfryscad_bosl2_screw_raw(anchor = "center", atype = "screw", blunt_start = true, details = false, drive = "hex", head = "socket", length = 100.0, spec = "M6,100", thread = "coarse");
		}
	}
	union();
}
