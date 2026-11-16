include <C:/gh/oomlout_oobb_version_5/git/BOSL2/std.scad>
include <C:/gh/oomlout_oobb_version_5/git/BOSL2/screws.scad>

module github_belfryscad_bosl2_screw_raw(
    spec="M3,12",
    head="socket",
    drive="none",
    length=12,
    thread="coarse",
    drive_size=undef,
    thread_len=undef,
    undersize=undef,
    shaft_undersize=undef,
    head_undersize=undef,
    tolerance=undef,
    blunt_start=true,
    details=false,
    atype="screw",
    anchor="center"
) {
    let(
        $tags_shown="ALL",
        $tags_hidden=[],
        $tag="",
        $tags=""
    )
    screw(
        spec=spec,
        head=head,
        drive=drive,
        thread=thread,
        drive_size=drive_size,
        length=length,
        thread_len=thread_len,
        undersize=undersize,
        shaft_undersize=shaft_undersize,
        head_undersize=head_undersize,
        tolerance=tolerance,
        blunt_start=blunt_start,
        details=details,
        atype=atype,
        anchor=anchor
    );
}
