"""
This is the main file of the tool "Multi-vector simulation tool".

Tool structure:

(parent)    multi_vector_simulator.py
(child)     --A0_initialization.py

(child)      --B0_data_input.py

(child)     --C0_data_processing.py
(child sub)    --C1_verification.py
(child sub)    --C2_economic_processing.py

(child)     --D0_modelling_and_optimization.py
(child sub)    --D1_model_components.py
(child sub)    --D2_model_constraints.py

(child)     --F0_output.py
(child sub)    --E1_process_results.py
(child sub)    --E2_verification_of_constraints.py
(child sub)    --E3_indicator_calculation.py

patent:     Main file, all children connected through parent
child:      Child file, one of the main functions of the tool.
            Internal processes, feeds output back to parent
child-sub:  Sub-child function, feeds only back to child functions
"""

import logging
import os

import multi_vector_simulator.A0_initialization as A0
import multi_vector_simulator.A1_csv_to_json as A1
import multi_vector_simulator.B0_data_input_json as B0
import multi_vector_simulator.C0_data_processing as C0
import multi_vector_simulator.D0_modelling_and_optimization as D0
import multi_vector_simulator.E0_evaluation as E0
import multi_vector_simulator.F0_output as F0

try:
    from multi_vector_simulator.F2_autoreport import (
        create_app,
        open_in_browser,
        print_pdf,
    )
except ModuleNotFoundError:
    logging.warning(
        "Some packages are mising to generate automatic report, if you want to install them use \n\tpip install multi-vector-simulator[report]"
    )

from multi_vector_simulator.version import version_num, version_date

from multi_vector_simulator.utils import copy_inputs_template

from multi_vector_simulator.utils.constants import (
    REPO_PATH,
    CSV_ELEMENTS,
    CSV_EXT,
    PATH_INPUT_FILE,
    PATH_INPUT_FOLDER,
    PATH_OUTPUT_FOLDER,
    INPUT_TYPE,
    JSON_WITH_RESULTS,
    REPORT_FOLDER,
    PDF_REPORT,
    ARG_PDF,
    ARG_REPORT_PATH,
    ARG_PATH_SIM_OUTPUT,
    ARG_DEBUG_REPORT,
    SIMULATION_SETTINGS,
    JSON_PROCESSED,
    JSON_FILE_EXTENSION,
)


def main(**kwargs):
    r"""
    Starts MVS tool simulations.

    Other Parameters
    ----------------
    overwrite : bool, optional
        Determines whether to replace existing results in `path_output_folder`
        with the results of the current simulation (True) or not (False).
        Default: False.
    pdf_report: bool, optional
        Can generate an automatic pdf report of the simulation's results (True) or not (False)
        Default: False.
    input_type : str, optional
        Defines whether the input is taken from the `mvs_config.json` file
        ("json") or from csv files ('csv') located within
        <path_input_folder>/csv_elements/. Default: 'json'.
    path_input_folder : str, optional
        The path to the directory where the input CSVs/JSON files are located.
        Default: 'inputs/'.
    path_output_folder : str, optional
        The path to the directory where the results of the simulation such as
        the plots, time series, results JSON files are saved by MVS E-Lands.
        Default: 'MVS_outputs/'
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

    logging.debug("Accessing script: A0_initialization")

    user_input = A0.process_user_arguments(
        welcome_text=welcome_text, **kwargs
    )

    # Read all inputs
    #    print("")
    #    # todo: is user input completely used?
    #    dict_values = data_input.load_json(user_input[PATH_INPUT_FILE ])

    move_copy_config_file = False

    if user_input[INPUT_TYPE] == CSV_EXT:
        logging.debug("Accessing script: A1_csv_to_json")
        move_copy_config_file = True
        A1.create_input_json(
            input_directory=os.path.join(user_input[PATH_INPUT_FOLDER], CSV_ELEMENTS)
        )

    logging.debug("Accessing script: B0_data_input_json")
    dict_values = B0.load_json(
        user_input[PATH_INPUT_FILE],
        path_input_folder=user_input[PATH_INPUT_FOLDER],
        path_output_folder=user_input[PATH_OUTPUT_FOLDER],
        move_copy=move_copy_config_file,
        set_default_values=True,
    )

    print("")
    logging.debug("Accessing script: C0_data_processing")
    C0.all(dict_values)

    F0.store_as_json(
        dict_values,
        dict_values[SIMULATION_SETTINGS][PATH_OUTPUT_FOLDER],
        JSON_PROCESSED,
    )

    if "path_pdf_report" in user_input or "path_png_figs" in user_input:
        save_energy_system_graph = True
    else:
        save_energy_system_graph = False

    print("")
    logging.debug("Accessing script: D0_modelling_and_optimization")
    results_meta, results_main = D0.run_oemof(
        dict_values, save_energy_system_graph=save_energy_system_graph,
    )

    print("")
    logging.debug("Accessing script: E0_evaluation")
    E0.evaluate_dict(dict_values, results_main, results_meta)

    logging.debug("Accessing script: F0_outputs")
    F0.evaluate_dict(
        dict_values,
        path_pdf_report=user_input.get("path_pdf_report", None),
        path_png_figs=user_input.get("path_png_figs", None),
    )
    return 1


def report(pdf=None, path_simulation_output_json=None, path_pdf_report=None):

    """Display the report of a MVS simulation

    Command line use:

    .. code-block:: bash

        mvs_report [-h] [-i [PATH_SIM_OUTPUT]] [-o [REPORT_PATH]] [-pdf]

    optional command line arguments:
      -h, --help           show this help message and exit
      -pdf [PRINT_REPORT]  print the report as pdf (default: False)
      -i [OUTPUT_FOLDER]   path to the simulation result json file
                           'json_with_results.json'
      -o [REPORT_PATH]     path to save the pdf report
      -d [DEBUG_REPORT]    run the dash app in debug mode with hot-reload

    Parameters
    ----------
    pdf: bool
        if True a pdf report should be generated
        Default: False
    path_simulation_output_json: str
        path to the simulation result json file 'json_with_results.json'
    path_pdf_report: str
        path to save the pdf report

    Returns
    -------

    Save a pdf report if option -pdf is provided, otherwise display the report as an app
    """

    # Parse the arguments from the command line
    parser = A0.report_arg_parser()
    args = vars(parser.parse_args())

    # Give priority from user input kwargs over command line arguments
    # However the command line arguments have priority over default kwargs
    if pdf is None:
        pdf = args.get(ARG_PDF, False)
    if path_simulation_output_json is None:
        path_simulation_output_json = args.get(ARG_PATH_SIM_OUTPUT)

    if path_pdf_report is None:
        path_pdf_report = args.get(ARG_REPORT_PATH)

    # if the user only provided the path to the folder, we complete with default json file
    if os.path.isdir(path_simulation_output_json) is True:
        path_simulation_output_json = os.path.join(
            path_simulation_output_json, JSON_WITH_RESULTS + JSON_FILE_EXTENSION
        )
        logging.warning(
            f"Only path to a folder provided ({args.get(ARG_PATH_SIM_OUTPUT)}), looking now for default {JSON_WITH_RESULTS + JSON_FILE_EXTENSION} file within this folder"
        )

    if os.path.exists(path_simulation_output_json) is False:
        raise FileNotFoundError(
            "Simulation results file {} not found. You need to run a simulation to generate "
            "the data before you can generate a report\n\n\tsee `mvs_tool -h` for help on how "
            "to run a simulation\n".format(path_simulation_output_json)
        )
    else:
        # path to the mvs simulation output files
        path_sim_output = os.path.dirname(path_simulation_output_json)

        # if report path is not specified it will be included in the mvs simulation outputs folder
        if path_pdf_report == "":
            path_pdf_report = os.path.join(path_sim_output, REPORT_FOLDER, PDF_REPORT)

        # load the results of a simulation
        dict_values = B0.load_json(
            path_simulation_output_json, flag_missing_values=False
        )
        test_app = create_app(dict_values, path_sim_output=path_sim_output)
        banner = "*" * 40
        print(banner + "\nPress ctrl+c to stop the report server\n" + banner)
        if pdf is True:
            print_pdf(test_app, path_pdf_report=path_pdf_report)
        else:
            if args.get(ARG_DEBUG_REPORT) is True:
                test_app.run_server(debug=True)
            else:
                # run the dash server for 600s before shutting it down
                open_in_browser(test_app, timeout=600)
                print(
                    banner
                    + "\nThe report server has timed out.\nTo start it again run "
                    "`mvs_report`.\nTo let it run for a longer time, change timeout setting in "
                    "the cli.py file\n" + banner
                )


def create_input_template_folder():
    """Create a copy of the input_template folder in the current directory

    The input_template folder is located within the multi_vector_simulator package

    Returns
    -------
    None, create a new folder in the current directory
    """

    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    copy_inputs_template(REPO_PATH)


if __name__ == "__main__":
    main()
