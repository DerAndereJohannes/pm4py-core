from enum import Enum
from pm4py.algo.discovery.evolutionary_tree import variants
from pm4py.util import exec_utils


class Variants(Enum):
    DISCOVERY = variants.discovery


DISCOVERY = Variants.DISCOVERY
DEFAULT_VARIANT = DISCOVERY
VERSIONS = {Variants.DISCOVERY}


def apply(log, parameters=None, variant=DEFAULT_VARIANT):

    if parameters is None:
        parameters = {}

    return exec_utils.get_variant(variant).apply(log, parameters)
