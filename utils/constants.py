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

ZB_A_FIELDS = ['AAA', 'AAB', 'AAC', 'AAD', 'AAE', 'AAF', 'AAG', 'AAH',
               'AAI', 'AAJ', 'AAK', 'AAL', 'AAM', 'AAN', 'AAO', 'AAP',
               'AAQ', 'AAT', 'AAU', 'AAV', 'ABA', 'ABB', 'ABC', 'ABE',
               'ABF', 'ABG', 'ABH', 'ABI', 'ABJ', 'ABK', 'ABL', 'ABM',
               'ABN', 'ABO', 'ABP', 'ABQ', 'ABR', 'ABS', 'ABT', 'ACA',
               'ACB', 'ACC', 'ACD', 'ACE', 'ACF', 'ACG', 'ACH', 'ACI',
               'ACJ', 'ACK', 'ACL', 'ACM', 'ACN', 'ADA', 'ADB', 'ADC',
               'ADE', 'AXA', 'AXB', 'AXC', 'AXD', 'AXE', 'AXF', 'AXG',
               'AXH', 'AXY', 'ZC']
ZB_C_FIELDS = ['CAA', 'CAB', 'CAJ', 'CAL', 'CAM', 'CAN', 'CAO', 'CAP',
               'CAQ', 'CAR', 'CAS', 'CBA', 'CBB', 'CBC', 'CBD', 'CBE',
               'CBF', 'CBG', 'CBH', 'CBI', 'CBJ', 'CBK', 'CBL', 'CBM',
               'CBN', 'CBO', 'CBP', 'CBR', 'CBS', 'CBT', 'CCA', 'CCB',
               'CCC', 'CCD', 'CCG', 'CCK', 'CCL', 'CCM', 'CCN', 'CCO',
               'CCP', 'CCQ', 'CCR', 'CCS', 'CCT', 'CDA', 'CDB', 'CDC',
               'CDD', 'CDE', 'CXA', 'CXB', 'CXC', 'CXD', 'CXE']
