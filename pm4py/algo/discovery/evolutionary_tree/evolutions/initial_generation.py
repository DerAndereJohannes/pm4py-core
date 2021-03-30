from enum import Enum
from copy import deepcopy
from random import randint
from pm4py.algo.discovery.evolutionary_tree.parameters import Parameters, TreeKeys
from pm4py.objects.process_tree.process_tree import ProcessTree, Operator
from pm4py.objects.log.util.log import get_event_labels


operators = [Operator.SEQUENCE, Operator.XOR,
             Operator.PARALLEL, Operator.LOOP]


def random_generation(log, activity_labels, parameters):
    new_tree = random_selection(None, activity_labels)

    # if the initial node is not an activity node
    if new_tree.label is None:
        generate_tree(new_tree, activity_labels)

    return new_tree


def generate_tree(parent_node, log_labels):
    # if activity node, stop
    if parent_node.label is not None:
        return

    # if operator node, continue until all operators have 2 children
    while len(parent_node.children) < 2:
        parent_node.children.append(random_selection(parent_node, log_labels))
        generate_tree(parent_node.children[-1], log_labels)


def random_selection(parent, log_labels):
    op_ac = randint(0, 1)

    # if operator
    if op_ac:
        operator_id = randint(0, len(operators) - 1)
        return ProcessTree(operator=operators[operator_id], parent=parent)
    else:
        activity_id = randint(0, len(log_labels) - 1)
        return ProcessTree(label=log_labels[activity_id], parent=parent)


def trace_model(log, activity_labels, parameters):
    # generate all trace process trees
    if not parameters["trace_trees"]:
        parameters["trace_trees"] = create_trace_trees(log, parameters)

    # return merged initial trace trees together
    return merge_trace_trees(parameters["trace_trees"], parameters)


def create_trace_trees(log, parameters):
    trace_trees = []

    for trace in log:
        # get activity count
        events = [a[parameters[Parameters.ACTIVITY_KEY.value]] for a in trace]
        ev_executions = set()
        ev_duplicates = list()
        for ev in events:
            if ev in ev_executions and ev not in ev_duplicates:
                ev_duplicates.append(ev)
            else:
                ev_executions.add(ev)

        # initialize tree
        pt = ProcessTree(operator=Operator.SEQUENCE)

        # if there are no duplicates, return sequence of whole trace
        if len(ev_duplicates) == 0:
            pt.children = [ProcessTree(label=ev, parent=pt) for ev in events]
        else:
            has_looped = False
            for ev in events:
                if ev not in ev_duplicates:
                    pt.children.append(ProcessTree(label=ev, parent=pt))
                elif not has_looped:
                    pt.children.append(generate_loop(ev_duplicates, pt))
                    has_looped = True

        trace_trees.append(pt)
    return trace_trees


def merge_trace_trees(tree_list, parameters):
    # start with a random trace tree
    initial_id = randint(0, len(tree_list) - 1)
    merged_tree = deepcopy(tree_list[initial_id])
    tree_children = [repr(pt) for pt in merged_tree.children]
    is_merged = {initial_id}
    to_continue = randint(0, 1)

    # while should merge more traces
    while to_continue:
        to_merge = randint(0, len(tree_list) - 1)
        # check if trace is already merged
        while to_merge in is_merged:
            to_merge = randint(0, len(tree_list) - 1)

        # get children representation from candidate to merge
        to_merge_children = [repr(pt) for pt in tree_list[to_merge]]

        missing_from_other = get_missing_sections(tree_children, to_merge_children)
        missing_from_main = get_missing_sections(to_merge_children, tree_children)


        is_merged.add(to_merge)
        to_continue = randint(0, 1)

    return merged_tree


def get_missing_sections(main_children, other_children):
    missing_start = -1
    missing_from_other = []
    for child_id in range(main_children):
        # if missing in other model
        if main_children[child_id] not in other_children:
            if missing_start == -1:
                missing_start = child_id
        # if end of missing section
        elif missing_start != -1:
            missing_end = child_id - 1
            before = {child for child in main_children[:missing_start]}
            after = {child for child in main_children[missing_end:]}
            missing_from_other.append((missing_start, missing_end, before, after))
            missing_start = -1

    # if missing section has not been closed, close it
    if missing_start != -1:
        missing_end = len(main_children) - 1
        before = {child for child in main_children[:missing_start]}
        after = {child for child in main_children[missing_end:]}
        missing_from_other.append((missing_start, missing_end, before, after))

    return missing_from_other


def generate_loop(duplicates, parent):
    loop_root = ProcessTree(operator=Operator.LOOP, parent=parent)
    # get number of options
    seq_length = len(duplicates)
    # select which activity to be singled out (if any)
    single_choice = randint(0, seq_length)

    # generate the single activity
    if single_choice == seq_length:
        single = ProcessTree(parent=loop_root)
    else:
        single = ProcessTree(label=duplicates[single_choice], parent=loop_root)

    # generate the sequence operator and children
    seq = ProcessTree(operator=Operator.SEQUENCE, parent=loop_root)
    seq_child = {duplicates[i] for i in range(seq_length) if i != single_choice}
    seq.children = [ProcessTree(label=a, parent=seq) for a in seq_child]

    # decide on which comes first
    if randint(0, 1):
        loop_root.children.extend((single, seq))
    else:
        loop_root.children.extend((seq, single))

    # add final tau
    loop_root.children.append(ProcessTree(parent=loop_root))

    return loop_root


def single_trace_model(log, activity_labels, parameters):
    # generate all trace process trees
    if "trace_trees" not in parameters:
        parameters["trace_trees"] = create_trace_trees(log, parameters)
    if "trace_id_used" not in parameters:
        parameters["trace_id_used"] = set()
    # if all traces have been used, create a random tree
    if len(parameters["trace_id_used"]) >= len(log):
        return random_generation(log, activity_labels, parameters)

    # fetch remaining unused trace_ids
    remaining_ids = list({x for x in range(len(log))} - parameters["trace_id_used"])
    # select new trace from remaining ids
    selector = randint(0, len(remaining_ids) - 1)
    parameters["trace_id_used"].add(remaining_ids[selector])

    # return random trace from generated trees
    return parameters["trace_trees"][remaining_ids[selector]]


class Variants(Enum):
    RANDOM = random_generation
    SINGLE_TRACE = single_trace_model
    TRACE_MODEL = trace_model


DEFAULT_VARIANT = Variants.RANDOM


def generate_initial_population(log, parameters, variant=DEFAULT_VARIANT):
    population = [None]*parameters[Parameters.POPULATION_SIZE.value]
    activity_labels = get_event_labels(log, parameters[Parameters.ACTIVITY_KEY.value])
    trees = set()

    for treeid in range(len(population)):
        population[treeid] = dict()
        population[treeid][TreeKeys.ID.value] = treeid
        population[treeid][TreeKeys.LOG_ACTIVITIES.value] = activity_labels
        new_tree = None
        # prevent duplicates
        while new_tree is None or new_tree in trees:
            new_tree = variant(log, activity_labels, parameters)

        population[treeid][TreeKeys.TREE.value] = new_tree
        trees.add(new_tree)

    return population
