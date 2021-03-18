from pm4py.util import constants
from enum import Enum


class Parameters(Enum):
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    START_TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_START_TIMESTAMP_KEY
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    CASE_ID_KEY = constants.PARAMETER_CONSTANT_CASEID_KEY
    MAX_EVOLUTIONS = "max_evolutions"
    N_EVOLUTION_NO_CHANGE = "stable_evolutions"
    TARGET_QUALITY = "target_quality"
    POPULATION_SIZE = "population_size"
    ELITE_SIZE = "elite_size"


default_discovery = {
    Parameters.MAX_EVOLUTIONS: 100,
    Parameters.N_EVOLUTION_NO_CHANGE: 3,
    Parameters.TARGET_QUALITY: 1,
    Parameters.POPULATION_SIZE: 20,
    Parameters.ELITE_SIZE: 5
}
