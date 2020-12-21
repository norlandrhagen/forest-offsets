import json
from collections import defaultdict
from itertools import permutations

from utils import load_supersection_shapes


def generate_border_dict():

    supersections = load_supersection_shapes()

    store = defaultdict(list)
    for pair in permutations(supersections.itertuples(), 2):
        if pair[0].geometry.intersects(pair[1].geometry):
            store[pair[0].Index].append(pair[1].Index)
    return store


if __name__ == '__main__':
    d = generate_border_dict()
    with open('../data/border_dict.json', 'w') as f:
        json.dump(d, f)