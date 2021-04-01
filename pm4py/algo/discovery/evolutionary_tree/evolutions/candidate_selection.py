from enum import Enum
from copy import deepcopy
from random import choices, random
from statistics import mean, stdev
from pm4py.algo.discovery.evolutionary_tree.parameters import Parameters, TreeKeys


def quality_proportional(population, parameters):
    selection_quantity = parameters[Parameters.POPULATION_SIZE.value] - parameters[Parameters.ELITE_SIZE.value]
    pt_selection = []
    # for each free spot
    for _ in range(selection_quantity):
        # select candidates with probability proportional to the quality metric
        pt_selection.append(choices(population, [p[TreeKeys.QUALITY.value] for p in population])[0])
        # remove the winning tree from the still undecided
        # population.remove(pt_selection[-1])

    return pt_selection


def sigma_scaled_sus(population, parameters):
    selection_quantity = parameters[Parameters.POPULATION_SIZE.value] - parameters[Parameters.ELITE_SIZE.value]
    # apply sigma scaling to all of the quality values
    pop_quality = [pt[TreeKeys.QUALITY.value] for pt in population]
    pop_mean = mean(pop_quality)
    pop_stdev = stdev(pop_quality)
    sigma_scaled = [max(1+((p - pop_mean)/(2*pop_stdev)), 0) for p in pop_quality]

    # apply stochastic universal selection
    pointer_gap = 1 / selection_quantity
    pointer_start = random() * pointer_gap
    pop_sum = sigma_scaled[0]/sum(sigma_scaled)
    pop_id = 0
    pt_selection = []

    for pointer_id in range(selection_quantity):
        curr_loc = pointer_start + (pointer_id * pointer_gap)
        while curr_loc > pop_sum:
            pop_id += 1
            pop_sum += sigma_scaled[pop_id]/sum(sigma_scaled)
        pt_selection.append(population[pop_id])

    return pt_selection


class Variants(Enum):
    QUALITY_PROPORTIONAL = quality_proportional
    SIGMA_SCALED_SUS = sigma_scaled_sus


DEFAULT_VARIANT = Variants.QUALITY_PROPORTIONAL


def select_candidates(population, parameters, variant=DEFAULT_VARIANT):
    # sort the population from most fit to least fit
    population = sorted(population, key=lambda x: x[TreeKeys.QUALITY.value], reverse=True)
    # copy the top ELITE_SIZE number of process trees into the elite list based on quality value
    elite = [deepcopy(pt) for pt in population[:parameters[Parameters.ELITE_SIZE.value]]]

    pt_selection = variant(population, parameters)

    return elite, pt_selection
