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
from pm4py.util import constants
from enum import Enum


class Parameters(Enum):
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    START_TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_START_TIMESTAMP_KEY
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    CASE_ID_KEY = constants.PARAMETER_CONSTANT_CASEID_KEY
    DEPENDENCY_THRESH = "dependency_thresh"
    AND_MEASURE_THRESH = "and_measure_thresh"
    MIN_ACT_COUNT = "min_act_count"
    MIN_DFG_OCCURRENCES = "min_dfg_occurrences"
    DFG_PRE_CLEANING_NOISE_THRESH = "dfg_pre_cleaning_noise_thresh"
    LOOP_LENGTH_TWO_THRESH = "loop_length_two_thresh"
    HEU_NET_DECORATION = "heu_net_decoration"
