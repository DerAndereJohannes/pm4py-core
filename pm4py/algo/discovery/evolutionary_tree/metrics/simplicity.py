from copy import deepcopy
from enum import Enum
from pm4py.algo.discovery.evolutionary_tree.parameters import TreeKeys
from pm4py.objects.process_tree.util import is_tau_leaf, is_leaf
from pm4py.objects.process_tree.process_tree import Operator


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
    process_tree = tree[TreeKeys.TREE.value]

    if process_tree.label:
        return 1.0

    useless_tree = deepcopy(process_tree)
    counter = dict()
    counter["activity_list"] = tree[TreeKeys.LOG_ACTIVITIES.value] + [None]
    counter["useless"] = 0
    counter["node_count"] = 1

    count_useless(useless_tree, counter)
    print(counter["useless"], counter["node_count"])

    return 1 - (counter["useless"] / counter["node_count"])


def count_useless(tree, to_count):

    # start at the bottom
    for child in tree.children:
        if child.operator:
            count_useless(child, to_count)

    operator_count = {op: 0 for op in Operator}
    activity_count = {ac: 0 for ac in to_count["activity_list"]}

    # get preliminary useful information
    for child in tree.children:
        if child.operator:
            operator_count[child.operator] += 1
        elif is_leaf(child):
            activity_count[child.label] += 1

        to_count["node_count"] += 1

    # count useless and continue to check children
    for child in tree.children:
        if is_useless(child, operator_count, activity_count):
            to_count["useless"] += 1
            child.useless = True
        else:
            child.useless = False


def is_useless(node, operators, activities):
    # if current node is an activity
    if node.label or is_tau_leaf(node):
        if node.parent.operator in {Operator.SEQUENCE, Operator.PARALLEL}:
            if is_tau_leaf(node):
                # 1. node is tau in a SEQUENCE or PARALLEL operator
                return True
        elif node.parent.operator in {Operator.XOR, Operator.OR}:
            if is_leaf(node) and activities[node.label] > 1:
                # 4. node is duplicate tau (or activity) in an OR or XOR operator
                activities[node.label] -= 1
                return True
        elif node.parent.operator == Operator.LOOP:
            if is_tau_leaf(node) \
               and activities[None] == 2 and sum(activities.values()) == 2 \
               and operators[Operator.LOOP] == 1 and sum(operators.values()) == 1:
                # 6. node is tau along with another tau and a loop as fellow children
                node.rule6 = True
                return True
    else:
        if len(node.children) < 2:
            # 2. node is an operator with only one child
            return True
        elif node.parent.operator == node.operator and node.operator != Operator.LOOP:
            # 7. if node is of same type as parent (except for loops)
            return True
        elif False not in {child.useless for child in node.children}:
            # 3. node is an operator with only useless children
            return True
        elif node.operator == Operator.LOOP and len(node.children) == 3:
            for child in node.children:
                if child.rule6 is not None:
                    # 5. if rule 6 was activated, loop operator is useless
                    return True

    return False


class Variants(Enum):
    SIMPLICITY_SIZE = {"name": "simplicity_size", "function": simplicity_size}
    SIMPLICITY_OCCURENCE = {"name": "simplicity_occurence", "function": simplicity_occurence}
    SIMPLICITY_USELESS_NODES = {"name": "simplicity_useless", "function": simplicity_useless_nodes}
