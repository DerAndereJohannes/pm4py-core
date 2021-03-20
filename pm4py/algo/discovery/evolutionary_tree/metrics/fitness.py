from enum import Enum
from pm4py.algo.discovery.evolutionary_tree.parameters import TreeKeys
from pm4py.algo.conformance.tree_alignments.algorithm import apply as compute_tree_alignments
import pm4py.evaluation.replay_fitness.evaluator as evaluator


def tree_alignments(log, tree):
    tree["alignment"] = compute_tree_alignments(log, tree[TreeKeys.TREE.value])
    tree[Variants.TREE_ALIGNMENTS.value["name"]] = evaluator.evaluate(tree["alignment"], variant=evaluator.ALIGNMENT_BASED)["averageFitness"]


class Variants(Enum):
    TREE_ALIGNMENTS = {"name": "alignment_fitness", "function": tree_alignments}
