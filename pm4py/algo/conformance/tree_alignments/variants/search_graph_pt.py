'''
    This file is part of PM4Py (More Info: https://pm4py.fit.fraunhofer.de).

    PM4Py is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    PM4Py is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with PM4Py.  If not, see <https://www.gnu.org/licenses/>.
'''
import copy
import heapq
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from enum import Enum
from typing import List, Any, Optional

from pm4py.objects.log.log import Trace
from pm4py.objects.petri import align_utils
from pm4py.algo.conformance.tree_alignments.util import search_graph_pt_replay_semantics as pt_sem
from pm4py.objects.process_tree import util as pt_util
from pm4py.objects.process_tree.process_tree import ProcessTree
from pm4py.objects.process_tree.process_tree import Operator
from pm4py.util import exec_utils, constants, xes_constants
from pm4py.objects.log.log import EventLog
from pm4py.util import variants_util
from pm4py.algo.reduction.variants import tree_tr_based
import pkgutil


class Parameters(Enum):
    CORES = 'cores'
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    ENABLE_REDUCTION = 'enable_reduction'
    SHOW_PROGRESS_BAR = "show_progress_bar"


class SGASearchState:
    def __init__(self, costs: float, index: int, state: pt_sem.ProcessTreeState,
                 leaves: Optional[List[ProcessTree]] = None,
                 parent: Any = None, children: List[Any] = None):
        self.costs = costs  # costs of the solution of this state
        self.index = index  # index 'to be explained'
        self.state = state  # state in the model
        self.leaves = leaves if leaves is not None else list()  # leaves that 'got you here'
        self.parent = parent  # parent search state
        self.children = children if children is not None else set()  # successor search states

    def __lt__(self, other):
        if self.costs < other.costs:
            return True
        elif self.costs == other.costs:
            return self.index > other.index
        else:
            return False

    def __str__(self):
        return '(' + str(self.costs) + ',' + str(self.index) + ',' + str(self.state) + ')'


def _construct_result_dictionary(state: SGASearchState, variant: List[str]):
    result = dict()
    result['cost'] = state.costs
    alignment = list()
    current_state = state
    parent_state = state.parent
    while parent_state is not None:
        if len(current_state.leaves) > 0:
            if current_state.index == len(variant):
                leaf_labels = list(reversed(list(map(lambda o: o.label, current_state.leaves))))
                if variant[-1] in leaf_labels:
                    i = leaf_labels.index(variant[-1])
                    leaves_reversed = list(reversed(current_state.leaves))
                    for j in range(len(leaves_reversed)):
                        if i == j:
                            alignment.append((variant[-1], leaves_reversed[j]))
                        else:
                            alignment.append((align_utils.SKIP, leaves_reversed[j]))
                else:
                    if current_state.costs - len(current_state.leaves) > parent_state.costs:
                        alignment.append((variant[parent_state.index], align_utils.SKIP))
                    for leaf in reversed(current_state.leaves):
                        alignment.append((align_utils.SKIP, leaf))
            else:
                alignment.append((variant[parent_state.index], current_state.leaves[len(current_state.leaves) - 1]))
                leaves_reversed = list(reversed(current_state.leaves))[1:]
                for n in leaves_reversed:
                    alignment.append((align_utils.SKIP, n))
        else:
            alignment.append((variant[parent_state.index], align_utils.SKIP))
        parent_state = parent_state.parent
        current_state = current_state.parent
    result['alignment'] = list(reversed(alignment))
    result['optimal'] = True
    return result


def _is_final_tree_state(state, pt):
    return state[(id(pt), pt)] == ProcessTree.OperatorState.CLOSED


def _update_costs_recursive(delta, states):
    for state in states:
        state.costs = state.costs - delta
        _update_costs_recursive(delta, state.children)


def _check_if_state_exists_and_update(search_state: SGASearchState, collection):
    match = False
    for alt in collection:
        if alt.index == search_state.index and alt.state == search_state.state:
            match = True
            if search_state.costs < alt.costs:
                _update_costs_recursive(alt.costs - search_state.costs, alt.children)
                alt.costs = search_state.costs
                alt.parent = search_state.parent
                alt.leaves = search_state.leaves
    return match


def _add_new_state(state, parent, open, closed):
    if not _check_if_state_exists_and_update(state, closed):
        if not _check_if_state_exists_and_update(state, open):
            parent.children.add(state)
            heapq.heappush(open, state)
        else:
            heapq.heapify(open)
    return open, closed


def _obtain_leaves_from_state_path(path, include_tau=False):
    return list(map(lambda t: t[0], list(
        filter(lambda t: t[0].operator is None and t[0].label is not None and t[1] == ProcessTree.OperatorState.OPEN,
               path)))) if not include_tau else list(map(lambda t: t[0], list(
        filter(lambda t: t[0].operator is None and t[1] == ProcessTree.OperatorState.OPEN,
               path))))


def _need_log_move(old_state, new_state, path) -> bool:
    if len(_obtain_leaves_from_state_path(path, include_tau=True)) > 0:
        return True
    choices = list(filter(lambda o: pt_util.is_any_operator_of(o[1], {Operator.XOR, Operator.LOOP}), old_state.keys()))
    for choice in choices:
        choice = choice[1]
        if pt_util.is_operator(choice, Operator.XOR):
            if (pt_util.is_in_state(choice, ProcessTree.OperatorState.FUTURE, old_state) or pt_util.is_in_state(choice,
                                                                                                                ProcessTree.OperatorState.CLOSED,
                                                                                                                old_state)) and \
                    old_state[(id(choice), choice)] != new_state[(id(choice), choice)]:
                return True
        elif pt_util.is_operator(choice, Operator.LOOP):
            for loop_child in choice.children:
                if (pt_util.is_in_state(loop_child, ProcessTree.OperatorState.FUTURE,
                                        old_state) or pt_util.is_in_state(loop_child,
                                                                          ProcessTree.OperatorState.CLOSED,
                                                                          old_state)) and \
                        old_state[(id(loop_child), loop_child)] != new_state[(id(loop_child), loop_child)]:
                    return True
    return False


def apply_variant(variant, tree_leaf_set, pt):
    lmcf = [1] * len(variant)
    initial_search_state = SGASearchState(0, 0, pt_sem.get_initial_state(pt))
    sga_closed = set()
    sga_open = [initial_search_state]
    heapq.heapify(sga_open)
    count = 0
    while not len(sga_open) == 0:
        count += 1
        sga_state = heapq.heappop(sga_open)
        if _is_final_tree_state(sga_state.state, pt) and sga_state.index == len(variant):
            return _construct_result_dictionary(sga_state, variant)
        else:
            sga_closed.add(sga_state)
            if sga_state.index < len(lmcf):
                candidates = [l for l in tree_leaf_set if
                              l.label is not None and l.label == variant[sga_state.index]]
                need_log_move = len(candidates) == 0
                for leaf in candidates:
                    path, new_state = pt_sem.shortest_path_to_enable(leaf, copy.copy(sga_state.state))
                    need_log_move = True if path is None else need_log_move
                    if path is not None:
                        model_moves = _obtain_leaves_from_state_path(path)
                        need_log_move = need_log_move if need_log_move else _need_log_move(sga_state.state, new_state,
                                                                                           path)
                        sync_path, new_state = pt_sem.shortest_path_to_close(leaf, new_state)
                        path.extend(sync_path)
                        leaves = _obtain_leaves_from_state_path(path, include_tau=True)
                        sga_open, sga_closed = _add_new_state(
                            SGASearchState(sga_state.costs + len(model_moves),
                                           sga_state.index + 1,
                                           new_state, leaves=leaves, parent=sga_state), sga_state,
                            sga_open,
                            sga_closed)
                if need_log_move:
                    sga_open, sga_closed = _add_new_state(
                        SGASearchState(sga_state.costs + lmcf[sga_state.index],
                                       sga_state.index + 1,
                                       copy.copy(sga_state.state), parent=sga_state), sga_state, sga_open, sga_closed)
            else:
                # FINISH
                path, new_state = pt_sem.shortest_path_to_close(pt, sga_state.state)
                model_moves = _obtain_leaves_from_state_path(path, include_tau=False)
                sga_state.state = new_state
                sga_state.costs = sga_state.costs + len(model_moves)
                sga_state.leaves.extend(_obtain_leaves_from_state_path(path, include_tau=True))
                heapq.heappush(sga_open, sga_state)


def apply_from_variants_tree_string(var_list, tree_string, parameters=None):
    """
    Apply the alignments from the specification of a list of variants in the log.
    The tree is specified as a PTML input

    Parameters
    ------------
    var_list
        List of variants (for each item, the first entry is the variant itself, the second entry may be the number of cases)
    tree_string
        PTML string representing the tree
    parameters
        Parameters of the algorithm

        Returns
    --------------
    dictio_alignments
        Dictionary that assigns to each variant its alignment
    """
    if parameters is None:
        parameters = {}

    from pm4py.objects.process_tree.importer.variants import ptml

    tree = ptml.import_tree_from_string(tree_string, parameters=parameters)

    res = apply_from_variants_list(var_list, tree, parameters=parameters)
    return res


def apply_from_variants_list(var_list, tree, parameters=None):
    """
    Apply the alignments from the specification of a list of variants in the log

    Parameters
    -------------
    var_list
        List of variants (for each item, the first entry is the variant itself, the second entry may be the number of cases)
    tree
        Process tree
    parameters
        Parameters of the algorithm

    Returns
    --------------
    dictio_alignments
        Dictionary that assigns to each variant its alignment
    """
    if parameters is None:
        parameters = {}

    dictio_alignments = {}
    log = EventLog()

    for index, varitem in enumerate(var_list):
        trace = variants_util.variant_to_trace(varitem[0], parameters=parameters)
        log.append(trace)

    alignments = apply(log, tree, parameters=parameters)
    for index, varitem in enumerate(var_list):
        dictio_alignments[varitem[0]] = alignments[index]
    return dictio_alignments


def get_reduced_tree(tree, trace, parameters=None):
    """
    Reduces the process tree in order to replay the trace

    Parameters
    ---------------
    tree
        Process tree
    trace
        Process execution

    Returns
    ---------------
    red_tree
        Reduced process tree (if the reduction is enabled)
    leaves
        Leaves of the tree
    """
    if parameters is None:
        parameters = {}
    enable_reduction = exec_utils.get_param_value(Parameters.ENABLE_REDUCTION, parameters, True)

    if enable_reduction:
        tree = tree_tr_based.apply(tree, trace, parameters=parameters)
    leaves = frozenset(pt_util.get_leaves(tree))

    return tree, leaves


def apply_multiprocessing(obj, pt, parameters=None):
    """
    Returns alignments for a process tree (using the multiprocessing package to distribute the workload
    among different cores)

    Parameters
    --------------
    obj
        Event log or trace (a conversion is done if necessary)
    pt
        Process tree
    parameters
        Parameters of the algorithm

    Returns
    --------------
    alignments
        Alignments
    """
    if parameters is None:
        parameters = {}

    leaves = frozenset(pt_util.get_leaves(pt))
    activity_key = exec_utils.get_param_value(Parameters.ACTIVITY_KEY, parameters, xes_constants.DEFAULT_NAME_KEY)
    num_cores = exec_utils.get_param_value(Parameters.CORES, parameters, multiprocessing.cpu_count() - 2)

    if type(obj) is Trace:
        variant = tuple(x[activity_key] for x in obj)
        tree, lvs = get_reduced_tree(pt, obj, parameters=parameters)
        return apply_variant(variant, lvs, tree)
    else:
        with ProcessPoolExecutor(max_workers=num_cores) as executor:
            ret = []
            best_worst_cost = apply_variant([], leaves, pt)["cost"]
            tree_red_dict = {}
            futures = {}
            align_dict = {}
            for trace in obj:
                variant = tuple(x[activity_key] for x in trace)
                if variant not in futures:
                    activities = frozenset(variant)
                    if activities not in tree_red_dict:
                        tree, lvs = get_reduced_tree(pt, trace, parameters=parameters)
                        tree_red_dict[activities] = (tree, lvs)
                    else:
                        tree, lvs = tree_red_dict[activities]
                    futures[variant] = executor.submit(apply_variant, variant, lvs, tree)
            for trace in obj:
                variant = tuple(x[activity_key] for x in trace)
                if variant not in align_dict:
                    al = futures[variant].result()
                    ltrace_bwc = len(trace) + best_worst_cost
                    # calculate fitness as in the Petri net alignments
                    if ltrace_bwc > 0:
                        al["fitness"] = 1.0 - al["cost"] / ltrace_bwc
                    else:
                        al["fitness"] = 0.0
                    # makes the cost uniform with Petri net alignments
                    al["cost"] *= 10000
                    align_dict[variant] = al
                ret.append(align_dict[variant])
        return ret


def apply(obj, pt, parameters=None):
    """
    Returns alignments for a process tree

    Parameters
    --------------
    obj
        Event log or trace (a conversion is done if necessary)
    pt
        Process tree
    parameters
        Parameters of the algorithm

    Returns
    --------------
    alignments
        Alignments
    """
    if parameters is None:
        parameters = {}

    progress = None
    show_progress_bar = exec_utils.get_param_value(Parameters.SHOW_PROGRESS_BAR, parameters, True)
    leaves = frozenset(pt_util.get_leaves(pt))
    activity_key = exec_utils.get_param_value(Parameters.ACTIVITY_KEY, parameters, xes_constants.DEFAULT_NAME_KEY)
    if type(obj) is Trace:
        variant = tuple(x[activity_key] for x in obj)
        tree, lvs = get_reduced_tree(pt, obj, parameters=parameters)
        return apply_variant(variant, lvs, tree)
    else:
        if show_progress_bar and pkgutil.find_loader("tqdm"):
            from pm4py.statistics.variants.log import get as variants_get
            variants = variants_get.get_variants(obj, parameters=parameters)
            if len(variants) > 1:
                from tqdm.auto import tqdm
                progress = tqdm(total=len(variants), desc="aligning log, completed variants :: ")
        ret = []
        best_worst_cost = apply_variant([], leaves, pt)["cost"]
        align_dict = {}
        tree_red_dict = {}
        for trace in obj:
            variant = tuple(x[activity_key] for x in trace)
            if variant not in align_dict:
                activities = frozenset(variant)
                if activities not in tree_red_dict:
                    tree, lvs = get_reduced_tree(pt, trace, parameters=parameters)
                    tree_red_dict[activities] = (tree, lvs)
                else:
                    tree, lvs = tree_red_dict[activities]
                al = apply_variant(variant, lvs, tree)
                ltrace_bwc = len(trace) + best_worst_cost
                # calculate fitness as in the Petri net alignments
                if ltrace_bwc > 0:
                    al["fitness"] = 1.0 - al["cost"] / ltrace_bwc
                else:
                    al["fitness"] = 0.0
                # makes the cost uniform with Petri net alignments
                al["cost"] *= 10000
                align_dict[variant] = al
                if progress is not None:
                    progress.update()
            ret.append(align_dict[variant])
        # gracefully close progress bar
        if progress is not None:
            progress.close()
        del progress
        return ret
