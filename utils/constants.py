# -*- coding: utf-8 -*-
"""Module containing the constants."""

# Constants for file types
FILE_TYPE_JSON = "json"

# shapefile names
SHP_NAME_MANHOLES = "manholes"
SHP_NAME_PIPES = "pipes"
SHP_NAME_MEASURING_POINTS = "measuring_points"
SHAPEFILE_LIST = [SHP_NAME_MANHOLES, SHP_NAME_PIPES, SHP_NAME_MEASURING_POINTS]

# json name and property
JSON_NAME = "review.json"
JSON_KEY_PROJ = "project"
JSON_KEY_NAME = "name"
JSON_KEY_URL = "url"
JSON_KEY_SLUG = "slug"

# Herstelmaatregeln
HERSTELMAATREGELEN = [
    "",
    "Aanbrengen deel relining",
    "Aanbrengen relining",
    "Gedeeltelijk herleggen",
    "Geheel herleggen",
    "Naderonderzoek",
    "Obstakel weg frezen",
    "Reinigingsfrequentie opvoeren",
    "Reparatie in ander herstel voorstel",
    "T-stuk/bocht en standpijp vervangen",
    "T-stuk/bocht vervangen",
    "T-stuk in hoofdriool vervangen (inclusief standpijp en T-stuk/bocht)",
    "Vaker inspecteren",
    "Van binnenuit reinigen",
    "Anders",
    "Geen actie",
]