from pm4py.algo.discovery.evolutionary_tree.parameters import default_discovery


def apply(log, parameters=None):

    # set default parameters if empty
    if parameters is None or parameters == {}:
        parameters = default_discovery

    return 0  # process tree
