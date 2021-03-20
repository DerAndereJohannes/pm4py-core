from pm4py.algo.discovery.evolutionary_tree.evolutions.initial_generation import Variants as init_variants
from pm4py.algo.discovery.evolutionary_tree.parameters import Parameters
import pm4py.algo.discovery.evolutionary_tree.metrics.fitness as fitness

default_discovery = {
    Parameters.ACTIVITY_KEY.value: 'concept:name',
    Parameters.INIT_GENERATION_VARIANT.value: init_variants.RANDOM,
    Parameters.MAX_EVOLUTIONS.value: 100,
    Parameters.N_EVOLUTION_NO_CHANGE.value: 3,
    Parameters.TARGET_QUALITY.value: 1,
    Parameters.POPULATION_SIZE.value: 20,
    Parameters.ELITE_SIZE.value: 5,
    Parameters.EVALUATION_METRICS.value: [(fitness.Variants.TREE_ALIGNMENTS, 1)]
}