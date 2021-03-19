from pm4py.algo.discovery.evolutionary_tree.evolutions.initial_generation import Variants as init_variants
from pm4py.algo.discovery.evolutionary_tree.parameters import Parameters

default_discovery = {
    Parameters.ACTIVITY_KEY: 'concept:name',
    Parameters.INIT_GENERATION_VARIANT: init_variants.RANDOM,
    Parameters.MAX_EVOLUTIONS: 100,
    Parameters.N_EVOLUTION_NO_CHANGE: 3,
    Parameters.TARGET_QUALITY: 1,
    Parameters.POPULATION_SIZE: 20,
    Parameters.ELITE_SIZE: 5
}