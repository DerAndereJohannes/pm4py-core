from enum import Enum
from pm4py.algo.discovery.evolutionary_tree.parameters import TreeKeys


def simplicity_size(log, tree):
    # use activity count to lower punishment for logs with many activities
    act_count = len(tree[TreeKeys.LOG_ACTIVITIES.value])
    return (act_count + 1) / (act_count + count_nodes(tree[TreeKeys.TREE.value]))


def count_nodes(tree):
    count = 1
    for child in tree.children:
        count += count_nodes(child)
    return count


def simplicity_occurence(log, tree):
    activity_list = tree[TreeKeys.LOG_ACTIVITIES.value]
    process_tree = tree[TreeKeys.TREE.value]

    # if only one node
    if process_tree.label:
        missing_activities = len(activity_list) - 1
        event_classes = len(activity_list)
        return 1 - ((missing_activities) / (1 + event_classes))

    counter = dict()
    counter["occurences"] = {act: 0 for act in activity_list}
    counter["tree_activities"] = set()
    counter["node_count"] = 1

    count_occurences(process_tree, counter)

    duplicate_activities = sum(counter["occurences"].values())
    missing_activities = len(activity_list) - len(counter["tree_activities"])
    event_classes = len(activity_list)

    return 1 - ((duplicate_activities + missing_activities)/(counter["node_count"] + event_classes))


def count_occurences(tree, to_count):
    for child in tree.children:
        if child.label is not None:
            if child.label in to_count["tree_activities"]:
                to_count["occurences"][child.label] += 1
            to_count["tree_activities"].add(child.label)
        to_count["node_count"] += 1

        count_occurences(child, to_count)


def simplicity_useless_nodes(log, tree):
    pass


class Variants(Enum):
    SIMPLICITY_SIZE = {"name": "simplicity_size", "function": simplicity_size}
    SIMPLICITY_OCCURENCE = {"name": "simplicity_occurence", "function": simplicity_occurence}
    SIMPLICITY_USELESS_NODES = {"name": "simplicity_useless", "function": simplicity_useless_nodes}