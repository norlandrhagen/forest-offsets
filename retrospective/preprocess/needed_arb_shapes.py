from glob import glob
import json


# https://gis.arb.ca.gov/fedarcgis/rest/services/ARBOC_issuance_map/MapServer/0/query
# Log into ARB GIS portal,
# in text, search `%_%` and make sure to tick 'return id only'
# paste the output here :)
ALL_IDS = [
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
    31,
    32,
    33,
    34,
    35,
    36,
    37,
    38,
    39,
    40,
    41,
    42,
    43,
    44,
    45,
    46,
    47,
    48,
    49,
    50,
    51,
    52,
    53,
    54,
    55,
    56,
    57,
    58,
    59,
    60,
    61,
    62,
    63,
    64,
    65,
    66,
    67,
    68,
    69,
    70,
    71,
    72,
    73,
    74,
    75,
    76,
    77,
    78,
    79,
    80,
    81,
    82,
    83,
    84,
    85,
    86,
    87,
    88,
    89,
    90,
    91,
    92,
    93,
    94,
    95,
    96,
    97,
    99,
    100,
    101,
    102,
    103,
    104,
    110,
    123,
    124,
    129,
    130,
    132,
    133,
    134,
    135,
    136,
    138,
    139,
    140,
    143,
    145,
    146,
    147,
    148,
    149,
    150,
    151,
    153,
    169,
    170,
    171,
    172,
    173,
    174,
    175,
    176,
]


def main():
    fnames = glob('/Users/darryl/forest-retro/shapes/*json')
    object_ids = []
    for fname in fnames:
        try:
            d = json.load(open(fname))

            object_ids.append(d['features'][0]['properties']['OBJECTID'])
        except KeyError:
            print(fname)
    still_need = [x for x in ALL_IDS if x not in object_ids]
    print(still_need)


if __name__ == '__main__':
    main()
