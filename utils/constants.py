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


RIBX_CODE_DESCRIPTION_MAPPING = {
    'BAA': 'Deformatie',
    'BAB': 'Scheur',
    'BAC': 'Breuk/instorting',
    'BAD': 'Defecte bakstenen of defect metselwerk ',
    'BAE': 'Ontbrekende metselspecie',
    'BAF': 'Oppervlakteschade',
    'BAG': 'Instekende inlaat',
    'BAH': 'Defecte aansluiting',
    'BAI': 'Indringend afdichtingsmateriaal ',
    'BAJ': 'Verplaatste verbinding ',
    'BAK': 'Lining',
    'BAL': 'Defecte reparatie',
    'BAM': 'Lasfouten',
    'BAN': 'Poreuze buis',
    'BAO': 'Grond zichtbaar door defect',
    'BAP': 'Holle ruimte zichtbaar door defect',
    'BBA': 'Wortels',
    'BBB': 'Aangehechte afzettingen',
    'BBC': 'Bezonken afzettingen',
    'BBD': 'Binnendringen van grond ',
    'BBE': 'Andere obstakels ',
    'BBF': 'Infiltratie ',
    'BBG': 'Exfiltratie',
    'BBH': 'Ongedierte ',
    'BCA': 'Aansluiting ',
    'BCB': 'Plaatselijke reparatie ',
    'BCC': 'Geprefabriceerd bochtstuk ',
    'BCD': 'Beginknooppunt ',
    'BCE': 'Eindknooppunt ',
    'BDA': 'Algemene foto ',
    'BDB': 'Algemene opmerking ',
    'BDC': 'Inspectie beeindigd voor het eindknooppunt ',
    'BDD': 'Waterpeil',
    'BDE': 'Instroom vanuit binnenkomende buis',
    'BDF': 'Atmosfeer in leiding ',
    'BDG': 'Verlies van beeld ',
    'DAA': 'Deformatie',
    'DAB': 'Scheur',
    'DAC': 'Breuk/instorting',
    'DAD': 'Defecte bakstenen of defect metselwerk ',
    'DAE': 'Ontbrekende metselspecie',
    'DAF': 'Oppervlakteschade',
    'DAG': 'Instekende inlaat',
    'DAH': 'Defecte aansluiting',
    'DAI': 'Indringend afdichtingsmateriaal ',
    'DAJ': 'Verplaatste verbinding ',
    'DAK': 'Lining waarnemingen',
    'DAL': 'Defecte reparatie',
    'DAM': 'Lasfouten',
    'DAN': 'Poreuze wand ',
    'DAO': 'Grond zichtbaar door defect',
    'DAP': 'Holle ruimte zichtbaar door defect',
    'DAQ': 'Defect klimijzer of ladder',
    'DAR': 'Defect deksel of putrand',
    'DBA': 'Wortels',
    'DBB': 'Aangehechte afzettingen',
    'DBC': 'Bezonken afzettingen',
    'DBD': 'Binnendringen van grond ',
    'DBE': 'Andere obstakels ',
    'DBF': 'Infiltratie ',
    'DBG': 'Exfiltratie',
    'DBH': 'Ongedierte ',
    'DCA': 'Soort aansluiting',
    'DCB': 'Plaatselijke reparatie ',
    'DCG': 'Aansluitende leiding',
    'DCH': 'Banket',
    'DCI': 'Stoomprofiel',
    'DCJ': 'Veiligheidskettingen/ stangen',
    'DCK': 'Controlerende voorziening vloeistofstroom',
    'DCL': 'Andere afvalwaterleiding door put',
    'DCM': 'Zandvang onder deksel',
    'DCN': 'Slibvanger in stroomprofiel ',
    'DCO': 'Dwarsdoorsnede',
    'DDA': 'Algemene foto ',
    'DDB': 'Algemene opmerking ',
    'DDC': 'Inspectie beëindigd voor dat deze gereed is.',
    'DDD': 'Waterpeil',
    'DDE': 'Instroom vanuit binnenkomende buis',
    'DDF': 'Atmosfeer in put',
    'DDG': 'Verlies van beeld '
}
