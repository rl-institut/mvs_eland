import pandas as pd
import pytest
import logging
from copy import deepcopy

import multi_vector_simulator.C0_data_processing as C0

from multi_vector_simulator.utils.constants import TYPE_BOOL
from multi_vector_simulator.utils.constants_json_strings import (
    UNIT,
    PROJECT_DATA,
    ENERGY_PROVIDERS,
    ENERGY_STORAGE,
    ENERGY_CONSUMPTION,
    ENERGY_PRODUCTION,
    ENERGY_CONVERSION,
    ENERGY_BUSSES,
    OUTFLOW_DIRECTION,
    TIMESERIES_NORMALIZED,
    INFLOW_DIRECTION,
    PROJECT_DURATION,
    DISCOUNTFACTOR,
    OPTIMIZE_CAP,
    MAXIMUM_CAP,
    INSTALLED_CAP,
    FILENAME,
    PEAK_DEMAND_PRICING,
    AVAILABILITY_DISPATCH,
    OEMOF_ASSET_TYPE,
    INFLOW_DIRECTION,
    OUTFLOW_DIRECTION,
    EFFICIENCY,
    TAX,
    AGE_INSTALLED,
    VALUE,
    LABEL,
    DISPATCH_PRICE,
    SPECIFIC_COSTS_OM,
    DEVELOPMENT_COSTS,
    SPECIFIC_REPLACEMENT_COSTS_INSTALLED,
    SPECIFIC_REPLACEMENT_COSTS_OPTIMIZED,
    SPECIFIC_COSTS,
    LIFETIME,
    SIMULATION_SETTINGS,
    EVALUATED_PERIOD,
    START_DATE,
    END_DATE,
    TIMESTEP,
    TIME_INDEX,
    ANNUITY_FACTOR,
    SIMULATION_ANNUITY,
    LIFETIME_SPECIFIC_COST,
    TIMESERIES_PEAK,
    CRF,
    ANNUITY_SPECIFIC_INVESTMENT_AND_OM,
    LIFETIME_SPECIFIC_COST_OM,
    LIFETIME_PRICE_DISPATCH,
    PERIODS,
    UNIT_MINUTE,
    ENERGY_VECTOR,
    ASSET_DICT,
    LES_ENERGY_VECTOR_S,
    FEEDIN_TARIFF,
    PEAK_DEMAND_PRICING_PERIOD,
    DSO_CONSUMPTION,
    DSO_PEAK_DEMAND_PERIOD,
    ECONOMIC_DATA,
    CURR,
    AUTO_SOURCE,
    DSO_PEAK_DEMAND_SUFFIX,
    ENERGY_PRICE,
    DSO_FEEDIN,
    AUTO_SINK,
    CONNECTED_CONSUMPTION_SOURCE,
    CONNECTED_PEAK_DEMAND_PRICING_TRANSFORMERS,
    CONNECTED_FEEDIN_SINK,
    DISPATCHABILITY,
    OEMOF_SOURCE,
    UNIT_YEAR,
)
from multi_vector_simulator.utils.exceptions import InvalidPeakDemandPricingPeriodsError


def test_add_economic_parameters():
    economic_parameters = {
        PROJECT_DURATION: {VALUE: 20},
        DISCOUNTFACTOR: {VALUE: 0.15},
    }
    C0.add_economic_parameters(economic_parameters)
    # the actual value of the annuity factor should have been checked in C2
    for k in (ANNUITY_FACTOR, CRF):
        assert (
            k in economic_parameters.keys()
        ), f"Function does not add {k} to the economic parameters."


settings = {EVALUATED_PERIOD: {VALUE: 365}}

economic_data = {
    PROJECT_DURATION: {VALUE: 20},
    ANNUITY_FACTOR: {VALUE: 1},
    CRF: {VALUE: 1},
    DISCOUNTFACTOR: {VALUE: 0},
    TAX: {VALUE: 0},
}

dict_asset = {
    SPECIFIC_COSTS_OM: {VALUE: 1, UNIT: "a_unit"},
    CRF: {VALUE: 1},
    SPECIFIC_COSTS: {VALUE: 1, UNIT: "a_unit"},
    DISPATCH_PRICE: {VALUE: 1},
    DEVELOPMENT_COSTS: {VALUE: 1},
    LIFETIME: {VALUE: 20},
    UNIT: "a_unit",
    AGE_INSTALLED: {VALUE: 0},
}


def test_evaluate_lifetime_costs_adds_all_parameters():
    C0.evaluate_lifetime_costs(settings, economic_data, dict_asset)
    for k in (
        LIFETIME_SPECIFIC_COST,
        ANNUITY_SPECIFIC_INVESTMENT_AND_OM,
        LIFETIME_SPECIFIC_COST_OM,
        LIFETIME_PRICE_DISPATCH,
        SIMULATION_ANNUITY,
        SPECIFIC_REPLACEMENT_COSTS_OPTIMIZED,
        SPECIFIC_REPLACEMENT_COSTS_INSTALLED,
    ):
        assert (
            k in dict_asset.keys()
        ), f"Function does not add {k} to the asset dictionary."


start_date = pd.Timestamp("2018-01-01 00:00:00")
dict_test_avilability = {
    SIMULATION_SETTINGS: {
        TIME_INDEX: pd.date_range(
            start=start_date, periods=8760, freq=str(60) + UNIT_MINUTE
        ),
        START_DATE: start_date,
        TIMESTEP: {VALUE: 60},
    }
}


def test_define_availability_of_peak_demand_pricing_assets_yearly():
    dict_availability_timeseries = C0.define_availability_of_peak_demand_pricing_assets(
        dict_test_avilability, 1, 12
    )
    assert (
        len(dict_availability_timeseries) == 1
    ), f"Function does not create a single availability_timeseries for the whole year."
    assert (
        dict_availability_timeseries[1].values.sum() == 8760
    ), f"Availablity of a single dict_availability_timeseries is not ensured for every hour of the year."


def test_define_availability_of_peak_demand_pricing_assets_monthly():
    dict_availability_timeseries = C0.define_availability_of_peak_demand_pricing_assets(
        dict_test_avilability, 12, 1
    )
    assert (
        len(dict_availability_timeseries) == 12
    ), f"Function does not create 12 individual availability_timeseries for the whole year."
    assert (
        dict_availability_timeseries[1].values.sum() == 31 * 24
    ), f"Availability timeseries that is supposed to be 1 for January alone has an unexpected number of available hours."
    total = 0
    for key in dict_availability_timeseries:
        total += dict_availability_timeseries[key].values.sum()
    assert (
        total == 8760
    ), f"Availablity of all 12 availability_timeseries does not insure availability every hour of the year."


def test_define_availability_of_peak_demand_pricing_assets_quarterly():
    dict_availability_timeseries = C0.define_availability_of_peak_demand_pricing_assets(
        dict_test_avilability, 4, 3
    )
    assert (
        len(dict_availability_timeseries) == 4
    ), f"Function does not create 4 individual availability_timeseries for the whole year."
    total = 0
    for key in dict_availability_timeseries:
        total += dict_availability_timeseries[key].values.sum()
    assert (
        total == 8760
    ), f"Availablity of all 12 availability_timeseries does not insure availability every hour of the year."


def test_define_transformer_for_peak_demand_pricing():
    dict_test = {
        ENERGY_CONVERSION: {},
        ENERGY_PROVIDERS: {
            "dso": {
                LABEL: "a_label",
                INFLOW_DIRECTION: "a_direction",
                OUTFLOW_DIRECTION: "b_direction",
                PEAK_DEMAND_PRICING: {VALUE: 60},
                UNIT: "unit",
                ENERGY_VECTOR: "a_vector",
            }
        },
    }
    dict_test_dso = dict_test[ENERGY_PROVIDERS]["dso"].copy()
    transformer_name = "a_name"
    timeseries_availability = pd.Series()
    C0.define_transformer_for_peak_demand_pricing(
        dict_test, dict_test_dso, transformer_name, timeseries_availability
    )
    assert transformer_name in dict_test[ENERGY_CONVERSION]
    for k in [
        LABEL,
        OPTIMIZE_CAP,
        INSTALLED_CAP,
        INFLOW_DIRECTION,
        OUTFLOW_DIRECTION,
        AVAILABILITY_DISPATCH,
        DISPATCH_PRICE,
        SPECIFIC_COSTS,
        DEVELOPMENT_COSTS,
        SPECIFIC_COSTS_OM,
        OEMOF_ASSET_TYPE,
        EFFICIENCY,
        ENERGY_VECTOR,
    ]:
        assert (
            k in dict_test[ENERGY_CONVERSION][transformer_name]
        ), f"Function does not add {k} to the asset dictionary of the {transformer_name}."
    assert (
        dict_test[ENERGY_CONVERSION][transformer_name][SPECIFIC_COSTS_OM][VALUE]
        == dict_test[ENERGY_PROVIDERS]["dso"][PEAK_DEMAND_PRICING][VALUE]
    ), f"The {SPECIFIC_COSTS_OM} of the newly defined {transformer_name} is not equal to the {PEAK_DEMAND_PRICING} of the energy provider it is defined from."


def test_define_energy_vectors_from_busses():
    bus_name = "a_bus"
    bus_label = bus_name + "label"
    energy_vector = "Electricity"
    dict_test = {
        PROJECT_DATA: {},
        ENERGY_BUSSES: {bus_name: {LABEL: bus_label, ENERGY_VECTOR: energy_vector}},
    }
    C0.define_energy_vectors_from_busses(dict_test)
    assert (
        LES_ENERGY_VECTOR_S in dict_test[PROJECT_DATA]
    ), f"The keys and names of the energy vectors of the LES are not added to the dict_test."
    assert (
        energy_vector in dict_test[PROJECT_DATA][LES_ENERGY_VECTOR_S]
    ), f"The energy vector of bus {bus} is not added as {LES_ENERGY_VECTOR_S}."
    expected_label = energy_vector.replace("_", " ")
    assert (
        dict_test[PROJECT_DATA][LES_ENERGY_VECTOR_S][energy_vector] == expected_label
    ), f"The label of the {energy_vector} is incorrectly parsed as {dict_test[PROJECT_DATA][LES_ENERGY_VECTOR_S][energy_vector]} instead of {expected_label}."


def test_add_assets_to_asset_dict_of_connected_busses():
    asset_names = ["asset_name_" + str(i) for i in range(0, 6)]
    in_bus_names = ["in_bus_name_" + str(i) for i in range(0, 6)]
    out_bus_names = ["out_bus_name_" + str(i) for i in range(0, 6)]
    energy_vector = "Electricity"
    dict_test = {
        ENERGY_BUSSES: {},
        ENERGY_PROVIDERS: {
            asset_names[0]: {
                LABEL: asset_names[0],
                OUTFLOW_DIRECTION: out_bus_names[0],
                INFLOW_DIRECTION: in_bus_names[0],
                ENERGY_VECTOR: energy_vector,
            }
        },
        ENERGY_STORAGE: {
            asset_names[1]: {
                LABEL: asset_names[1],
                OUTFLOW_DIRECTION: out_bus_names[1],
                INFLOW_DIRECTION: in_bus_names[1],
                ENERGY_VECTOR: energy_vector,
            }
        },
        ENERGY_CONSUMPTION: {
            asset_names[2]: {
                LABEL: asset_names[2],
                INFLOW_DIRECTION: in_bus_names[2],
                ENERGY_VECTOR: energy_vector,
            }
        },
        ENERGY_PRODUCTION: {
            asset_names[3]: {
                LABEL: asset_names[3],
                OUTFLOW_DIRECTION: out_bus_names[2],
                ENERGY_VECTOR: energy_vector,
            }
        },
        ENERGY_CONVERSION: {
            asset_names[4]: {
                LABEL: asset_names[4],
                OUTFLOW_DIRECTION: out_bus_names[3],
                INFLOW_DIRECTION: in_bus_names[3],
                ENERGY_VECTOR: energy_vector,
            },
            asset_names[5]: {
                LABEL: asset_names[5],
                OUTFLOW_DIRECTION: [out_bus_names[4], out_bus_names[5]],
                INFLOW_DIRECTION: [in_bus_names[4], in_bus_names[5]],
                ENERGY_VECTOR: energy_vector,
            },
        },
    }
    for bus in in_bus_names:
        dict_test[ENERGY_BUSSES].update(
            {bus: {LABEL: bus, ENERGY_VECTOR: energy_vector}}
        )

    for bus in out_bus_names:
        dict_test[ENERGY_BUSSES].update(
            {bus: {LABEL: bus, ENERGY_VECTOR: energy_vector}}
        )

    C0.add_assets_to_asset_dict_of_connected_busses(dict_test)

    assert (
        asset_names[0] in dict_test[ENERGY_BUSSES][in_bus_names[0]][ASSET_DICT]
    ), f"Asset {asset_names[0]} not added to the connected bus {in_bus_names[0]}"
    assert (
        asset_names[1] in dict_test[ENERGY_BUSSES][in_bus_names[1]][ASSET_DICT]
    ), f"Asset {asset_names[1]} not added to the connected bus {in_bus_names[1]}"
    assert (
        asset_names[2] in dict_test[ENERGY_BUSSES][in_bus_names[2]][ASSET_DICT]
    ), f"Asset {asset_names[2]} not added to the connected bus {in_bus_names[2]}"
    assert (
        asset_names[4] in dict_test[ENERGY_BUSSES][in_bus_names[3]][ASSET_DICT]
    ), f"Asset {asset_names[4]} not added to the connected bus {in_bus_names[3]}"
    assert (
        asset_names[5] in dict_test[ENERGY_BUSSES][in_bus_names[4]][ASSET_DICT]
    ), f"Asset {asset_names[5]} not added to the connected bus {in_bus_names[4]}"
    assert (
        asset_names[5] in dict_test[ENERGY_BUSSES][in_bus_names[5]][ASSET_DICT]
    ), f"Asset {asset_names[5]} not added to the connected bus {in_bus_names[5]}"
    assert (
        asset_names[0] in dict_test[ENERGY_BUSSES][out_bus_names[0]][ASSET_DICT]
    ), f"Asset {asset_names[0]} not added to the connected bus {out_bus_names[0]}"
    assert (
        asset_names[1] in dict_test[ENERGY_BUSSES][out_bus_names[1]][ASSET_DICT]
    ), f"Asset {asset_names[1]} not added to the connected bus {out_bus_names[1]}"
    assert (
        asset_names[3] in dict_test[ENERGY_BUSSES][out_bus_names[2]][ASSET_DICT]
    ), f"Asset {asset_names[3]} not added to the connected bus {out_bus_names[2]}"
    assert (
        asset_names[4] in dict_test[ENERGY_BUSSES][out_bus_names[3]][ASSET_DICT]
    ), f"Asset {asset_names[4]} not added to the connected bus {out_bus_names[3]}"
    assert (
        asset_names[5] in dict_test[ENERGY_BUSSES][out_bus_names[4]][ASSET_DICT]
    ), f"Asset {asset_names[5]} not added to the connected bus {out_bus_names[4]}"
    assert (
        asset_names[5] in dict_test[ENERGY_BUSSES][out_bus_names[5]][ASSET_DICT]
    ), f"Asset {asset_names[5]} not added to the connected bus {out_bus_names[5]}"


def test_add_asset_to_asset_dict_for_each_flow_direction():
    bus_names = ["bus_name_" + str(i) for i in range(1, 3)]
    asset_name = "asset"
    asset_label = "asset_label"
    energy_vector = "Electricity"
    dict_test = {
        ENERGY_BUSSES: {
            bus_names[0]: {LABEL: bus_names[0], ENERGY_VECTOR: energy_vector},
            bus_names[1]: {LABEL: bus_names[1], ENERGY_VECTOR: energy_vector},
        },
        ENERGY_CONVERSION: {
            asset_name: {
                LABEL: asset_label,
                OUTFLOW_DIRECTION: bus_names[0],
                INFLOW_DIRECTION: bus_names[1],
                ENERGY_VECTOR: energy_vector,
            }
        },
    }
    C0.add_asset_to_asset_dict_for_each_flow_direction(
        dict_test, dict_test[ENERGY_CONVERSION][asset_name], asset_name
    )
    for bus in dict_test[ENERGY_BUSSES].keys():
        assert (
            asset_name in dict_test[ENERGY_BUSSES][bus][ASSET_DICT].keys()
        ), f"Asset {asset_name} is not included in the asset list of {bus}."
        assert (
            dict_test[ENERGY_BUSSES][bus][ASSET_DICT][asset_name] == asset_label
        ), f"The asset label of asset {asset_name} in the asset list of {bus} is of unexpected value."


def test_add_asset_to_asset_dict_of_bus_ValueError():
    bus_name = "bus_name"
    asset_name = "asset"
    asset_label = "asset_label"
    energy_vector = "Electricity"
    dict_test = {
        ENERGY_BUSSES: {bus_name: {LABEL: bus_name, ENERGY_VECTOR: energy_vector}},
        ENERGY_PROVIDERS: {
            asset_name: {
                LABEL: asset_label,
                OUTFLOW_DIRECTION: bus_name + "s",
                ENERGY_VECTOR: energy_vector,
            }
        },
    }
    with pytest.raises(ValueError):
        C0.add_asset_to_asset_dict_of_bus(
            dict_values=dict_test,
            bus=dict_test[ENERGY_PROVIDERS][asset_name][OUTFLOW_DIRECTION],
            asset_key=asset_name,
            asset_label=asset_label,
        )


def test_add_asset_to_asset_dict_of_bus():
    bus_name = "bus_name"
    asset_name = "asset"
    asset_label = "asset_label"
    energy_vector = "Electricity"
    dict_test = {
        ENERGY_BUSSES: {bus_name: {LABEL: bus_name, ENERGY_VECTOR: energy_vector}},
        ENERGY_PROVIDERS: {
            asset_name: {
                LABEL: asset_label,
                OUTFLOW_DIRECTION: bus_name,
                ENERGY_VECTOR: energy_vector,
            }
        },
    }
    C0.add_asset_to_asset_dict_of_bus(
        dict_values=dict_test,
        bus=dict_test[ENERGY_PROVIDERS][asset_name][OUTFLOW_DIRECTION],
        asset_key=asset_name,
        asset_label=asset_label,
    )

    assert (
        asset_name in dict_test[ENERGY_BUSSES][bus_name][ASSET_DICT]
    ), f"The asset {asset_name} is not added to the list of assets attached to the bus."
    assert (
        dict_test[ENERGY_BUSSES][bus_name][ASSET_DICT][asset_name] == asset_label
    ), f"The asset {asset_name} is not added with its {LABEL} to the list of assets attached to the bus."


def test_apply_function_to_single_or_list_apply_to_single():
    def multiply(parameter):
        parameter_processed = 2 * parameter
        return parameter_processed

    parameter = 1
    parameter_processed = C0.apply_function_to_single_or_list(multiply, parameter)
    assert parameter_processed == 2, f"The multiplication with a single value fails."


def test_apply_function_to_single_or_list_apply_to_list():
    def multiply(parameter):
        parameter_processed = 2 * parameter
        return parameter_processed

    parameter = [1, 1]
    parameter_processed = C0.apply_function_to_single_or_list(multiply, parameter)
    assert parameter_processed == [2, 2], f"The multiplication with a list fails."


def test_determine_months_in_a_peak_demand_pricing_period_not_valid():
    with pytest.raises(InvalidPeakDemandPricingPeriodsError):
        C0.determine_months_in_a_peak_demand_pricing_period(
            5, 365
        ), f"No InvalidPeakDemandPricingPeriodsError is raised eventhough an invalid number of pricing periods is requested."


def test_determine_months_in_a_peak_demand_pricing_period_valid():
    months_in_a_period = C0.determine_months_in_a_peak_demand_pricing_period(4, 365)
    assert (
        months_in_a_period == 3
    ), f"The duration, ie. months of the peak demand pricing periods, are calculated incorrectly."


def test_evaluate_lifetime_costs():
    settings = {EVALUATED_PERIOD: {VALUE: 10}}
    economic_data = {
        PROJECT_DURATION: {VALUE: 20},
        DISCOUNTFACTOR: {VALUE: 0.1},
        TAX: {VALUE: 0},
        CRF: {VALUE: 0.1},
        ANNUITY_FACTOR: {VALUE: 7},
    }

    dict_asset = {
        SPECIFIC_COSTS_OM: {VALUE: 5, UNIT: "unit"},
        SPECIFIC_COSTS: {VALUE: 100, UNIT: "unit"},
        DISPATCH_PRICE: {VALUE: 1, UNIT: "unit"},
        LIFETIME: {VALUE: 10},
        UNIT: UNIT,
        AGE_INSTALLED: {VALUE: 0},
    }

    C0.evaluate_lifetime_costs(settings, economic_data, dict_asset)

    # Note: Only the relevant keys are tested here. The valid calculation of the costs is tested with test_benchmark_KPI.py, Test_Economic_KPI.test_benchmark_Economic_KPI_C2_E2()
    for k in [
        LIFETIME_SPECIFIC_COST,
        LIFETIME_SPECIFIC_COST_OM,
        ANNUITY_SPECIFIC_INVESTMENT_AND_OM,
        SIMULATION_ANNUITY,
        LIFETIME_PRICE_DISPATCH,
        SPECIFIC_REPLACEMENT_COSTS_INSTALLED,
        SPECIFIC_REPLACEMENT_COSTS_OPTIMIZED,
    ]:
        assert k in dict_asset, f"Function does not add {k} to the asset dictionary."


group = "GROUP"
asset = "ASSET"
subasset = "SUBASSET"
unit = "kW"
installed_cap = 50


def test_process_maximum_cap_constraint_maximumCap_undefined():
    """If no maximum cap is defined previously, it is defined as none."""
    dict_values = {group: {asset: {UNIT: unit}}}
    C0.process_maximum_cap_constraint(dict_values, group, asset, subasset=None)
    assert (
        MAXIMUM_CAP in dict_values[group][asset]
    ), f"The function does not add a MAXIMUM_CAP to the asset dictionary."
    assert (
        dict_values[group][asset][MAXIMUM_CAP][VALUE] is None
    ), f"Eventhough there is no limit imposed to the asset capacity, its maximumCap is defined to be {dict_values[group][asset][MAXIMUM_CAP][VALUE]}."
    assert (
        dict_values[group][asset][MAXIMUM_CAP][UNIT] == unit
    ), f"The maximumCap is in {dict_values[group][asset][MAXIMUM_CAP][UNIT]}, while the asset itself has unit {dict_values[group][asset][UNIT]}."


def test_process_maximum_cap_constraint_maximumCap_is_None():
    """The asset has a maximumCap==None, and a unit is added."""
    dict_values = {group: {asset: {UNIT: unit, MAXIMUM_CAP: {VALUE: None}}}}
    C0.process_maximum_cap_constraint(dict_values, group, asset, subasset=None)
    assert (
        dict_values[group][asset][MAXIMUM_CAP][VALUE] is None
    ), f"Eventhough there is no limit imposed to the asset capacity, its maximumCap is defined to be {dict_values[group][asset][MAXIMUM_CAP][VALUE]}."
    assert (
        dict_values[group][asset][MAXIMUM_CAP][UNIT] == unit
    ), f"The maximumCap is in {dict_values[group][asset][MAXIMUM_CAP][UNIT]}, while the asset itself has unit {dict_values[group][asset][UNIT]}."


def test_process_maximum_cap_constraint_maximumCap_is_int():
    """The asset has a maximumCap of int, and a unit is added."""
    maxCap = 100
    dict_values = {
        group: {
            asset: {
                UNIT: unit,
                INSTALLED_CAP: {VALUE: installed_cap},
                MAXIMUM_CAP: {VALUE: maxCap},
            }
        }
    }
    C0.process_maximum_cap_constraint(dict_values, group, asset, subasset=None)
    assert (
        dict_values[group][asset][MAXIMUM_CAP][VALUE] == maxCap
    ), f"The initial maximumCap defined by the end-user ({maxCap}) is overwritten by a different value ({dict_values[group][asset][MAXIMUM_CAP][VALUE]})."
    assert (
        dict_values[group][asset][MAXIMUM_CAP][UNIT] == unit
    ), f"The maximumCap is in {dict_values[group][asset][MAXIMUM_CAP][UNIT]}, while the asset itself has unit {dict_values[group][asset][UNIT]}."


def test_process_maximum_cap_constraint_maximumCap_is_float():
    """The asset has a maximumCap of float, and a unit is added"""
    maxCap = 100.1
    dict_values = {
        group: {
            asset: {
                UNIT: unit,
                INSTALLED_CAP: {VALUE: installed_cap},
                MAXIMUM_CAP: {VALUE: maxCap},
            }
        }
    }
    C0.process_maximum_cap_constraint(dict_values, group, asset, subasset=None)
    assert (
        dict_values[group][asset][MAXIMUM_CAP][VALUE] == maxCap
    ), f"The initial maximumCap defined by the end-user ({maxCap}) is overwritten by a different value ({dict_values[group][asset][MAXIMUM_CAP][VALUE]})."
    assert (
        dict_values[group][asset][MAXIMUM_CAP][UNIT] == unit
    ), f"The maximumCap is in {dict_values[group][asset][MAXIMUM_CAP][UNIT]}, while the asset itself has unit {dict_values[group][asset][UNIT]}."


def test_process_maximum_cap_constraint_maximumCap_is_0():
    """The asset has no maximumCapacity, and the entry is translated into a unit-value pair."""
    maxCap = 0

    dict_values = {
        group: {
            asset: {
                UNIT: unit,
                INSTALLED_CAP: {VALUE: installed_cap},
                MAXIMUM_CAP: {VALUE: maxCap},
            }
        }
    }
    with pytest.warns(UserWarning):
        C0.process_maximum_cap_constraint(dict_values, group, asset, subasset=None)
        assert (
            dict_values[group][asset][MAXIMUM_CAP][VALUE] is None
        ), f"The initial maximumCap defined by the end-user ({maxCap}) is overwritten by a different value ({dict_values[group][asset][MAXIMUM_CAP][VALUE]})."


def test_process_maximum_cap_constraint_maximumCap_is_int_smaller_than_installed_cap():
    """"The asset has a maximumCap < installedCap which is invalid and being ignored."""
    maxCap = 10
    dict_values = {
        group: {
            asset: {
                UNIT: unit,
                INSTALLED_CAP: {VALUE: installed_cap},
                MAXIMUM_CAP: {VALUE: maxCap},
            }
        }
    }
    with pytest.warns(UserWarning):
        C0.process_maximum_cap_constraint(dict_values, group, asset, subasset=None)
        assert (
            dict_values[group][asset][MAXIMUM_CAP][VALUE] is None
        ), f"The invalid input is not ignored by defining maximumCap as None."


def test_process_maximum_cap_constraint_group_is_ENERGY_PRODUCTION_fuel_source():
    """The asset belongs to the energy production group, but is a dispatchable fuel source. The maximumCap is processed as usual."""
    group = ENERGY_PRODUCTION
    maxCap = 100
    dict_values = {
        group: {
            asset: {
                LABEL: asset,
                UNIT: unit,
                INSTALLED_CAP: {VALUE: installed_cap},
                MAXIMUM_CAP: {VALUE: maxCap},
                FILENAME: None,
            }
        }
    }
    C0.process_maximum_cap_constraint(dict_values, group, asset, subasset=None)
    assert (
        dict_values[group][asset][MAXIMUM_CAP][VALUE] == maxCap
    ), f"The initial maximumCap defined by the end-user ({maxCap}) is overwritten by a different value ({dict_values[group][asset][MAXIMUM_CAP][VALUE]})."


def test_process_maximum_cap_constraint_group_is_ENERGY_PRODUCTION_non_dispatchable_asset():
    """The asset belongs to the energy production group, and is a non-dispatchable asset.
    As the maximumCap is used to define the maximum capacity of an asset, but used in oemof-solph to limit a flow, the value has to be translated."""
    timeseries_peak = 0.8
    group = ENERGY_PRODUCTION
    maxCap = 100
    dict_values = {
        group: {
            asset: {
                LABEL: asset,
                UNIT: unit,
                INSTALLED_CAP: {VALUE: installed_cap},
                MAXIMUM_CAP: {VALUE: maxCap},
                FILENAME: "a_name",
                TIMESERIES_PEAK: {VALUE: timeseries_peak},
            }
        }
    }
    C0.process_maximum_cap_constraint(dict_values, group, asset, subasset=None)
    assert (
        dict_values[group][asset][MAXIMUM_CAP][VALUE] == maxCap * timeseries_peak
    ), f"The initial maximumCap defined by the end-user ({maxCap}) is overwritten by a different value ({dict_values[group][asset][MAXIMUM_CAP][VALUE]})."


def test_process_maximum_cap_constraint_subasset():
    """For storages, the subassets have to be processes. This tests the procedure examplary."""
    dict_values = {
        group: {
            asset: {subasset: {LABEL: asset, UNIT: unit, MAXIMUM_CAP: {VALUE: None},}}
        }
    }

    C0.process_maximum_cap_constraint(dict_values, group, asset, subasset=subasset)
    assert (
        dict_values[group][asset][subasset][MAXIMUM_CAP][VALUE] is None
    ), f"The function does not change the previously defined MAXIMUM_CAP."
    assert (
        dict_values[group][asset][subasset][MAXIMUM_CAP][UNIT] == unit
    ), f"The maximumCap is in {dict_values[group][asset][subasset][MAXIMUM_CAP][UNIT]}, while the asset itself has unit {dict_values[group][asset][subasset][UNIT]}."


DSO = "dso"
dict_test = deepcopy(dict_test_avilability)
dict_test[SIMULATION_SETTINGS].update({EVALUATED_PERIOD: {VALUE: 7}})
dict_test.update({ECONOMIC_DATA: {CURR: "curr"}})
dict_test.update(
    {
        ENERGY_CONVERSION: {},
        ENERGY_PROVIDERS: {
            DSO: {
                LABEL: "a_label",
                INFLOW_DIRECTION: "a_direction",
                OUTFLOW_DIRECTION: "b_direction",
                PEAK_DEMAND_PRICING: {VALUE: 60},
                UNIT: "unit",
                ENERGY_VECTOR: "a_vector",
                PEAK_DEMAND_PRICING_PERIOD: {VALUE: 1},
            }
        },
    }
)


def test_add_a_transformer_for_each_peak_demand_pricing_period_1_period():
    dict_test_trafo = deepcopy(dict_test)
    dict_availability_timeseries = C0.define_availability_of_peak_demand_pricing_assets(
        dict_test_trafo, 1, 12,
    )
    list_of_dso_energyConversion_assets = C0.add_a_transformer_for_each_peak_demand_pricing_period(
        dict_test_trafo, dict_test[ENERGY_PROVIDERS][DSO], dict_availability_timeseries,
    )
    assert (
        len(list_of_dso_energyConversion_assets) == 1
    ), f"The list of peak demand pricing transformers is not only one entry long."
    exp_list = [
        dict_test_trafo[ENERGY_PROVIDERS][DSO][LABEL]
        + DSO_CONSUMPTION
        + DSO_PEAK_DEMAND_PERIOD
    ]
    assert (
        list_of_dso_energyConversion_assets == exp_list
    ), f'The names of the created peak demand pricing transformers are with "{list_of_dso_energyConversion_assets}" not as they were expected ({exp_list}).'
    for transformer in list_of_dso_energyConversion_assets:
        assert (
            transformer in dict_test_trafo[ENERGY_CONVERSION]
        ), f"Transformer {transformer} is not added as an energyConversion object."


def test_add_a_transformer_for_each_peak_demand_pricing_period_2_periods():
    dict_test_trafo = deepcopy(dict_test)
    dict_availability_timeseries = C0.define_availability_of_peak_demand_pricing_assets(
        dict_test_trafo, 2, 6,
    )
    list_of_dso_energyConversion_assets = C0.add_a_transformer_for_each_peak_demand_pricing_period(
        dict_test_trafo, dict_test[ENERGY_PROVIDERS][DSO], dict_availability_timeseries,
    )
    assert (
        len(list_of_dso_energyConversion_assets) == 2
    ), f"The list of peak demand pricing transformers is not only two entries long."
    exp_list = [
        dict_test[ENERGY_PROVIDERS][DSO][LABEL]
        + DSO_CONSUMPTION
        + DSO_PEAK_DEMAND_PERIOD
        + "_"
        + str(1),
        dict_test[ENERGY_PROVIDERS][DSO][LABEL]
        + DSO_CONSUMPTION
        + DSO_PEAK_DEMAND_PERIOD
        + "_"
        + str(2),
    ]
    assert (
        list_of_dso_energyConversion_assets == exp_list
    ), f'The names of the created peak demand pricing transformers are with "{list_of_dso_energyConversion_assets}" not as they were expected ({exp_list}).'

    for transformer in list_of_dso_energyConversion_assets:
        assert (
            transformer in dict_test_trafo[ENERGY_CONVERSION]
        ), f"Transformer {transformer} is not added as an energyConversion object."


dict_test[ECONOMIC_DATA].update({PROJECT_DURATION: {VALUE: 20}})
dict_test[ENERGY_PROVIDERS][DSO].update({ENERGY_PRICE: {VALUE: 1, UNIT: UNIT}})
dict_test.update(
    {
        ENERGY_BUSSES: {
            dict_test[ENERGY_PROVIDERS][DSO][INFLOW_DIRECTION]: {},
            dict_test[ENERGY_PROVIDERS][DSO][OUTFLOW_DIRECTION]: {},
        }
    }
)
dict_test.update({ENERGY_PRODUCTION: {}})


def test_define_source():
    """The outflow direction is in energyBusses."""
    outflow = "out"
    dict_test_source = {
        ENERGY_BUSSES: {outflow: {}},
        ENERGY_PRODUCTION: {},
        ECONOMIC_DATA: {PROJECT_DURATION: {VALUE: 20}},
    }

    source_name = "source"
    unit_price = 1
    energy_vector = "Electricity"
    C0.define_source(
        dict_values=dict_test_source,
        asset_key=source_name,
        outflow_direction=outflow,
        energy_vector=energy_vector,
    )
    assert (
        source_name in dict_test_source[ENERGY_PRODUCTION]
    ), f"The source {source_name} was not added to the list of energyProduction assets."
    for key in [
        OEMOF_ASSET_TYPE,
        LABEL,
        OUTFLOW_DIRECTION,
        DISPATCHABILITY,
        LIFETIME,
        OPTIMIZE_CAP,
        MAXIMUM_CAP,
        AGE_INSTALLED,
        ENERGY_VECTOR,
    ]:
        assert (
            key in dict_test_source[ENERGY_PRODUCTION][source_name]
        ), f"The function should add key {key} to the newly defined source, but does not."
    assert (
        dict_test_source[ENERGY_PRODUCTION][source_name][OEMOF_ASSET_TYPE]
        == OEMOF_SOURCE
    ), f"The {OEMOF_ASSET_TYPE} of the defined source is not {OEMOF_SOURCE}."
    assert (
        dict_test_source[ENERGY_PRODUCTION][source_name][LABEL]
        == source_name + AUTO_SOURCE
    ), f"The {LABEL} of the defined source is not {source_name + AUTO_SOURCE}."
    assert (
        dict_test_source[ENERGY_PRODUCTION][source_name][OUTFLOW_DIRECTION] == outflow
    ), f"The {OUTFLOW_DIRECTION} of the defined source is not {outflow}."
    assert (
        dict_test_source[ENERGY_PRODUCTION][source_name][DISPATCHABILITY] is True
    ), f"The boolean value of {DISPATCHABILITY} of the defined source is not {True}."
    assert (
        dict_test_source[ENERGY_PRODUCTION][source_name][LIFETIME][VALUE] == 20
    ), f"The {LIFETIME} {VALUE} of the defined source is not {20}."
    assert (
        dict_test_source[ENERGY_PRODUCTION][source_name][LIFETIME][UNIT] == UNIT_YEAR
    ), f"The {LIFETIME} {UNIT} of the defined source is not {UNIT_YEAR}."
    assert (
        dict_test_source[ENERGY_PRODUCTION][source_name][OPTIMIZE_CAP][VALUE] is True
    ), f"The {OPTIMIZE_CAP} {VALUE} of the defined source is not {True}."
    assert (
        dict_test_source[ENERGY_PRODUCTION][source_name][OPTIMIZE_CAP][UNIT]
        == TYPE_BOOL
    ), f"The {OPTIMIZE_CAP} {UNIT} of the defined source is not {TYPE_BOOL}."
    assert (
        dict_test_source[ENERGY_PRODUCTION][source_name][MAXIMUM_CAP][VALUE] is None
    ), f"The {MAXIMUM_CAP} {VALUE} of the defined source is not {None}."
    # assert dict_test_source[ENERGY_PRODUCTION][source_name][MAXIMUM_CAP][UNIT] == "?" this is not properly defined in the function yet.
    assert (
        dict_test_source[ENERGY_PRODUCTION][source_name][AGE_INSTALLED][VALUE] == 0
    ), f"The {AGE_INSTALLED} {VALUE} of the defined source is not {0}."
    assert (
        dict_test_source[ENERGY_PRODUCTION][source_name][AGE_INSTALLED][UNIT]
        == UNIT_YEAR
    ), f"The {AGE_INSTALLED} {UNIT} of the defined source is not {UNIT_YEAR}."
    assert (
        dict_test_source[ENERGY_PRODUCTION][source_name][ENERGY_VECTOR] == energy_vector
    ), f"The {ENERGY_VECTOR} of the defined source is not {energy_vector}."
    assert (
        source_name in dict_test_source[ENERGY_BUSSES][outflow][ASSET_DICT]
    ), f"The new source {source_name} is not in the list of assets of the connected bus {outflow}."


def test_define_source_exception_unknown_bus():
    """The bus of an energy provider source is not included in the energyBusses."""
    outflow = "out"
    dict_test_source = {
        ENERGY_BUSSES: {},
        ENERGY_PRODUCTION: {},
        ECONOMIC_DATA: {PROJECT_DURATION: {VALUE: 20}},
    }

    source_name = "source"
    unit_price = 1
    energy_vector = "Electricity"
    C0.define_source(
        dict_values=dict_test_source,
        asset_key=source_name,
        outflow_direction=outflow,
        price={VALUE: unit_price, UNIT: UNIT},
        energy_vector=energy_vector,
    )
    assert (
        outflow in dict_test_source[ENERGY_BUSSES]
    ), f"Energy bus {outflow} is not defined for in the energyBusses"
    for key in [LABEL, ENERGY_VECTOR, ASSET_DICT]:
        assert (
            key in dict_test_source[ENERGY_BUSSES][outflow]
        ), f"Key {key} is not defined for the new energyBus {outflow}."
    assert (
        dict_test_source[ENERGY_BUSSES][outflow][LABEL] == outflow
    ), f"The {LABEL} of the bus is not {outflow} as it should be"
    assert (
        dict_test_source[ENERGY_BUSSES][outflow][ENERGY_VECTOR] == energy_vector
    ), f"The {ENERGY_VECTOR} of the bus is not {energy_vector} as it should be"
    assert dict_test_source[ENERGY_BUSSES][outflow][ASSET_DICT] == {
        source_name: source_name + AUTO_SOURCE
    }, f"The new source {source_name} is not included in the {ASSET_DICT} of the newly defined bus {outflow}"


def test_define_source_price_not_None_but_with_scalar_value():
    outflow = "out"
    dict_test_source = {
        ENERGY_BUSSES: {},
        ENERGY_PRODUCTION: {},
        ECONOMIC_DATA: {PROJECT_DURATION: {VALUE: 20}},
    }

    source_name = "source"
    unit_price = 1
    energy_vector = "Electricity"
    C0.define_source(
        dict_values=dict_test_source,
        asset_key=source_name,
        outflow_direction=outflow,
        price={VALUE: unit_price, UNIT: UNIT},
        energy_vector=energy_vector,
    )
    DISPATCH_PRICE in dict_test_source[ENERGY_PRODUCTION][
        source_name
    ], f"The price is not added as {DISPATCH_PRICE} to the new source."
    assert (
        dict_test_source[ENERGY_PRODUCTION][source_name][DISPATCH_PRICE][VALUE]
        == unit_price
    ), f"The dispatch price is not equal to the price it should be defined as."
    assert (
        dict_test_source[ENERGY_PRODUCTION][source_name][DISPATCH_PRICE][UNIT] == UNIT
    ), f"The unit of the dispatch price is not correct."


def test_define_source_timeseries_not_None():
    outflow = "out"
    dict_test_source = {
        ENERGY_BUSSES: {},
        ENERGY_PRODUCTION: {},
        ECONOMIC_DATA: {PROJECT_DURATION: {VALUE: 20}},
    }

    source_name = "source"
    unit_price = 1
    energy_vector = "Electricity"
    C0.define_source(
        dict_values=dict_test_source,
        asset_key=source_name,
        outflow_direction=outflow,
        price={VALUE: unit_price, UNIT: UNIT},
        energy_vector=energy_vector,
        timeseries=pd.Series([1, 2, 3]),
    )
    assert (
        dict_test_source[ENERGY_PRODUCTION][source_name][DISPATCHABILITY] is False
    ), f"With an availability timeseries defined, the new source should be defined with {DISPATCHABILITY} is {False}"
    assert (
        dict_test_source[ENERGY_PRODUCTION][source_name][OPTIMIZE_CAP][VALUE] is True
    ), f"The capacity of the non-dispatchable source should be optimized."
    assert (
        TIMESERIES_PEAK in dict_test_source[ENERGY_PRODUCTION][source_name]
    ), f"The property '{TIMESERIES_PEAK}' of the availability timeseries is not added."
    assert (
        TIMESERIES_NORMALIZED in dict_test_source[ENERGY_PRODUCTION][source_name]
    ), f"The property '{TIMESERIES_NORMALIZED}' of the availability timeseries is not added."
    assert (
        dict_test_source[ENERGY_PRODUCTION][source_name][DISPATCH_PRICE][VALUE]
        == unit_price / 3
    ), f"The dispatch price is was not normalized based on the availability timeseries."


dict_test.update({ENERGY_CONSUMPTION: {}})


def test_define_sink():
    dict_test_sink = deepcopy(dict_test)
    sink_name = "a_name"
    dict_feedin = {VALUE: -1, UNIT: UNIT}
    C0.define_sink(
        dict_values=dict_test_sink,
        asset_key=sink_name,
        price=dict_feedin,
        inflow_direction=dict_test_sink[ENERGY_PROVIDERS][DSO][INFLOW_DIRECTION],
        specific_costs={VALUE: 0, UNIT: CURR + "/" + UNIT},
        energy_vector=dict_test_sink[ENERGY_PROVIDERS][DSO][ENERGY_VECTOR],
    )
    assert (
        sink_name in dict_test_sink[ENERGY_CONSUMPTION]
    ), f"The sink {sink_name} was not added to the list of energyConsumption assets."


float = 0.9
dict_test[ENERGY_PROVIDERS][DSO].update({FEEDIN_TARIFF: {VALUE: float, UNIT: UNIT}})


def test_define_auxiliary_assets_of_energy_providers():
    dict_test_provider = deepcopy(dict_test)
    C0.define_auxiliary_assets_of_energy_providers(dict_test_provider, DSO)
    assert (
        DSO + DSO_CONSUMPTION in dict_test_provider[ENERGY_PRODUCTION]
    ), f"No source for energy consumption from the energy provider is added."
    assert (
        DSO + DSO_FEEDIN + AUTO_SINK in dict_test_provider[ENERGY_CONSUMPTION]
    ), f"No sink for feed-in into the energy provider`s grid is added."
    assert (
        CONNECTED_CONSUMPTION_SOURCE in dict_test_provider[ENERGY_PROVIDERS][DSO]
    ), f"The key {CONNECTED_CONSUMPTION_SOURCE} is not added to dict_test_provider[ENERGY_PROVIDERS][DSO]."
    exp = DSO + DSO_CONSUMPTION + AUTO_SOURCE
    assert (
        dict_test_provider[ENERGY_PROVIDERS][DSO][CONNECTED_CONSUMPTION_SOURCE] == exp
    ), f"The {CONNECTED_CONSUMPTION_SOURCE} is unexpected with {dict_test_provider[ENERGY_PROVIDERS][DSO][CONNECTED_CONSUMPTION_SOURCE]} instead of {exp}"
    assert (
        CONNECTED_PEAK_DEMAND_PRICING_TRANSFORMERS
        in dict_test_provider[ENERGY_PROVIDERS][DSO]
    ), f"The key {CONNECTED_PEAK_DEMAND_PRICING_TRANSFORMERS} is not added to dict_test_provider[ENERGY_PROVIDERS][DSO]."
    assert (
        len(
            dict_test_provider[ENERGY_PROVIDERS][DSO][
                CONNECTED_PEAK_DEMAND_PRICING_TRANSFORMERS
            ]
        )
        == 1
    ), f"There should only be one peak demand pricing transformer, but there are {len(dict_test_provider[ENERGY_PROVIDERS][DSO][CONNECTED_PEAK_DEMAND_PRICING_TRANSFORMERS])}."
    assert (
        CONNECTED_FEEDIN_SINK in dict_test_provider[ENERGY_PROVIDERS][DSO]
    ), f"The key {CONNECTED_FEEDIN_SINK} is not added to dict_test_provider[ENERGY_PROVIDERS][DSO]."
    exp = DSO + DSO_FEEDIN + AUTO_SINK
    assert (
        dict_test_provider[ENERGY_PROVIDERS][DSO][CONNECTED_FEEDIN_SINK] == exp
    ), f"The {CONNECTED_FEEDIN_SINK} is unexpected with {dict_test_provider[ENERGY_PROVIDERS][DSO][CONNECTED_FEEDIN_SINK]} instead of {exp}"
    assert (
        dict_test_provider[ENERGY_CONSUMPTION][exp][DISPATCH_PRICE][VALUE] == -float
    ), f"The feed-in tarrif should have the inverse sign than the {FEEDIN_TARIFF} defined in the energyProvider {DSO} (ie. {float}), but this is not the case with {dict_test_provider[ENERGY_CONSUMPTION][exp][FEEDIN_TARIFF][VALUE]}"


def test_change_sign_of_feedin_tariff_positive_value(caplog):
    """A positive feed-in tariff has to be changed to a negative value; a info message is logged."""
    feedin_tariff = 0.5
    dict_feedin = {VALUE: feedin_tariff, UNIT: UNIT}
    with caplog.at_level(logging.DEBUG):
        dict_feedin = C0.change_sign_of_feedin_tariff(dict_feedin, DSO)
    assert (
        dict_feedin[VALUE] == -feedin_tariff
    ), f"A positive {FEEDIN_TARIFF} should be set to a negative value."
    assert (
        "which means that feeding into the grid results in a revenue stream."
        in caplog.text
    ), f"When a positive {FEEDIN_TARIFF} is changed to a negative value there should be an info message."


def test_change_sign_of_feedin_tariff_negative_value(caplog):
    """A negative feed-in tariff is changed to a positive value as it indicates expenses when feeding into the grid; a warning msg is logged as the user might not be aware of the norm."""
    feedin_tariff = -0.5
    dict_feedin = {VALUE: feedin_tariff, UNIT: UNIT}
    with caplog.at_level(logging.WARNING):
        dict_feedin = C0.change_sign_of_feedin_tariff(dict_feedin, DSO)
    assert (
        dict_feedin[VALUE] == -feedin_tariff
    ), f"A negative {FEEDIN_TARIFF} should be set to a positive value."
    assert (
        "which means that payments are necessary to be allowed to feed-into the grid"
        in caplog.text
    ), f"When a negative {FEEDIN_TARIFF} is changed to a positive value there should be a warning."


def test_change_sign_of_feedin_tariff_zero(caplog):
    """If the feed-in tariff is zero is stays zero and no logging msg is added."""
    feedin_tariff = 0
    dict_feedin = {VALUE: feedin_tariff, UNIT: UNIT}
    with caplog.at_level(logging.WARNING):
        dict_feedin = C0.change_sign_of_feedin_tariff(dict_feedin, DSO)
    assert (
        dict_feedin[VALUE] == 0
    ), f"If the {FEEDIN_TARIFF} is zero it should stay like that but it was changed to {dict_feedin[VALUE]}."
    assert (
        "which means that there is no renumeration for feed-in to the grid"
        in caplog.text
    ), f"No information regarding feed-in tariff zero is added to the log."


"""
def test_asess_energyVectors_and_add_to_project_data():
    C2.identify_energy_vectors(dict_values)
    assert 1 == 0
    # assert "sector" in dict_values[PROJECT_DATA].keys()

#Create a sink for each energyVector (this actually might be changed in the future - create an excess sink for each bus?)
def test_create_excess_sinks_for_each_energyVector():
    assert 1 == 0

#- Add demand sinks to energyVectors (this should actually be changed and demand sinks should be added to bus relative to input_direction, also see issue #179)
def test_adding_demand_sinks_to_energyVectors():
    assert 1 == 0

def test_naming_busses():
    assert 1 == 0

def test_check_for_missing_data():
    assert 1 == 0

def test_add_missing_data_to_automatically_generated_objects():
    assert 1 == 0

def test_reading_timeseries_of_assets_one_column():
    assert 1 == 0

def test_reading_timeseries_of_assets_multi_column_csv():
    assert 1 == 0

def test_reading_timeseries_of_assets_delimiter_comma():
    assert 1 == 0

def test_reading_timeseries_of_assets_delimiter_semicolon():
    assert 1 == 0

# Read timeseries for parameter of an asset, eg. efficiency
def test_reading_timeseries_of_asset_for_parameter():
    assert 1 == 0

def test_parse_list_of_inputs_one_input():
    assert 1 == 0

def test_parse_list_of_inputs_two_inputs():
    assert 1 == 0

def test_parse_list_of_inputs_one_output():
    assert 1 == 0

def test_parse_list_of_inputs_two_outputs():
    assert 1 == 0

def test_parse_list_of_inputs_two_inputs_two_outputs():
    assert 1 == 0

def test_raise_error_message_multiple_inputs_not_multilpe_parameters():
    assert 1 == 0

def test_raise_error_message_multiple_outputs_multilpe_parameters():
    assert 1 == 0

# Define dso sinks, soures, transformer stations (this will be changed due to bug #119), also for peak demand pricing
def test_generation_of_dso_side():
    assert 1 == 0

# Add a source if a conversion object is connected to a new input_direction (bug #186)
def test_add_source_when_unknown_input_direction():
    assert 1 == 0

# Define all necessary energyBusses and add all assets that are connected to them specifically with asset name and label
def test_defined_energyBusses_complete():
    assert 1 == 0

def test_verification_executing_C1():
    assert 1 == 0
"""
