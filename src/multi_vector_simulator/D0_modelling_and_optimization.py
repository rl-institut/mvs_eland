import logging
import os
import timeit

from oemof.solph import processing
import oemof.solph as solph

import multi_vector_simulator.D1_model_components as D1
import multi_vector_simulator.D2_model_constraints as D2

from multi_vector_simulator.utils.constants import (
    PATH_OUTPUT_FOLDER,
    ES_GRAPH,
    PATHS_TO_PLOTS,
    PLOTS_ES,
)
from multi_vector_simulator.utils.constants_json_strings import (
    ENERGY_BUSSES,
    OEMOF_ASSET_TYPE,
    ACCEPTED_ASSETS_FOR_ASSET_GROUPS,
    OEMOF_GEN_STORAGE,
    OEMOF_SINK,
    OEMOF_SOURCE,
    OEMOF_TRANSFORMER,
    OEMOF_BUSSES,
    VALUE,
    SIMULATION_SETTINGS,
    LABEL,
    TIME_INDEX,
    OUTPUT_LP_FILE,
    SIMULATION_RESULTS,
    OBJECTIVE_VALUE,
    SIMULTATION_TIME,
)

"""
Functional requirements of module D0:
- measure time needed to build model
- measure time needed to solve model
- generate energy system model for oemof
- create dictionary of components so that they can be used for constraints and some
- raise warning if component not a (in mvs defined) oemof model type
- add all energy conversion, energy consumption, energy production, energy storage devices model
- plot network graph
- at constraints to remote model
- store lp file (optional)
- start oemof simulation
- process results by giving them to the next function
- dump oemof results
- add simulation parameters to dict values 
"""


class WrongOemofAssetForGroupError(ValueError):
    # Exception raised when an asset group has an asset with an denied oemof type
    pass


class UnknownOemofAssetType(ValueError):
    # Exception raised in case an asset type is defined for an asset group constants_json_strings but the oemof function is not jet defined (only dev)
    pass


def run_oemof(dict_values, save_energy_system_graph=False):
    """
    Creates and solves energy system model generated from excel template inputs.
    Each component is included by calling its constructor function in D1_model_components.

    Parameters
    ----------
    dict values: dict
        Includes all dictionary values describing the whole project, including costs,
        technical parameters and components. In C0_data_processing, each component was attributed
        with a certain in/output bus.

    Returns
    -------
    saves and returns oemof simulation results
    """

    start = timer.initalize()

    model, dict_model = model_building.initialize(dict_values)

    model = model_building.adding_assets_to_energysystem_model(
        dict_values, dict_model, model
    )

    model_building.plot_networkx_graph(
        dict_values, model, save_energy_system_graph=save_energy_system_graph
    )

    logging.debug("Creating oemof model based on created components and busses...")
    local_energy_system = solph.Model(model)
    logging.debug("Created oemof model based on created components and busses.")

    local_energy_system = D2.add_constraints(
        local_energy_system, dict_values, dict_model
    )

    model_building.store_lp_file(dict_values, local_energy_system)

    model, results_main, results_meta = model_building.simulating(
        dict_values, model, local_energy_system
    )

    timer.stop(dict_values, start)

    return results_meta, results_main


class model_building:
    def initialize(dict_values):
        """
        Initalization of oemof model

        Parameters
        ----------
        dict_values: dict
            dictionary of simulation

        Returns
        -------
        oemof energy model (oemof.solph.network.EnergySystem), dict_model which gathers the assets added to this model later.
        """
        logging.info("Initializing oemof simulation.")
        model = solph.EnergySystem(
            timeindex=dict_values[SIMULATION_SETTINGS][TIME_INDEX]
        )

        # this dictionary will include all generated oemof objects
        dict_model = {
            OEMOF_BUSSES: {},
            OEMOF_SINK: {},
            OEMOF_SOURCE: {},
            OEMOF_TRANSFORMER: {},
            OEMOF_GEN_STORAGE: {},
        }

        return model, dict_model

    def adding_assets_to_energysystem_model(dict_values, dict_model, model, **kwargs):
        """

        Parameters
        ----------
        dict_values: dict
            dict of simulation data

        dict_model:
            Updated list of assets in the oemof energy system model

        model: oemof.solph.network.EnergySystem
            Model of oemof energy system

        Returns
        -------

        """
        logging.info("Adding components to oemof energy system model...")

        # Busses have to be defined first
        for bus in dict_values[ENERGY_BUSSES]:
            D1.bus(model, dict_values[ENERGY_BUSSES][bus][LABEL], **dict_model)

        # Adding step by step all assets defined within the asset groups
        for asset_group in ACCEPTED_ASSETS_FOR_ASSET_GROUPS:
            if asset_group in dict_values:
                for asset in dict_values[asset_group]:
                    type = dict_values[asset_group][asset][OEMOF_ASSET_TYPE]
                    # Checking if the asset type is one accepted for the asset group (security measure)
                    if type in ACCEPTED_ASSETS_FOR_ASSET_GROUPS[asset_group]:
                        # if so, then the appropriate function of D1 should be called
                        if type == OEMOF_TRANSFORMER:
                            D1.transformer(
                                model, dict_values[asset_group][asset], **dict_model
                            )
                        elif type == OEMOF_SINK:
                            D1.sink(
                                model, dict_values[asset_group][asset], **dict_model
                            )
                        elif type == OEMOF_SOURCE:
                            D1.source(
                                model, dict_values[asset_group][asset], **dict_model
                            )
                        elif type == OEMOF_GEN_STORAGE:
                            D1.storage(
                                model, dict_values[asset_group][asset], **dict_model
                            )
                        else:
                            raise UnknownOemofAssetType(
                                f"Asset {asset} has type {type}, "
                                f"but this type is not a defined oemof asset type."
                            )

                    else:
                        raise WrongOemofAssetForGroupError(
                            f"Asset {asset} has type {type}, "
                            f"but this type is not an asset type attributed to asset group {asset_group}"
                            f" for oemof model generation."
                        )

        logging.debug("All components added.")
        return model

    def plot_networkx_graph(dict_values, model, save_energy_system_graph=False):
        """
        Plots a graph of the energy system if that graph is to be displayed or stored.

        Parameters
        ----------
        dict_values: dict
            All simulation inputs

        model: `oemof.solph.network.EnergySystem`
            oemof-solph object for energy system model

        save_energy_system_graph: bool
            if True, save the graph in the mvs output folder
            Default: False

        Returns
        -------
        None
        """
        if save_energy_system_graph is True:
            from multi_vector_simulator.F1_plotting import ESGraphRenderer

            fpath = os.path.join(
                dict_values[SIMULATION_SETTINGS][PATH_OUTPUT_FOLDER], ES_GRAPH
            )
            dict_values[PATHS_TO_PLOTS][PLOTS_ES] += str(fpath)

            # Draw the energy system model
            graph = ESGraphRenderer(model, filepath=fpath)
            logging.debug("Created graph of the energy system model.")

            graph.render()

    def store_lp_file(dict_values, local_energy_system):
        """
        Stores linear equation system generated with pyomo as an "lp file".

        Parameters
        ----------
        dict_values: dict
            All simulation input data

        local_energy_system: object
            pyomo object including all constraints of the energy system

        Returns
        -------
        Nothing.
        """
        path_lp_file = os.path.join(
            dict_values[SIMULATION_SETTINGS][PATH_OUTPUT_FOLDER], "lp_file.lp"
        )
        if dict_values[SIMULATION_SETTINGS][OUTPUT_LP_FILE][VALUE] is True:
            logging.debug("Saving to lp-file.")
            local_energy_system.write(
                path_lp_file, io_options={"symbolic_solver_labels": True},
            )

    def simulating(dict_values, model, local_energy_system):
        """
        Initiates the oemof-solph simulation, accesses results and writes main results into dict

        Parameters
        ----------
        dict_values: dict
            All simulation inputs

        model: object
            oemof-solph object for energy system model

        local_energy_system: object
            pyomo object storing all constraints of the energy system model

        Returns
        -------
        Updated model with results, main results (flows, assets) and meta results (simulation)
        """
        logging.info("Starting simulation.")
        local_energy_system.solve(
            solver="cbc",
            solve_kwargs={
                "tee": False
            },  # if tee_switch is true solver messages will be displayed
            cmdline_options={"ratioGap": str(0.03)},
        )  # ratioGap allowedGap mipgap
        logging.info("Problem solved.")

        # add results to the energy system to make it possible to store them.
        results_main = processing.results(local_energy_system)
        results_meta = processing.meta_results(local_energy_system)

        model.results["main"] = results_main
        model.results["meta"] = results_meta

        dict_values.update(
            {
                SIMULATION_RESULTS: {
                    LABEL: SIMULATION_RESULTS,
                    OBJECTIVE_VALUE: results_meta["objective"],
                    SIMULTATION_TIME: round(results_meta["solver"]["Time"], 2),
                }
            }
        )
        logging.info(
            "Simulation time: %s minutes.",
            round(dict_values[SIMULATION_RESULTS][SIMULTATION_TIME] / 60, 2),
        )
        return model, results_main, results_main


class timer:
    def initalize():
        """
        Starts a timer
        Returns
        -------
        """
        # Start clock to determine total simulation time
        start = timeit.default_timer()
        return start

    def stop(dict_values, start):
        """
        Ends timer and adds duration of simulation to dict_values
        Parameters
        ----------
        dict_values: dict
            Dict of simulation including SIMULATION_RESULTS key
        start: timestamp
            start time of timer

        Returns
        -------
        Simulation time in dict_values
        """
        duration = timeit.default_timer() - start
        dict_values[SIMULATION_RESULTS].update({"modelling_time": round(duration, 2)})

        logging.info(
            "Moddeling time: %s minutes.",
            round(dict_values[SIMULATION_RESULTS]["modelling_time"] / 60, 2),
        )
