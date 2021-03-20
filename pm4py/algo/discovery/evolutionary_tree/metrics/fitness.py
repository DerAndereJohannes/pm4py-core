from enum import Enum
from pm4py.algo.discovery.evolutionary_tree.parameters import TreeKeys
from pm4py.algo.conformance.tree_alignments.algorithm import apply as compute_tree_alignments
from pm4py.algo.conformance.tree_alignments.algorithm import Variants as fitness_variants
import pm4py.evaluation.replay_fitness.evaluator as evaluator


def tree_alignments(log, tree):
    tree["alignment"] = compute_tree_alignments(log, tree[TreeKeys.TREE.value], variant=fitness_variants.APPROXIMATED_MATRIX_LP)
    return evaluator.evaluate(tree["alignment"], variant=evaluator.ALIGNMENT_BASED)["averageFitness"]


class Variants(Enum):
    TREE_ALIGNMENTS = {"name": "alignment_fitness", "function": tree_alignments}
