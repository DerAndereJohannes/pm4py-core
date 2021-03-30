from enum import Enum
from copy import deepcopy
from random import choices
from pm4py.algo.discovery.evolutionary_tree.parameters import Parameters, TreeKeys


def quality_proportional(population, parameters):
    selection_quantity = parameters[Parameters.POPULATION_SIZE.value] - parameters[Parameters.ELITE_SIZE.value]
    pt_selection = []
    # for each free spot
    for _ in range(selection_quantity):
        # select candidates with probability proportional to the quality metric
        pt_selection.append(choices(population, [p[TreeKeys.QUALITY.value] for p in population])[0])
        # remove the winning tree from the still undecided
        population.remove(pt_selection[-1])

    return pt_selection


class Variants(Enum):
    QUALITY_PROPORTIONAL = quality_proportional


DEFAULT_VARIANT = Variants.QUALITY_PROPORTIONAL


def select_candidates(population, parameters, variant=DEFAULT_VARIANT):
    # copy the top ELITE_SIZE number of process trees into the elite list based on quality value
    elite = [deepcopy(pt) for pt in sorted(population, key=lambda x: x[TreeKeys.QUALITY.value], reverse=True)[:parameters[Parameters.ELITE_SIZE.value]]]

    pt_selection = variant(population, parameters)

    return elite, pt_selection
