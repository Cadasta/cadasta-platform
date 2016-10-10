from shapely.geometry import LineString, Point, Polygon
from shapely.wkt import dumps


def odk_geom_to_wkt(coords):
    """Convert geometries in ODK format to WKT."""
    if coords == '':
        return ''
    coords = coords.replace('\n', '')
    coords = coords.split(';')
    coords = [c.strip() for c in coords]
    if (coords[-1] == ''):
        coords.pop()

    if len(coords) > 1:
        # check for a geoshape taking into account
        # the bug in odk where the second coordinate in a geoshape
        # is the same as the last (first and last should be equal)
        if len(coords) > 3:
            if coords[1] == coords[-1]:  # geom is closed
                coords.pop()
                coords.append(coords[0])
        points = []
        for coord in coords:
            coord = coord.split(' ')
            coord = [x for x in coord if x]
            latlng = [float(coord[1]),
                      float(coord[0])]
            points.append(tuple(latlng))
        if (coords[0] != coords[-1] or len(coords) == 2):
            return dumps(LineString(points))
        else:
            return dumps(Polygon(points))
    else:
        latlng = coords[0].split(' ')
        latlng = [x for x in latlng if x]
        return dumps(Point(float(latlng[1]), float(latlng[0])))
