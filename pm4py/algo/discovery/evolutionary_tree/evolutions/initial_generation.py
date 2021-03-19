from enum import Enum
from random import randint
from pm4py.algo.discovery.evolutionary_tree.parameters import Parameters, TreeKeys
from pm4py.objects.process_tree.process_tree import ProcessTree
from pm4py.objects.process_tree.pt_operator import Operator
from pm4py.objects.log.util.log import get_event_labels


operators = [Operator.SEQUENCE, Operator.XOR,
             Operator.PARALLEL, Operator.LOOP,
             Operator.OR]


def random_generation(log, parameters):
    log_labels = get_event_labels(log, parameters[Parameters.ACTIVITY_KEY])
    new_tree = random_selection(None, log_labels)

    # if the initial node is not an activity node
    if new_tree.label is None:
        generate_tree(new_tree, log_labels)

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
    if op_ac or parent is None:
        operator_id = randint(0, len(operators) - 1)
        return ProcessTree(operator=operators[operator_id], parent=parent)
    else:
        activity_id = randint(0, len(log_labels) - 1)
        return ProcessTree(label=log_labels[activity_id], parent=parent)


class Variants(Enum):
    RANDOM = random_generation


DEFAULT_VARIANT = Variants.RANDOM


def generate_initial_population(log, parameters, variant=DEFAULT_VARIANT):
    population = [None]*parameters[Parameters.POPULATION_SIZE]

    for treeid in range(len(population)):
        population[treeid] = dict()
        population[treeid][TreeKeys.ID] = treeid
        population[treeid][TreeKeys.TREE] = variant(log, parameters)

    return population
