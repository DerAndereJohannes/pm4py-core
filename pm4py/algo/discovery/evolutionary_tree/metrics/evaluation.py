from pm4py.algo.discovery.evolutionary_tree.parameters import Parameters, TreeKeys


def evaluate_tree_list(log, tree_list, parameters):
    # if no weight value in metric, set to 1
    for metric in parameters[Parameters.EVALUATION_METRICS.value]:
        if not isinstance(metric, tuple) or \
           (isinstance(metric, tuple) and len(metric) == 1):
            metric = (metric, 1)

    for tree in tree_list:
        evaluate_tree(log, tree, parameters)
        calculate_quality(tree, parameters)


def evaluate_tree(log, tree, parameters):
    # for each evaluation dictionary in the parameters
    for metric in parameters[Parameters.EVALUATION_METRICS.value]:
        metric_dict = metric[0].value
        tree[metric_dict["name"]] = max(0, metric_dict["function"](log, tree))


def calculate_quality(tree, parameters):
    quality = 0
    weight_sum = sum([metric[1] for metric in parameters[Parameters.EVALUATION_METRICS.value]])

    for metric in parameters[Parameters.EVALUATION_METRICS.value]:
        metric_dict = metric[0].value
        quality += (metric[1] / weight_sum) * tree[metric_dict["name"]]

    tree[TreeKeys.QUALITY.value] = quality
