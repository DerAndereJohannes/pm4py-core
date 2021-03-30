from pm4py.algo.discovery.evolutionary_tree.parameters import Parameters, TreeKeys
from pm4py.algo.discovery.evolutionary_tree.defaults import default_discovery
from pm4py.algo.discovery.evolutionary_tree.evolutions.initial_generation import generate_initial_population
from pm4py.algo.discovery.evolutionary_tree.metrics.evaluation import evaluate_tree_list


def apply(log, parameters=None):

    # set default parameters if empty
    if parameters is None or parameters == {}:
        parameters = default_discovery

    return algorithm(log, parameters)


def algorithm(log, parameters):
    # Generate Population and list that keeps list of max qulity of generations
    generation_quality = [None]*parameters[Parameters.MAX_EVOLUTIONS]
    population_candidates = generate_initial_population(log, parameters, parameters[Parameters.INIT_GENERATION_VARIANT.value])
    evaluate_tree_list(log, population_candidates, parameters)

    # Keep mutating for MAX_EVOLUTIONS iterations
    for gen in range(parameters[Parameters.MAX_EVOLUTIONS]):
        # Store maximum quality of previous generation
        generation_quality[gen] = max(c[TreeKeys.QUALITY] for c in population_candidates)

        # Terminate if passed quality threshold is surpassed or difference
        # between generation too low
        if generation_quality[gen] >= parameters[Parameters.TARGET_QUALITY] \
           or (gen and generation_quality[gen] - generation_quality[gen - 1]
                < parameters[Parameters.N_EVOLUTION_NO_CHANGE]):
            break

        # Get elite population and select candidate population
        elite, population_candidates = select_candidates(population_candidates)

        # Mutate / crossover selected population
        mutate_candidates(population_candidates)

        # Evaluate new mutations
        evaluate_tree_list(log, population_candidates, parameters)

        # Bring elite back to population candidates
        population_candidates = population_candidates + elite

    # fetch tree with the best quality measurement
    best_tree = max(population_candidates, key=lambda c: c[TreeKeys.QUALITY])

    return best_tree[TreeKeys.TREE], best_tree


def select_candidates(population):
    return 0


def mutate_candidates(population):
    return 0
