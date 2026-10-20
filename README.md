# OrbitSim
Simple stylised orbit sim for my physics presentation

## Artemis-style free-return setup

The configured ship trajectory is a representative, planar Artemis-II-style free return, not a reconstruction of the flown mission ephemeris. The Moon starts at its existing orbital radius and speed, with its orbital phase rotated to align the flyby. The ship starts 200 km above Earth's mean radius with an Earth-centered translunar injection state.

The ship integrates Earth's gravity plus the Moon's differential gravity in the Earth-centered frame. Its trajectory ends at the 120 km Earth-entry interface. This restricted Earth-Moon model omits solar and other perturbations, so the path and timing are illustrative rather than mission-accurate.
