"""
This is the main file of the tool "Multi-vector simulation tool".

Tool structure:

(parent)    multi_vector_simulator.py

(child)    constants.py

(child)     --A0_initialization.py

(child)      --B0_data_input.py

(child)     --C0_data_processing.py
(child sub)    --C1_verification.py
(child sub)    --C2_economic_processing.py

(child)     --D0_modelling_and_optimization.py
(child sub)    --D1_model_components.py
(child sub)    --D2_model_constraints.py

(child)     --E0_evaluation.py
(child sub)    --E1_process_results.py
(child sub)    --E2_verification_of_constraints.py
(child sub)    --E4_verification.py

(child)    --F0_output.py
(child sub)    --F1_plotting.py
(child sub)    --F2_autoreport.py
patent:     Main file, all children connected through parent
child:      Child file, one of the main functions of the tool.
            Internal processes, feeds output back to parent
child-sub:  Sub-child function, feeds only back to child functions
"""

import logging
import json

# Loading all child functions
import multi_vector_simulator.B0_data_input_json as B0
import multi_vector_simulator.C0_data_processing as C0
import multi_vector_simulator.D0_modelling_and_optimization as D0
import multi_vector_simulator.E0_evaluation as E0
import multi_vector_simulator.F0_output as F0
from multi_vector_simulator.version import version_num, version_date
from multi_vector_simulator.utils import data_parser


def run_simulation(json_dict, epa_format=True, **kwargs):
    r"""
     Starts MVS tool simulation from an input json file

     Parameters
    -----------
     json_dict: dict
         json from http request
     epa_format: bool, optional
         Specifies whether the output is formatted for EPA standards
         Default: True

     Other Parameters
     ----------------
     pdf_report: bool, optional
         Can generate an automatic pdf report of the simulation's results (True) or not (False)
         Default: False.
     display_output : str, optional
         Sets the level of displayed logging messages.
         Options: "debug", "info", "warning", "error". Default: "info".
     lp_file_output : bool, optional
         Specifies whether linear equation system generated is saved as lp file.
         Default: False.

    """

    welcome_text = (
        "\n \n Multi-Vector Simulation Tool (MVS) V"
        + version_num
        + " "
        + "\n Version: "
        + version_date
        + " "
        + '\n Part of the toolbox of H2020 project "E-LAND", '
        + "Integrated multi-vector management system for Energy isLANDs"
        + "\n Coded at: Reiner Lemoine Institute (Berlin) "
        + "\n Contributors: Martha M. Hoffmann \n \n "
    )

    logging.info(welcome_text)

    logging.debug("Accessing script: B0_data_input_json")
    dict_values = B0.convert_from_json_to_special_types(json_dict)

    print("")
    logging.debug("Accessing script: C0_data_processing")
    C0.all(dict_values)

    print("")
    logging.debug("Accessing script: D0_modelling_and_optimization")
    results_meta, results_main = D0.run_oemof(dict_values)

    print("")
    logging.debug("Accessing script: E0_evaluation")
    E0.evaluate_dict(dict_values, results_main, results_meta)

    logging.debug("Convert results to json")

    if epa_format is True:
        epa_dict_values = data_parser.convert_mvs_params_to_epa(dict_values)

        json_values = F0.store_as_json(epa_dict_values)
        answer = json.loads(json_values)

    else:
        answer = dict_values

    return answer
