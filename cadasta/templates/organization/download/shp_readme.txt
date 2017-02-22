{% load i18n %}

{% blocktrans %}
You have downloaded all data from project "{{ project_name }}" in shapefile format.

Besides this README, the ZIP archive contains the shape files and CSV files containing the project data.

Shape files can only store geometries of a single type: either point, line, polygon or multigeometry variants of these.
Because of this, you will find a shape file for each type of geometry in project "{{ project_name }}".
We currently support point, linestring, polygon, multipoint, multilinestring and multipolygon geometries.
All shape files are provided with their corresponding *.shx, *.prj and *.dbf files.

The attribute table of each shapefile contains only the location ID.

The attributes for locations, parties and relationships are provided in CSV files called locations.csv, parties.csv and relationships.csv.
We use CSV instead of dBase files to avoid certain restrictions of the dBase format that would cause some data to be truncated.
{% endblocktrans %}
