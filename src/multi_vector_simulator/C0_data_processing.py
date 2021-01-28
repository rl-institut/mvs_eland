"""
Module C0 - Data processing
===========================

Module C0 prepares the data read from csv or json for simulation, ie. pre-processes it.
- Verify input values with C1
- Identify energyVectors and write them to project_data/sectors
- Create an excess sink for each bus
- Process start_date/simulation_duration to pd.datatimeindex (future: Also consider timesteplenghts)
- Add economic parameters to json with C2
- Calculate "simulation annuity" used in oemof model
- Add demand sinks to energyVectors (this should actually be changed and demand sinks should be added to bus relative to input_direction, also see issue #179)
- Translate input_directions/output_directions to bus names
- Add missing cost data to automatically generated objects (eg. DSO transformers)
- Read timeseries of assets and store into json (differ between one-column csv, multi-column csv)
- Read timeseries for parameter of an asset, eg. efficiency
- Parse list of inputs/outputs, eg. for chp
- Define dso sinks, sources, transformer stations (this will be changed due to bug #119), also for peak demand pricing
- Add a source if a conversion object is connected to a new input_direction (bug #186)
- Define all necessary energyBusses and add all assets that are connected to them specifically with asset name and label
- Multiply `maximumCap` of non-dispatchable sources by max(timeseries(kWh/kWp)) as the `maximumCap` is limiting the flow but we want to limit the installed capacity (see issue #446)
"""


import logging
import os
import sys
import pprint as pp
import pandas as pd
import warnings

from multi_vector_simulator.utils.constants import (
    TIME_SERIES,
    PATH_INPUT_FOLDER,
    PATH_OUTPUT_FOLDER,
    TYPE_BOOL,
    FILENAME,
    HEADER,
    JSON_PROCESSED,
)

from multi_vector_simulator.utils.constants_json_strings import *
from multi_vector_simulator.utils.exceptions import InvalidPeakDemandPricingPeriodsError
import multi_vector_simulator.B0_data_input_json as B0
import multi_vector_simulator.C1_verification as C1
import multi_vector_simulator.C2_economic_functions as C2
import multi_vector_simulator.F0_output as F0


def all(dict_values):
    """
    Function executing all pre-processing steps necessary
    :param dict_values
    All input data in dict format

    :return Pre-processed dictionary with all input parameters

    """
    # Check if any asset label has duplicates
    C1.check_for_label_duplicates(dict_values)

    B0.retrieve_date_time_info(dict_values[SIMULATION_SETTINGS])
    add_economic_parameters(dict_values[ECONOMIC_DATA])
    define_energy_vectors_from_busses(dict_values)
    C1.check_if_energy_vector_of_all_assets_is_valid(dict_values)

    ## Verify inputs
    # todo check whether input values can be true
    # C1.check_input_values(dict_values)
    # todo Check, whether files (demand, generation) are existing

    # Adds costs to each asset and sub-asset, adds time series to assets
    process_all_assets(dict_values)

    # check electricity price >= feed-in tariff todo: can be integrated into check_input_values() later
    C1.check_feedin_tariff_vs_energy_price(dict_values=dict_values)
    # check that energy supply costs are not lower than generation costs of any asset (of the same energy vector)
    C1.check_feedin_tariff_vs_levelized_cost_of_generation_of_production(dict_values)

    # check time series of non-dispatchable sources in range [0, 1]
    C1.check_non_dispatchable_source_time_series(dict_values)

    # display warning in case of maximum emissions constraint and no asset with zero emissions has no capacity limit
    C1.check_feasibility_of_maximum_emissions_constraint(dict_values)

    # display warning in case of emission_factor of provider > 0 while RE share = 100 %
    C1.check_emission_factor_of_providers(dict_values)

    # check efficiencies of storage capacity, raise error in case it is 0 and add a
    # warning in case it is <0.2 to help users to spot major change in #676
    C1.check_efficiency_of_storage_capacity(dict_values)

    # Perform basic (limited) check for module completeness
    C1.check_for_sufficient_assets_on_busses(dict_values)

    # just to be safe, run evaluation a second time
    C1.check_for_label_duplicates(dict_values)


def define_energy_vectors_from_busses(dict_values):
    """
    Identifies all energyVectors used in the energy system by looking at the defined energyBusses.
    The EnergyVectors later will be used to distribute costs and KPI amongst the sectors

    Parameters
    ----------
    dict_values: dict
        All input data in dict format

    Returns
    -------
    Update dict[PROJECT_DATA] by included energyVectors (LES_ENERGY_VECTOR_S)

    Notes
    -----
    Function tested with
    -  C1.test_define_energy_vectors_from_busses
    """
    dict_of_energy_vectors = {}
    energy_vector_string = ""
    for bus in dict_values[ENERGY_BUSSES]:
        energy_vector_name = dict_values[ENERGY_BUSSES][bus][ENERGY_VECTOR]
        if energy_vector_name not in dict_of_energy_vectors.keys():
            C1.check_if_energy_vector_is_defined_in_DEFAULT_WEIGHTS_ENERGY_CARRIERS(
                energy_vector_name, ENERGY_BUSSES, bus
            )
            dict_of_energy_vectors.update(
                {energy_vector_name: energy_vector_name.replace("_", " ")}
            )
            energy_vector_string = energy_vector_string + energy_vector_name + ", "

    dict_values[PROJECT_DATA].update({LES_ENERGY_VECTOR_S: dict_of_energy_vectors})
    logging.info(
        f"The energy system modelled includes following energy vectors: {energy_vector_string[:-2]}",
    )


def add_economic_parameters(economic_parameters):
    """
    Update economic parameters with annuity factor and CRF

    Parameters
    ----------

    economic_parameters: dict
        Economic parameters of the simulation

    Returns
    -------

    Updated economic parameters

    Notes
    -----
    Function tested with test_add_economic_parameters()
    """

    economic_parameters.update(
        {
            ANNUITY_FACTOR: {
                VALUE: C2.annuity_factor(
                    economic_parameters[PROJECT_DURATION][VALUE],
                    economic_parameters[DISCOUNTFACTOR][VALUE],
                ),
                UNIT: "?",
            }
        }
    )
    # Calculate crf
    economic_parameters.update(
        {
            CRF: {
                VALUE: C2.crf(
                    economic_parameters[PROJECT_DURATION][VALUE],
                    economic_parameters[DISCOUNTFACTOR][VALUE],
                ),
                UNIT: "?",
            }
        }
    )


def process_all_assets(dict_values):
    """defines dict_values['energyBusses'] for later reference

    :param dict_values:
    :return:
    """
    # Define all busses based on the in- and outflow directions of the assets in the input data
    add_assets_to_asset_dict_of_connected_busses(dict_values)
    # Define all excess sinks for each energy bus
    auto_sinks = define_excess_sinks(dict_values)

    # Needed for E3.total_demand_each_sector(), but location is not perfect as it is more about the model then the settings.
    # Decided against implementing a new major 1st level category in json to avoid an excessive datatree.
    dict_values[SIMULATION_SETTINGS].update({EXCESS + AUTO_SINK: auto_sinks})

    # process all energyAssets:
    # Attention! Order of asset_groups important. for energyProviders/energyConversion sinks and sources
    # might be defined that have to be processed in energyProduction/energyConsumption

    # The values of the keys are functions!
    asset_group_list = {
        ENERGY_PROVIDERS: energyProviders,
        ENERGY_CONVERSION: energyConversion,
        ENERGY_STORAGE: energyStorage,
        ENERGY_PRODUCTION: energyProduction,
        ENERGY_CONSUMPTION: energyConsumption,
    }

    for asset_group, asset_function in asset_group_list.items():
        logging.info("Pre-processing all assets in asset group %s.", asset_group)
        # call asset function connected to current asset group (see asset_group_list)
        asset_function(dict_values, asset_group)

        logging.debug(
            "Finished pre-processing all assets in asset group %s.", asset_group
        )

    logging.info("Processed cost data and added economic values.")


def define_excess_sinks(dict_values):
    r"""
    Define energy excess sinks for each bus

    Parameters
    ----------
    dict_values: dict
        All simulation parameters

    Returns
    -------
    Updates dict_values
    """
    auto_sinks = []
    for bus in dict_values[ENERGY_BUSSES]:
        excess_sink_name = bus + EXCESS
        energy_vector = dict_values[ENERGY_BUSSES][bus][ENERGY_VECTOR]
        define_sink(
            dict_values=dict_values,
            asset_key=excess_sink_name,
            price={VALUE: 0, UNIT: CURR + "/" + UNIT},
            inflow_direction=bus,
            energy_vector=energy_vector,
        )
        dict_values[ENERGY_BUSSES][bus].update({EXCESS: excess_sink_name})
        auto_sinks.append(excess_sink_name)
        logging.debug(
            f"Created excess sink for energy bus {bus}, connected to {ENERGY_VECTOR} {energy_vector}."
        )
    return auto_sinks


def energyConversion(dict_values, group):
    """Add lifetime capex (incl. replacement costs), calculate annuity (incl. om), and simulation annuity to each asset

    :param dict_values:
    :param group:
    :return:
    """
    #
    for asset in dict_values[group]:
        define_missing_cost_data(dict_values, dict_values[group][asset])
        evaluate_lifetime_costs(
            dict_values[SIMULATION_SETTINGS],
            dict_values[ECONOMIC_DATA],
            dict_values[group][asset],
        )
        # check if maximumCap exists and add it to dict_values
        process_maximum_cap_constraint(
            dict_values=dict_values, group=group, asset=asset
        )

        # in case there is only one parameter provided (input bus and one output bus)
        if (
            FILENAME in dict_values[group][asset][EFFICIENCY]
            and HEADER in dict_values[group][asset][EFFICIENCY]
        ):
            receive_timeseries_from_csv(
                dict_values[SIMULATION_SETTINGS], dict_values[group][asset], EFFICIENCY,
            )
        # in case there is more than one parameter provided (either (A) n input busses and 1 output bus or (B) 1 input bus and n output busses)
        # dictionaries with filenames and headers will be replaced by timeseries, scalars will be mantained
        elif isinstance(dict_values[group][asset][EFFICIENCY][VALUE], list):
            treat_multiple_flows(dict_values[group][asset], dict_values, EFFICIENCY)

            # same distinction of values provided with dictionaries (one input and one output) or list (multiple).
            # They can at turn be scalars, mantained, or timeseries
            logging.debug(
                "Asset %s has multiple input/output busses with a list of efficiencies. Reading list",
                dict_values[group][asset][LABEL],
            )
        else:
            logging.debug(f"Not loading {group} asset {asset} from file")
            compute_timeseries_properties(dict_values[group][asset])


def energyProduction(dict_values, group):
    """

    :param dict_values:
    :param group:
    :return:
    """
    for asset in dict_values[group]:
        define_missing_cost_data(dict_values, dict_values[group][asset])
        evaluate_lifetime_costs(
            dict_values[SIMULATION_SETTINGS],
            dict_values[ECONOMIC_DATA],
            dict_values[group][asset],
        )

        if FILENAME in dict_values[group][asset]:
            if dict_values[group][asset][FILENAME] in ("None", None):
                dict_values[group][asset].update({DISPATCHABILITY: True})
            else:
                receive_timeseries_from_csv(
                    dict_values[SIMULATION_SETTINGS],
                    dict_values[group][asset],
                    "input",
                )
                # If Filename defines the generation timeseries, then we have an asset with a lack of dispatchability
                dict_values[group][asset].update({DISPATCHABILITY: False})
        else:
            logging.debug(
                f"Not loading {group} asset {asset} from a file, timeseries is provided"
            )
            compute_timeseries_properties(dict_values[group][asset])
        # check if maximumCap exists and add it to dict_values
        process_maximum_cap_constraint(dict_values, group, asset)


def energyStorage(dict_values, group):
    """

    :param dict_values:
    :param group:
    :return:
    """
    for asset in dict_values[group]:
        for subasset in [STORAGE_CAPACITY, INPUT_POWER, OUTPUT_POWER]:
            define_missing_cost_data(
                dict_values, dict_values[group][asset][subasset],
            )
            evaluate_lifetime_costs(
                dict_values[SIMULATION_SETTINGS],
                dict_values[ECONOMIC_DATA],
                dict_values[group][asset][subasset],
            )

            # check if parameters are provided as timeseries
            for parameter in [EFFICIENCY, SOC_MIN, SOC_MAX]:
                if parameter in dict_values[group][asset][subasset] and (
                    FILENAME in dict_values[group][asset][subasset][parameter]
                    and HEADER in dict_values[group][asset][subasset][parameter]
                ):
                    receive_timeseries_from_csv(
                        dict_values[SIMULATION_SETTINGS],
                        dict_values[group][asset][subasset],
                        parameter,
                    )
                elif parameter in dict_values[group][asset][subasset] and isinstance(
                    dict_values[group][asset][subasset][parameter][VALUE], list
                ):
                    treat_multiple_flows(
                        dict_values[group][asset][subasset], dict_values, parameter
                    )
            # check if maximumCap exists and add it to dict_values
            process_maximum_cap_constraint(dict_values, group, asset, subasset)


def energyProviders(dict_values, group):
    """

    :param dict_values:
    :param group:
    :return:
    """
    # add sources and sinks depending on items in energy providers as pre-processing
    for asset in dict_values[group]:
        define_auxiliary_assets_of_energy_providers(dict_values, asset)

        # Add lifetime capex (incl. replacement costs), calculate annuity
        # (incl. om), and simulation annuity to each asset
        define_missing_cost_data(dict_values, dict_values[group][asset])
        evaluate_lifetime_costs(
            dict_values[SIMULATION_SETTINGS],
            dict_values[ECONOMIC_DATA],
            dict_values[group][asset],
        )


def energyConsumption(dict_values, group):
    """

    :param dict_values:
    :param group:
    :return:
    """
    for asset in dict_values[group]:
        define_missing_cost_data(dict_values, dict_values[group][asset])
        evaluate_lifetime_costs(
            dict_values[SIMULATION_SETTINGS],
            dict_values[ECONOMIC_DATA],
            dict_values[group][asset],
        )
        if INFLOW_DIRECTION not in dict_values[group][asset]:
            dict_values[group][asset].update(
                {INFLOW_DIRECTION: dict_values[group][asset][ENERGY_VECTOR]}
            )

        if FILENAME in dict_values[group][asset]:
            receive_timeseries_from_csv(
                dict_values[SIMULATION_SETTINGS],
                dict_values[group][asset],
                "input",
                is_demand_profile=True,
            )
        else:
            logging.debug(
                f"Not loading {group} asset {asset} from a file, timeseries is provided"
            )
            compute_timeseries_properties(dict_values[group][asset])


def define_missing_cost_data(dict_values, dict_asset):
    """

    :param dict_values:
    :param dict_asset:
    :return:
    """

    # read timeseries with filename provided for variable costs.
    # if multiple dispatch_price are given for multiple busses, it checks if any v
    # alue is a timeseries
    if DISPATCH_PRICE in dict_asset:
        if isinstance(dict_asset[DISPATCH_PRICE][VALUE], dict):
            receive_timeseries_from_csv(
                dict_values[SIMULATION_SETTINGS], dict_asset, DISPATCH_PRICE,
            )
        elif isinstance(dict_asset[DISPATCH_PRICE][VALUE], list):
            treat_multiple_flows(dict_asset, dict_values, DISPATCH_PRICE)

    economic_data = dict_values[ECONOMIC_DATA]

    basic_costs = {
        OPTIMIZE_CAP: {VALUE: False, UNIT: TYPE_BOOL},
        UNIT: "?",
        INSTALLED_CAP: {VALUE: 0.0, UNIT: UNIT},
        DEVELOPMENT_COSTS: {VALUE: 0, UNIT: CURR},
        SPECIFIC_COSTS: {VALUE: 0, UNIT: CURR + "/" + UNIT},
        SPECIFIC_COSTS_OM: {VALUE: 0, UNIT: CURR + "/" + UNIT_YEAR},
        DISPATCH_PRICE: {VALUE: 0, UNIT: CURR + "/" + UNIT + "/" + UNIT_YEAR},
        LIFETIME: {VALUE: economic_data[PROJECT_DURATION][VALUE], UNIT: UNIT_YEAR,},
        AGE_INSTALLED: {VALUE: 0, UNIT: UNIT_YEAR,},
    }

    # checks that an asset has all cost parameters needed for evaluation.
    # Adds standard values.
    str = ""
    for cost in basic_costs:
        if cost not in dict_asset:
            dict_asset.update({cost: basic_costs[cost]})
            str = str + " " + cost

    if len(str) > 1:
        logging.debug("Added basic costs to asset %s: %s", dict_asset[LABEL], str)


def add_assets_to_asset_dict_of_connected_busses(dict_values):
    """
    This function adds the assets of the different asset groups to the asset dict of ENERGY_BUSSES.
    The asset groups are: ENERGY_CONVERSION, ENERGY_PRODUCTION, ENERGY_CONSUMPTION, ENERGY_PROVIDERS, ENERGY_STORAGE

    Parameters
    ----------
    dict_values: dict
        Dictionary with all simulation information

    Returns
    -------
    Extends dict_values[ENERGY_BUSSES] by an asset_dict that includes all connected assets.

    Notes
    -----
    Tested with:
    - C0.test_add_assets_to_asset_dict_of_connected_busses()
    """
    for group in [
        ENERGY_CONVERSION,
        ENERGY_PRODUCTION,
        ENERGY_CONSUMPTION,
        ENERGY_PROVIDERS,
        ENERGY_STORAGE,
    ]:
        for asset in dict_values[group]:
            add_asset_to_asset_dict_for_each_flow_direction(
                dict_values, dict_values[group][asset], asset
            )


def add_asset_to_asset_dict_for_each_flow_direction(dict_values, dict_asset, asset_key):
    """
    Add asset to the asset dict of the busses connected to the INPUT_DIRECTION and OUTPUT_DIRECTION of the asset.

    Parameters
    ----------
    dict_values: dict
        All simulation information

    dict_asset: dict
        All information of the current asset

    asset_key: str
        Key that calls the dict_asset from dict_values[asset_group][key]

    Returns
    -------
    Updated dict_values, with dict_values[ENERGY_BUSSES] now including asset dictionaries for each asset connected to a bus.

    Notes
    -----
    Tested with:
    - C0.test_add_asset_to_asset_dict_for_each_flow_direction()
    """

    # The asset needs to be added both to the inflow as well as the outflow bus:
    for direction in [INFLOW_DIRECTION, OUTFLOW_DIRECTION]:
        # Check if the asset has an INFLOW_DIRECTION or OUTFLOW_DIRECTION
        if direction in dict_asset:
            bus = dict_asset[direction]
            # Check if a list ob busses is in INFLOW_DIRECTION or OUTFLOW_DIRECTION
            if isinstance(bus, list):
                # If true: All busses need to be checked
                bus_list = []
                # Checking each bus of the list
                for subbus in bus:
                    # Append bus name to bus_list
                    bus_list.append(subbus)
                    # Check if bus of the direction is already contained in energyBusses
                    add_asset_to_asset_dict_of_bus(
                        bus=subbus,
                        dict_values=dict_values,
                        asset_key=asset_key,
                        asset_label=dict_asset[LABEL],
                    )

            # If false: Only one bus
            else:
                # Check if bus of the direction is already contained in energyBusses
                add_asset_to_asset_dict_of_bus(
                    bus=bus,
                    dict_values=dict_values,
                    asset_key=asset_key,
                    asset_label=dict_asset[LABEL],
                )


def add_asset_to_asset_dict_of_bus(bus, dict_values, asset_key, asset_label):
    """
    Adds asset key and label to a bus defined by `energyBusses.csv`
    Sends an error message if the bus was not included in `energyBusses.csv`

    Parameters
    ----------
    dict_values: dict
        Dict of all simulation parameters

    bus: str
        A bus label

    asset_key: str
        Key with with an dict_asset would be called from dict_values[groups][key]

    asset_label: str
        Label of the asset

    Returns
    -------
    Updated dict_values[ENERGY_BUSSES] by adding an asset to the busses` ASSET DICT

    EnergyBusses now has following keys: LABEL, ENERGY_VECTOR, ASSET_DICT

    Notes
    -----
    Tested with:
    - C0.test_add_asset_to_asset_dict_of_bus()
    - C0.test_add_asset_to_asset_dict_of_bus_ValueError()
    """
    # If bus not defined in `energyBusses.csv` display error message
    if bus not in dict_values[ENERGY_BUSSES]:
        bus_string = ", ".join(map(str, dict_values[ENERGY_BUSSES].keys()))
        msg = (
            f"Asset {asset_key} has an inflow or outflow direction of {bus}. "
            f"This bus is not defined in `energyBusses.csv`: {bus_string}. "
            f"You may either have a typo in one of the files or need to add a bus to `energyBusses.csv`."
        )
        raise ValueError(msg)

    # If the EnergyBus has no ASSET_DICT to which the asset can be added later, add it
    if ASSET_DICT not in dict_values[ENERGY_BUSSES][bus]:
        dict_values[ENERGY_BUSSES][bus].update({ASSET_DICT: {}})

    # Asset should added to respective bus
    dict_values[ENERGY_BUSSES][bus][ASSET_DICT].update({asset_key: asset_label})
    logging.debug(f"Added asset {asset_label} to bus {bus}")


def define_auxiliary_assets_of_energy_providers(dict_values, dso):
    r"""
    Defines all sinks and sources that need to be added to model the transformer using assets of energyConsumption, energyProduction and energyConversion.

    Parameters
    ----------
    dict_values
    dso

    Returns
    -------
    Updated dict_values

    Notes
    -----
    This function is tested with following pytests:
    - C0.test_define_auxiliary_assets_of_energy_providers()
    - C0.test_determine_months_in_a_peak_demand_pricing_period_not_valid()
    - C0.test_determine_months_in_a_peak_demand_pricing_period_valid()
    - C0.test_define_availability_of_peak_demand_pricing_assets_yearly()
    - C0.test_define_availability_of_peak_demand_pricing_assets_monthly()
    - C0.test_define_availability_of_peak_demand_pricing_assets_quarterly()
    - C0.test_add_a_transformer_for_each_peak_demand_pricing_period_1_period()
    - C0.test_add_a_transformer_for_each_peak_demand_pricing_period_2_periods()
    - C0.test_define_transformer_for_peak_demand_pricing()
    - C0.test_define_source()
    - C0.test_define_source_exception_unknown_bus()
    - C0.test_define_source_timeseries_not_None()
    - C0.test_define_source_price_not_None_but_with_scalar_value()
    - C0.test_define_sink() -> incomplete
    - C0.test_change_sign_of_feedin_tariff_positive_value()
    - C0.test_change_sign_of_feedin_tariff_negative_value()
    - C0.test_change_sign_of_feedin_tariff_zero()
    """

    number_of_pricing_periods = dict_values[ENERGY_PROVIDERS][dso][
        PEAK_DEMAND_PRICING_PERIOD
    ][VALUE]

    months_in_a_period = determine_months_in_a_peak_demand_pricing_period(
        number_of_pricing_periods,
        dict_values[SIMULATION_SETTINGS][EVALUATED_PERIOD][VALUE],
    )

    dict_availability_timeseries = define_availability_of_peak_demand_pricing_assets(
        dict_values, number_of_pricing_periods, months_in_a_period,
    )

    list_of_dso_energyConversion_assets = add_a_transformer_for_each_peak_demand_pricing_period(
        dict_values, dict_values[ENERGY_PROVIDERS][dso], dict_availability_timeseries,
    )

    define_source(
        dict_values=dict_values,
        asset_key=dso + DSO_CONSUMPTION,
        outflow_direction=dict_values[ENERGY_PROVIDERS][dso][OUTFLOW_DIRECTION]
        + DSO_PEAK_DEMAND_SUFFIX,
        price=dict_values[ENERGY_PROVIDERS][dso][ENERGY_PRICE],
        energy_vector=dict_values[ENERGY_PROVIDERS][dso][ENERGY_VECTOR],
        emission_factor=dict_values[ENERGY_PROVIDERS][dso][EMISSION_FACTOR],
    )

    dict_feedin = change_sign_of_feedin_tariff(
        dict_values[ENERGY_PROVIDERS][dso][FEEDIN_TARIFF], dso
    )

    # define feed-in sink of the DSO
    define_sink(
        dict_values=dict_values,
        asset_key=dso + DSO_FEEDIN + AUTO_SINK,
        price=dict_feedin,
        inflow_direction=dict_values[ENERGY_PROVIDERS][dso][INFLOW_DIRECTION],
        specific_costs={VALUE: 0, UNIT: CURR + "/" + UNIT},
        energy_vector=dict_values[ENERGY_PROVIDERS][dso][ENERGY_VECTOR],
    )

    dict_values[ENERGY_PROVIDERS][dso].update(
        {
            CONNECTED_CONSUMPTION_SOURCE: dso + DSO_CONSUMPTION + AUTO_SOURCE,
            CONNECTED_PEAK_DEMAND_PRICING_TRANSFORMERS: list_of_dso_energyConversion_assets,
            CONNECTED_FEEDIN_SINK: dso + DSO_FEEDIN + AUTO_SINK,
        }
    )


def change_sign_of_feedin_tariff(dict_feedin_tariff, dso):
    r"""
    Change the sign of the feed-in tariff.
    Additionally, prints a logging.warning in case of the feed-in tariff is entered as
    negative value in 'energyProviders.csv'.

    Parameters
    ----------
    dict_feedin_tariff: dict
        Dict of feedin tariff with Unit-value pair

    dso: str
        Name of the energy provider

    Returns
    -------
    dict_feedin_tariff: dict
        Dict of feedin tariff, to be used as input to C0.define_sink

    Notes
    -----
    Tested with:
    - C0.test_change_sign_of_feedin_tariff_positive_value()
    - C0.test_change_sign_of_feedin_tariff_negative_value()
    - C0.test_change_sign_of_feedin_tariff_zero()
    """
    if dict_feedin_tariff[VALUE] > 0:
        # Add a debug message in case the feed-in is interpreted as revenue-inducing.
        logging.debug(
            f"The {FEEDIN_TARIFF} of {dso} is positive, which means that feeding into the grid results in a revenue stream."
        )
    elif dict_feedin_tariff[VALUE] == 0:
        # Add a warning msg in case the feedin induces expenses rather then revenue
        logging.info(
            f"The {FEEDIN_TARIFF} of {dso} is 0, which means that there is no renumeration for feed-in to the grid. Potentially, this can lead to random dispatch into feed-in and excess sinks."
        )
    elif dict_feedin_tariff[VALUE] < 0:
        # Add a warning msg in case the feedin induces expenses rather then revenue
        logging.warning(
            f"The {FEEDIN_TARIFF} of {dso} is negative, which means that payments are necessary to be allowed to feed-into the grid. If you intended a revenue stream, set the feedin tariff to a positive value."
        )
    else:
        pass

    dict_feedin_tariff = {
        VALUE: -dict_feedin_tariff[VALUE],
        UNIT: dict_feedin_tariff[UNIT],
    }
    return dict_feedin_tariff


def define_availability_of_peak_demand_pricing_assets(
    dict_values, number_of_pricing_periods, months_in_a_period
):
    r"""
    Determined the availability timeseries for the later to be defined dso assets for taking into account the peak demand pricing periods.

    Parameters
    ----------
    dict_values: dict
        All simulation inputs
    number_of_pricing_periods: int
        Number of pricing periods in a year. Valid: 1,2,3,4,6,12
    months_in_a_period: int
        Duration of a period

    Returns
    -------
    dict_availability_timeseries: dict
        Dict with all availability timeseries for each period

    """
    dict_availability_timeseries = {}
    for period in range(1, number_of_pricing_periods + 1):
        availability_in_period = pd.Series(
            0, index=dict_values[SIMULATION_SETTINGS][TIME_INDEX]
        )
        time_period = pd.date_range(
            # Period start
            start=dict_values[SIMULATION_SETTINGS][START_DATE]
            + pd.DateOffset(months=(period - 1) * months_in_a_period),
            # Period end, with months_in_a_period durartion
            end=dict_values[SIMULATION_SETTINGS][START_DATE]
            + pd.DateOffset(months=(period) * months_in_a_period, hours=-1),
            freq=str(dict_values[SIMULATION_SETTINGS][TIMESTEP][VALUE]) + UNIT_MINUTE,
        )

        availability_in_period = availability_in_period.add(
            pd.Series(1, index=time_period), fill_value=0
        ).loc[dict_values[SIMULATION_SETTINGS][TIME_INDEX]]
        print(f"lenght of availability_in_period: {len(availability_in_period)}")
        dict_availability_timeseries.update({period: availability_in_period})

    return dict_availability_timeseries


def add_a_transformer_for_each_peak_demand_pricing_period(
    dict_values, dict_dso, dict_availability_timeseries
):
    r"""
    Adds transformers that are supposed to model the peak_demand_pricing periods for each period.
    This is changed compared to MVS 0.3.0, as there a peak demand pricing period was added by adding a source, not a transformer.

    Parameters
    ----------
    dict_values: dict
        dict with all simulation parameters

    dict_dso: dict
        dict with all info on the specific dso at hand

    dict_availability_timeseries: dict
        dict with all availability timeseries for each period

    Returns
    -------
    list_of_dso_energyConversion_assets: list
        List of names of newly added energy conversion assets,

    Updated dict_values with a transformer for each peak demand pricing period

    Notes
    -----

    Tested by:
    - C0.test_add_a_transformer_for_each_peak_demand_pricing_period_1_period
    - C0.test_add_a_transformer_for_each_peak_demand_pricing_period_2_periods
    """

    list_of_dso_energyConversion_assets = []
    for key in dict_availability_timeseries.keys():
        if len(dict_availability_timeseries.keys()) == 1:
            transformer_name = (
                dict_dso[LABEL] + DSO_CONSUMPTION + DSO_PEAK_DEMAND_PERIOD
            )
        else:
            transformer_name = (
                dict_dso[LABEL]
                + DSO_CONSUMPTION
                + DSO_PEAK_DEMAND_PERIOD
                + "_"
                + str(key)
            )

        define_transformer_for_peak_demand_pricing(
            dict_values=dict_values,
            dict_dso=dict_dso,
            transformer_name=transformer_name,
            timeseries_availability=dict_availability_timeseries[key],
        )

        list_of_dso_energyConversion_assets.append(transformer_name)

    logging.debug(
        f"The peak demand pricing price of {dict_dso[PEAK_DEMAND_PRICING][VALUE]} {dict_values[ECONOMIC_DATA][CURR]} "
        f"is set as specific_costs_om of the peak demand pricing transformers of the DSO."
    )
    return list_of_dso_energyConversion_assets


def determine_months_in_a_peak_demand_pricing_period(
    number_of_pricing_periods, simulation_period_lenght
):
    r"""
    Check if the number of peak demand pricing periods is valid.
    Warns user that in case the number of periods exceeds 1 but the simulation time is not a year,
    there could be an unexpected number of timeseries considered.
    Raises error if number of peak demand pricing periods is not valid.

    Parameters
    ----------
    number_of_pricing_periods: int
        Defined in csv, is number of pricing periods within a year
    simulation_period_lenght: int
        Defined in csv, is number of days of the simulation

    Returns
    -------
    months_in_a_period: float
        Number of months that make a period, will be used to determine availability of dso assets
    """

    # check number of pricing periods - if >1 the simulation has to cover a whole year!
    if number_of_pricing_periods > 1:
        if simulation_period_lenght != 365:
            logging.debug(
                f"\n Message for dev: Following warning is not technically true, "
                f"as the evaluation period has to approximately be "
                f"larger than 365/peak demand pricing periods (see #331)."
            )
            logging.warning(
                f"You have chosen a number of peak demand pricing periods > 1."
                f"Please be advised that if you are not simulating for a year (365d)"
                f"an possibly unexpected number of periods will be considered."
            )

    if number_of_pricing_periods not in [1, 2, 3, 4, 6, 12]:
        raise InvalidPeakDemandPricingPeriodsError(
            f"You have defined a number of peak demand pricing periods of {number_of_pricing_periods}. "
            f"Acceptable values are, however: 1 (yearly), 2 (half-yearly), 3 (each trimester), 4 (quarterly), 6 (every two months) and 1 (monthly)."
        )

    # defines the number of months that one period constists of.
    months_in_a_period = 12 / number_of_pricing_periods
    logging.info(
        "Peak demand pricing is taking place %s times per year, ie. every %s "
        "months.",
        number_of_pricing_periods,
        months_in_a_period,
    )
    return months_in_a_period


def define_transformer_for_peak_demand_pricing(
    dict_values, dict_dso, transformer_name, timeseries_availability
):
    r"""
    Defines a transformer for peak demand pricing in energyConverion

    Parameters
    ----------
    dict_values: dict
        All simulation parameters

    dict_dso: dict
        All values connected to the DSO

    transformer_name: str
        label of the transformer to be added

    timeseries_availability: pd.Series
        Timeseries of transformer availability. Introduced to cover peak demand pricing.

    Returns
    -------
    Updated dict_values with newly added transformer asset in the energyConversion asset group.
    """

    default_dso_transformer = {
        LABEL: transformer_name,
        OPTIMIZE_CAP: {VALUE: True, UNIT: TYPE_BOOL},
        INSTALLED_CAP: {VALUE: 0, UNIT: dict_dso[UNIT]},
        INFLOW_DIRECTION: dict_dso[INFLOW_DIRECTION] + DSO_PEAK_DEMAND_SUFFIX,
        OUTFLOW_DIRECTION: dict_dso[OUTFLOW_DIRECTION],
        AVAILABILITY_DISPATCH: timeseries_availability,
        EFFICIENCY: {VALUE: 1, UNIT: "factor"},
        DEVELOPMENT_COSTS: {VALUE: 0, UNIT: CURR},
        SPECIFIC_COSTS: {VALUE: 0, UNIT: CURR + "/" + dict_dso[UNIT],},
        SPECIFIC_COSTS_OM: {
            VALUE: dict_dso[PEAK_DEMAND_PRICING][VALUE],
            UNIT: CURR + "/" + dict_dso[UNIT] + "/" + UNIT_YEAR,
        },
        DISPATCH_PRICE: {VALUE: 0, UNIT: CURR + "/" + dict_dso[UNIT] + "/" + UNIT_HOUR},
        OEMOF_ASSET_TYPE: OEMOF_TRANSFORMER,
        ENERGY_VECTOR: dict_dso[ENERGY_VECTOR],
        AGE_INSTALLED: {VALUE: 0, UNIT: UNIT_YEAR},
    }

    dict_values[ENERGY_CONVERSION].update({transformer_name: default_dso_transformer})

    logging.debug(
        f"Model for peak demand pricing: Adding transfomer {transformer_name}."
    )


def define_source(
    dict_values,
    asset_key,
    outflow_direction,
    energy_vector,
    emission_factor,
    price=None,
    timeseries=None,
):
    r"""
    Defines a source with default input values. If kwargs are given, the default values are overwritten.

    Parameters
    ----------
    dict_values: dict
        Dictionary to which source should be added, with all simulation parameters

    asset_key: str
        key under which the asset is stored in the asset group

    energy_vector: str
        Energy vector the new asset should belong to

    emission_factor : dict
        Dict with a unit-value pair of the emission factor of the new asset

    price: dict
        Dict with a unit-value pair of the dispatch price of the source.
        The value can also be defined though FILENAME and HEADER, making the value of the price a timeseries.
        Default: None

    timeseries: pd.Dataframe
        Timeseries defining the availability of the source. Currently not used.
        Default: None

    Returns
    -------
    Updates dict_values[ENERGY_BUSSES] if outflow_direction not in it
    Standard source defined as:

    Notes
    -----
    The pytests for this function are not complete. It is started with:
    - C0.test_define_source()
    - C0.test_define_source_exception_unknown_bus()
    - C0.test_define_source_timeseries_not_None()
    - C0.test_define_source_price_not_None_but_with_scalar_value()
    Missing:
    - C0.test_define_source_price_not_None_but_timeseries(), ie. value defined by FILENAME and HEADER
    """
    source_label = asset_key + AUTO_SOURCE
    default_source_dict = {
        OEMOF_ASSET_TYPE: OEMOF_SOURCE,
        LABEL: source_label,
        OUTFLOW_DIRECTION: outflow_direction,
        DISPATCHABILITY: True,
        # OPEX_VAR: {VALUE: price, UNIT: CURR + "/" + UNIT},
        LIFETIME: {
            VALUE: dict_values[ECONOMIC_DATA][PROJECT_DURATION][VALUE],
            UNIT: UNIT_YEAR,
        },
        OPTIMIZE_CAP: {VALUE: True, UNIT: TYPE_BOOL},
        MAXIMUM_CAP: {VALUE: None, UNIT: "?"},
        AGE_INSTALLED: {VALUE: 0, UNIT: UNIT_YEAR,},
        ENERGY_VECTOR: energy_vector,
        EMISSION_FACTOR: emission_factor,
    }

    if outflow_direction not in dict_values[ENERGY_BUSSES]:
        dict_values[ENERGY_BUSSES].update(
            {
                outflow_direction: {
                    LABEL: outflow_direction,
                    ENERGY_VECTOR: energy_vector,
                    ASSET_DICT: {asset_key: source_label},
                }
            }
        )

    if price is not None:
        if FILENAME in price and HEADER in price:
            price.update(
                {
                    VALUE: get_timeseries_multiple_flows(
                        dict_values[SIMULATION_SETTINGS],
                        default_source_dict,
                        price[FILENAME],
                        price[HEADER],
                    )
                }
            )
        determine_dispatch_price(dict_values, price, default_source_dict)

    if timeseries is not None:
        # This part is currently not used.
        default_source_dict.update({DISPATCHABILITY: False})
        logging.debug(
            f"{default_source_dict[LABEL]} can provide a total generation of {sum(timeseries.values)}"
        )
        default_source_dict[OPTIMIZE_CAP].update({VALUE: True})
        default_source_dict.update(
            {
                TIMESERIES_PEAK: {VALUE: max(timeseries), UNIT: "kW"},
                TIMESERIES_NORMALIZED: timeseries / max(timeseries),
            }
        )
        if DISPATCH_PRICE in default_source_dict and max(timeseries) != 0:
            default_source_dict[DISPATCH_PRICE].update(
                {VALUE: default_source_dict[DISPATCH_PRICE][VALUE] / max(timeseries)}
            )

    dict_values[ENERGY_PRODUCTION].update({asset_key: default_source_dict})

    logging.info(
        f"Asset {default_source_dict[LABEL]} was added to the energyProduction assets."
    )

    apply_function_to_single_or_list(
        function=add_asset_to_asset_dict_of_bus,
        parameter=outflow_direction,
        dict_values=dict_values,
        asset_key=asset_key,
        asset_label=default_source_dict[LABEL],
    )


def determine_dispatch_price(dict_values, price, source):
    """
    This function needs to be re-evaluated.

    Parameters
    ----------
    dict_values
    price
    source

    Returns
    -------

    """
    # check if multiple busses are provided
    # for each bus, read time series for dispatch_price if a file name has been
    # provided in energy price
    if isinstance(price[VALUE], list):
        source.update({DISPATCH_PRICE: {VALUE: [], UNIT: price[UNIT]}})
        values_info = []
        for element in price[VALUE]:
            if isinstance(element, dict):
                source[DISPATCH_PRICE][VALUE].append(
                    get_timeseries_multiple_flows(
                        dict_values[SIMULATION_SETTINGS],
                        source,
                        element[FILENAME],
                        element[HEADER],
                    )
                )
                values_info.append(element)
            else:
                source[DISPATCH_PRICE][VALUE].append(element)
        if len(values_info) > 0:
            source[DISPATCH_PRICE]["values_info"] = values_info

    elif isinstance(price[VALUE], dict):
        source.update(
            {
                DISPATCH_PRICE: {
                    VALUE: {
                        FILENAME: price[VALUE][FILENAME],
                        HEADER: price[VALUE][HEADER],
                    },
                    UNIT: price[UNIT],
                }
            }
        )
        receive_timeseries_from_csv(
            dict_values[SIMULATION_SETTINGS], source, DISPATCH_PRICE
        )
    else:
        source.update({DISPATCH_PRICE: {VALUE: price[VALUE], UNIT: price[UNIT]}})

    if type(source[DISPATCH_PRICE][VALUE]) == pd.Series:
        logging.debug(
            f"{source[LABEL]} was created, with a price defined as a timeseries (average: {source[DISPATCH_PRICE][VALUE].mean()})."
        )
    else:
        logging.debug(
            f"{source[LABEL]} was created, with a price of {source[DISPATCH_PRICE][VALUE]}."
        )


def define_sink(
    dict_values, asset_key, price, inflow_direction, energy_vector, **kwargs
):
    r"""
    This automatically defines a sink for an oemof-sink object. The sinks are added to the energyConsumption assets.

    Parameters
    ----------
    dict_values: dict
        All information of the simulation

    asset_key: str
        label of the asset to be generated

    price: float
        Price of dispatch of the asset

    inflow_direction: str
        Direction from which energy is provided to the sink

    kwargs: Misc
        Common parameters:
        -

    Returns
    -------
    Updates dict_values[ENERGY_BUSSES] if outflow_direction not in it
    Updates dict_values[ENERGY_CONSUMPTION] with a new sink

    Notes
    -----
    Examples:
    - Used to define excess sinks for all energyBusses
    - Used to define feed-in sink for each DSO

    The pytests for this function are not complete. It is started with:
    - C0.test_define_sink() and only the assertion messages are missing
    """
    sink_label = asset_key + AUTO_SINK
    # create a dictionary for the sink
    sink = {
        OEMOF_ASSET_TYPE: OEMOF_SINK,
        LABEL: sink_label,
        INFLOW_DIRECTION: inflow_direction,
        # OPEX_VAR: {VALUE: price, UNIT: CURR + "/" + UNIT},
        LIFETIME: {
            VALUE: dict_values[ECONOMIC_DATA][PROJECT_DURATION][VALUE],
            UNIT: UNIT_YEAR,
        },
        AGE_INSTALLED: {VALUE: 0, UNIT: UNIT_YEAR,},
        ENERGY_VECTOR: energy_vector,
        OPTIMIZE_CAP: {VALUE: True, UNIT: TYPE_BOOL},
    }

    if inflow_direction not in dict_values[ENERGY_BUSSES]:
        dict_values[ENERGY_BUSSES].update(
            {
                inflow_direction: {
                    LABEL: inflow_direction,
                    ENERGY_VECTOR: energy_vector,
                    ASSET_DICT: {asset_key: sink_label},
                }
            }
        )

    if energy_vector is None:
        raise ValueError(
            f"The {ENERGY_VECTOR} of the automatically defined sink {asset_key + AUTO_SINK} is invalid: {energy_vector}."
        )

    # check if multiple busses are provided
    # for each bus, read time series for dispatch_price if a file name has been provided in feedin tariff
    if isinstance(price[VALUE], list):
        sink.update({DISPATCH_PRICE: {VALUE: [], UNIT: price[UNIT]}})
        values_info = []
        for element in price[VALUE]:
            if isinstance(element, dict):
                timeseries = get_timeseries_multiple_flows(
                    dict_values[SIMULATION_SETTINGS],
                    sink,
                    element[FILENAME],
                    element[HEADER],
                )
                if asset_key[-6:] == "feedin":
                    sink[DISPATCH_PRICE][VALUE].append([-i for i in timeseries])
                else:
                    sink[DISPATCH_PRICE][VALUE].append(timeseries)
            else:
                sink[DISPATCH_PRICE][VALUE].append(element)
        if len(values_info) > 0:
            sink[DISPATCH_PRICE]["values_info"] = values_info

    elif isinstance(price[VALUE], dict):
        sink.update(
            {
                DISPATCH_PRICE: {
                    VALUE: {
                        FILENAME: price[VALUE][FILENAME],
                        HEADER: price[VALUE][HEADER],
                    },
                    UNIT: price[UNIT],
                }
            }
        )
        receive_timeseries_from_csv(
            dict_values[SIMULATION_SETTINGS], sink, DISPATCH_PRICE
        )
        if (
            asset_key[-6:] == "feedin"
        ):  # change into negative value if this is a feedin sink
            sink[DISPATCH_PRICE].update(
                {VALUE: [-i for i in sink[DISPATCH_PRICE][VALUE]]}
            )
    else:
        if asset_key[-6:] == "feedin":
            value = -price[VALUE]
        else:
            value = price[VALUE]
        sink.update({DISPATCH_PRICE: {VALUE: value, UNIT: price[UNIT]}})

    for item in [SPECIFIC_COSTS, SPECIFIC_COSTS_OM]:
        if item in kwargs:
            sink.update(
                {item: kwargs[item],}
            )

    # update dictionary
    dict_values[ENERGY_CONSUMPTION].update({asset_key: sink})

    # If multiple input busses exist
    apply_function_to_single_or_list(
        function=add_asset_to_asset_dict_of_bus,
        parameter=inflow_direction,
        dict_values=dict_values,
        asset_key=asset_key,
        asset_label=sink[LABEL],
    )


def apply_function_to_single_or_list(function, parameter, **kwargs):
    """
    Applies function to a paramter or to a list of parameters and returns resut

    Parameters
    ----------
    function: func
        Function to be applied to a parameter

    parameter: float/str/boolean or list
        Parameter, either float/str/boolean or list to be evaluated
    kwargs
        Miscellaneous arguments for function to be called

    Returns
    -------
    Processed parameter (single) or list of processed para<meters
    """
    if isinstance(parameter, list):
        parameter_processed = []
        for parameter_item in parameter:
            parameter_processed.append(function(parameter_item, **kwargs))
    else:
        parameter_processed = function(parameter, **kwargs)

    return parameter_processed


def evaluate_lifetime_costs(settings, economic_data, dict_asset):
    r"""
    Evaluates specific costs of an asset over the project lifetime. This includes:
    - LIFETIME_PRICE_DISPATCH (C2.determine_lifetime_price_dispatch)
    - LIFETIME_SPECIFIC_COST
    - LIFETIME_SPECIFIC_COST_OM
    - ANNUITY_SPECIFIC_INVESTMENT_AND_OM
    - SIMULATION_ANNUITY

    The DEVELOPMENT_COSTS are not processed here, as they are not necessary for the optimization.

    Parameters
    ----------
    settings: dict
        dict of simulation settings, including:
        - EVALUATED_PERIOD

    economic_data: dict
        dict of economic data of the simulation, including
        - project duration (PROJECT_DURATION)
        - discount factor (DISCOUNTFACTOR)
        - tax (TAX)
        - CRF
        - ANNUITY_FACTOR

    dict_asset: dict
        dict of all asset parameters, including
        - SPECIFIC_COSTS
        - SPECIFIC_COSTS_OM
        - LIFETIME

    Returns
    -------
    Updates asset dict with
    - LIFETIME_PRICE_DISPATCH (C2.determine_lifetime_price_dispatch)
    - LIFETIME_SPECIFIC_COST
    - LIFETIME_SPECIFIC_COST_OM
    - ANNUITY_SPECIFIC_INVESTMENT_AND_OM
    - SIMULATION_ANNUITY
    - SPECIFIC_REPLACEMENT_COSTS_INSTALLED
    - SPECIFIC_REPLACEMENT_COSTS_OPTIMIZED
    Notes
    -----

    Tested with:
    - test_evaluate_lifetime_costs_adds_all_parameters()
    - Test_Economic_KPI.test_benchmark_Economic_KPI_C2_E2()

    """

    C2.determine_lifetime_price_dispatch(dict_asset, economic_data)

    (
        specific_capex,
        specific_replacement_costs_optimized,
        specific_replacement_costs_already_installed,
    ) = C2.capex_from_investment(
        investment_t0=dict_asset[SPECIFIC_COSTS][VALUE],
        lifetime=dict_asset[LIFETIME][VALUE],
        project_life=economic_data[PROJECT_DURATION][VALUE],
        discount_factor=economic_data[DISCOUNTFACTOR][VALUE],
        tax=economic_data[TAX][VALUE],
        age_of_asset=dict_asset[AGE_INSTALLED][VALUE],
        asset_label=dict_asset[LABEL],
    )

    dict_asset.update(
        {
            LIFETIME_SPECIFIC_COST: {
                VALUE: specific_capex,
                UNIT: dict_asset[SPECIFIC_COSTS][UNIT],
            }
        }
    )

    dict_asset.update(
        {
            SPECIFIC_REPLACEMENT_COSTS_OPTIMIZED: {
                VALUE: specific_replacement_costs_optimized,
                UNIT: dict_asset[SPECIFIC_COSTS][UNIT],
            }
        }
    )

    dict_asset.update(
        {
            SPECIFIC_REPLACEMENT_COSTS_INSTALLED: {
                VALUE: specific_replacement_costs_already_installed,
                UNIT: dict_asset[SPECIFIC_COSTS][UNIT],
            }
        }
    )

    # Annuities of components including opex AND capex #
    dict_asset.update(
        {
            ANNUITY_SPECIFIC_INVESTMENT_AND_OM: {
                VALUE: C2.annuity(
                    dict_asset[LIFETIME_SPECIFIC_COST][VALUE],
                    economic_data[CRF][VALUE],
                )
                + dict_asset[SPECIFIC_COSTS_OM][VALUE],  # changes from dispatch_price
                UNIT: dict_asset[LIFETIME_SPECIFIC_COST][UNIT] + "/" + UNIT_YEAR,
            }
        }
    )

    dict_asset.update(
        {
            LIFETIME_SPECIFIC_COST_OM: {
                VALUE: dict_asset[SPECIFIC_COSTS_OM][VALUE]
                * economic_data[ANNUITY_FACTOR][VALUE],
                UNIT: dict_asset[SPECIFIC_COSTS_OM][UNIT][:-2],
            }
        }
    )

    dict_asset.update(
        {
            SIMULATION_ANNUITY: {
                VALUE: C2.simulation_annuity(
                    dict_asset[ANNUITY_SPECIFIC_INVESTMENT_AND_OM][VALUE],
                    settings[EVALUATED_PERIOD][VALUE],
                ),
                UNIT: CURR + "/" + UNIT + "/" + EVALUATED_PERIOD,
            }
        }
    )


# read timeseries. 2 cases are considered: Input type is related to demand or generation profiles,
# so additional values like peak, total or average must be calculated. Any other type does not need this additional info.
def receive_timeseries_from_csv(
    settings, dict_asset, input_type, is_demand_profile=False
):
    """

    :param settings:
    :param dict_asset:
    :param type:
    :return:
    """
    if input_type == "input" and "input" in dict_asset:
        file_name = dict_asset[input_type][FILENAME]
        header = dict_asset[input_type][HEADER]
        unit = dict_asset[input_type][UNIT]
    elif FILENAME in dict_asset:
        # todo this input/file_name thing is a workaround and has to be improved in the future
        # if only filename is given here, then only one column can be in the csv
        file_name = dict_asset[FILENAME]
        unit = dict_asset[UNIT] + "/" + UNIT_HOUR
    else:
        file_name = dict_asset[input_type][FILENAME]
        header = dict_asset[input_type][HEADER]
        unit = dict_asset[input_type][UNIT]

    file_path = os.path.join(settings[PATH_INPUT_FOLDER], TIME_SERIES, file_name)
    C1.lookup_file(file_path, dict_asset[LABEL])

    data_set = pd.read_csv(file_path, sep=",", keep_default_na=True)

    if FILENAME in dict_asset:
        header = data_set.columns[0]

    if len(data_set.index) == settings[PERIODS]:
        if input_type == "input":
            timeseries = pd.Series(data_set[header].values, index=settings[TIME_INDEX])
            timeseries = replace_nans_in_timeseries_with_0(
                timeseries, dict_asset[LABEL]
            )
            dict_asset.update({TIMESERIES: timeseries})
        else:
            timeseries = pd.Series(data_set[header].values, index=settings[TIME_INDEX])
            timeseries = replace_nans_in_timeseries_with_0(
                timeseries, dict_asset[LABEL] + "(" + input_type + ")"
            )
            dict_asset[input_type][VALUE] = timeseries

        logging.debug("Added timeseries of %s (%s).", dict_asset[LABEL], file_path)
    elif len(data_set.index) >= settings[PERIODS]:
        if input_type == "input":
            dict_asset.update(
                {
                    TIMESERIES: pd.Series(
                        data_set[header][0 : len(settings[TIME_INDEX])].values,
                        index=settings[TIME_INDEX],
                    )
                }
            )
        else:
            dict_asset[input_type][VALUE] = pd.Series(
                data_set[header][0 : len(settings[TIME_INDEX])].values,
                index=settings[TIME_INDEX],
            )

        logging.info(
            "Provided timeseries of %s (%s) longer than evaluated period. "
            "Excess data dropped.",
            dict_asset[LABEL],
            file_path,
        )

    elif len(data_set.index) <= settings[PERIODS]:
        logging.critical(
            "Input error! "
            "Provided timeseries of %s (%s) shorter then evaluated period. "
            "Operation terminated",
            dict_asset[LABEL],
            file_path,
        )
        sys.exit()

    if input_type == "input":
        compute_timeseries_properties(dict_asset)


def replace_nans_in_timeseries_with_0(timeseries, label):
    """

    Replaces nans in the timeseries (if any) with 0

    Parameters

    ----------
    timeseries: pd.Series
        demand or resource timeseries in dict_asset (having nan value(s) if any),
        also of parameters that are not defined as scalars but as timeseries

    label: str
        Contains user-defined information about the timeseries to be printed into the eventual error message

    Returns
    ----------
    timeseries: pd.Series
        timeseries without NaN values

    Notes
    -----
    Function tested with
    - C0.test_replace_nans_in_timeseries_with_0()
    """
    if sum(pd.isna(timeseries)) > 0:
        incidents = sum(pd.isna(timeseries))
        logging.warning(
            f"A number of {incidents} NaN value(s) found in the {TIMESERIES} of {label}. Changing NaN value(s) to 0."
        )
        timeseries = timeseries.fillna(0)
    return timeseries


def compute_timeseries_properties(dict_asset):
    """Compute peak, aggregation, average and normalize timeseries

    Parameters

    ----------
    dict_asset: dict
        dict of all asset parameters, must contain TIMESERIES key

    Returns
    -------
    None
    Add TIMESERIES_PEAK, TIMESERIES_TOTAL, TIMESERIES_AVERAGE and TIMESERIES_NORMALIZED
    to dict_asset

    Notes
    -----
    Function tested with
    - C0.test_compute_timeseries_properties_TIMESERIES_in_dict_asset()
    - C0.test_compute_timeseries_properties_TIMESERIES_not_in_dict_asset()
    """

    if TIMESERIES in dict_asset:
        timeseries = dict_asset[TIMESERIES]
        unit = dict_asset[UNIT]

        dict_asset.update(
            {
                TIMESERIES_PEAK: {VALUE: max(timeseries), UNIT: unit,},
                TIMESERIES_TOTAL: {VALUE: sum(timeseries), UNIT: unit,},
                TIMESERIES_AVERAGE: {
                    VALUE: sum(timeseries) / len(timeseries),
                    UNIT: unit,
                },
            }
        )

        logging.debug("Normalizing timeseries of %s.", dict_asset[LABEL])
        dict_asset.update(
            {TIMESERIES_NORMALIZED: timeseries / dict_asset[TIMESERIES_PEAK][VALUE]}
        )
        # just to be sure!
        if any(dict_asset[TIMESERIES_NORMALIZED].values) > 1:
            logging.error(
                f"{dict_asset[LABEL]} normalized timeseries has values greater than 1."
            )
        if any(dict_asset[TIMESERIES_NORMALIZED].values) < 0:
            logging.error(
                f"{ dict_asset[LABEL]} normalized timeseries has negative values."
            )


def treat_multiple_flows(dict_asset, dict_values, parameter):
    """
    This function consider the case a technical parameter on the json file has a list of values because multiple
    inputs or outputs busses are considered.
    Parameters
    ----------
    dict_values:
    dictionary of current values of the asset
    parameter:
    usually efficiency. Different efficiencies will be given if an asset has multiple inputs or outputs busses,
    so a list must be considered.

    Returns
    -------

    """
    updated_values = []
    values_info = (
        []
    )  # filenames and headers will be stored to allow keeping track of the timeseries generation
    for element in dict_asset[parameter][VALUE]:
        if isinstance(element, dict):
            updated_values.append(
                get_timeseries_multiple_flows(
                    dict_values[SIMULATION_SETTINGS],
                    dict_asset,
                    element[FILENAME],
                    element[HEADER],
                )
            )
            values_info.append(element)
        else:
            updated_values.append(element)
    dict_asset[parameter][VALUE] = updated_values
    if len(values_info) > 0:
        dict_asset[parameter].update({"values_info": values_info})


# reads timeseries specifically when the need comes from a multiple or output busses situation
# returns the timeseries. Does not update any dictionary
def get_timeseries_multiple_flows(settings, dict_asset, file_name, header):
    """

    Parameters
    ----------
    dict_asset:
    dictionary of the asset
    file_name:
    name of the file to read the time series
    header:
    name of the column where the timeseries is provided

    Returns
    -------

    """
    file_path = os.path.join(settings[PATH_INPUT_FOLDER], TIME_SERIES, file_name)
    C1.lookup_file(file_path, dict_asset[LABEL])

    data_set = pd.read_csv(file_path, sep=",")
    if len(data_set.index) == settings[PERIODS]:
        return pd.Series(data_set[header].values, index=settings[TIME_INDEX])
    elif len(data_set.index) >= settings[PERIODS]:
        return pd.Series(
            data_set[header][0 : len(settings[TIME_INDEX])].values,
            index=settings[TIME_INDEX],
        )
    elif len(data_set.index) <= settings[PERIODS]:
        logging.critical(
            "Input error! "
            "Provided timeseries of %s (%s) shorter then evaluated period. "
            "Operation terminated",
            dict_asset[LABEL],
            file_path,
        )
        sys.exit()


def process_maximum_cap_constraint(dict_values, group, asset, subasset=None):
    """
    Checks if maximumCap is in `dict_values` and if not, adds value None.

    Parameters
    ----------
    dict_values: dict
        dictionary of all assets

    group: str
        Group that the asset belongs to (str). Used to acces sub-asset data and for error messages.

    asset: str
        asset name

    subasset: str
        subasset name.
        Default: None.

    Returns
    -------
    Updates the asset dictionary.

    * Unit of MaximumCap is asset unit

    If MaximumCap is changed depends on its value:
    * If MaximumCap not in asset dict: MaximumCap is None
    * If MaximumCap < installed Cap: invalid, MaximumCap is None
    * If MaximumCap == 0: invalid, MaximumCap is None
    * If MaximumCap > installedCap and group != energyProviders: pass
    * If MaximumCap > installedCap and group == energyProviders and filename not in asset_dict: pass
    * If MaximumCap > installedCap and group == energyProviders and filename in asset_dict (non-dispatchable assets): MaximumCap == MaximumCap/peak(timeseries)
    """
    if subasset is None:
        asset_dict = dict_values[group][asset]
    else:
        asset_dict = dict_values[group][asset][subasset]

    # Check if a maximumCap is defined
    if MAXIMUM_CAP not in asset_dict:
        asset_dict.update({MAXIMUM_CAP: {VALUE: None}})
    else:
        if asset_dict[MAXIMUM_CAP][VALUE] is not None:
            # adapt maximumCap of non-dispatchable sources
            if group == ENERGY_PRODUCTION and asset_dict[FILENAME] is not None:
                asset_dict[MAXIMUM_CAP][VALUE] = (
                    asset_dict[MAXIMUM_CAP][VALUE] * asset_dict[TIMESERIES_PEAK][VALUE]
                )
                logging.debug(
                    f"Parameter {MAXIMUM_CAP} of asset '{asset_dict[LABEL]}' was multiplied by the peak value of {TIMESERIES}. This was done as the aimed constraint is to limit the power, not the flow."
                )
            # check if maximumCap is greater that installedCap
            if asset_dict[MAXIMUM_CAP][VALUE] < asset_dict[INSTALLED_CAP][VALUE]:
                message = (
                    f"The stated maximumCap in {group} {asset} is smaller than the "
                    f"installedCap ({asset_dict[MAXIMUM_CAP][VALUE]}/{asset_dict[INSTALLED_CAP][VALUE]}). Please enter a greater maximumCap."
                    "For this simulation, the maximumCap will be "
                    "disregarded and not be used in the simulation"
                )
                warnings.warn(UserWarning(message))
                logging.warning(message)
                asset_dict[MAXIMUM_CAP][VALUE] = None
            # check if maximumCap is 0
            elif asset_dict[MAXIMUM_CAP][VALUE] == 0:
                message = (
                    f"The stated maximumCap of zero in {group} {asset} is invalid."
                    "For this simulation, the maximumCap will be "
                    "disregarded and not be used in the simulation."
                )
                warnings.warn(UserWarning(message))
                logging.warning(message)
                asset_dict[MAXIMUM_CAP][VALUE] = None

    asset_dict[MAXIMUM_CAP].update({UNIT: asset_dict[UNIT]})
