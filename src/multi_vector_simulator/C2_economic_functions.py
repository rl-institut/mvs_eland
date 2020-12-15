# todo check whether this is the most recent version
# - there were some project costs included wrongly,
# and something with the replacement costs
"""
Module C2 performs the economic pre-processing of MVS' input parameters.
It includes basic economic formulas.

Functionalities:
- Calculate annuity factor
- calculate crf depending on year
- calculate specific lifetime capex, considering replacement costs and residual value of the asset
- calculate annuity from present costs
- calculate present costs based on annuity
- calculate effective fuel price cost, in case there is a annual fuel price change (this functionality still has to be checked in this module)
"""
import logging
import pandas as pd

from multi_vector_simulator.utils.constants import UNIT_HOUR

from multi_vector_simulator.utils.constants_json_strings import (
    ANNUITY_FACTOR,
    DISPATCH_PRICE,
    VALUE,
    UNIT,
    LIFETIME_PRICE_DISPATCH,
)

# annuity factor to calculate present value of cash flows
def annuity_factor(project_life, discount_factor):
    r"""
    Calculates the annuity factor, which in turn in used to calculate the present value of annuities (instalments)

    Parameters
    ----------

    project_life: int
        time period over which the costs of the system occur
    discount_factor: float
        weighted average cost of capital, which is the after-tax average cost of various capital sources

    Returns
    -------
    annuity_factor: float
        financial value "annuity factor".
        Dividing a present cost by tha annuity factor returns its annuity,
        multiplying an annuity with the annuity factor returns its present value


    Notes
    -----

    .. math::

        annuity factor = \frac{1}{discount factor} - \frac{1}{
        discountfactor \cdot (1 + discount factor)^{project life}}

    """
    annuity_factor = 1 / discount_factor - 1 / (
        discount_factor * (1 + discount_factor) ** project_life
    )
    return annuity_factor


# accounting factor to translate present value to annual cash flows
def crf(project_life, discount_factor):
    """
    Calculates the capital recovery ratio used to determine the present value of a series of equal payments (annuity)

    :param project_life: time period over which the costs of the system occur
    :param discount_factor: weighted average cost of capital, which is the after-tax average cost of various capital sources
    :return: capital recovery factor, a ratio used to calculate the present value of an annuity
    """
    crf = (discount_factor * (1 + discount_factor) ** project_life) / (
        (1 + discount_factor) ** project_life - 1
    )
    return crf


def capex_from_investment(
    investment_t0, lifetime, project_life, discount_factor, tax, age_of_asset
):
    """
    Calculates the capital expenditures, also known as CapEx.

    CapEx represent the total funds used to acquire or upgrade an asset.
    The specific capex is calculated by taking into account all future cash flows connected to the investment into one unit of the asset.
    This includes reinvestments, operation and management costs, dispatch costs as well as a deduction of the residual value at project end.
    The residual value is calculated with a linear depreciation of the last investment, ie. as a even share of the last investment over
    the lifetime of the asset. The remaining value of the asset is translated in a present value and then deducted.

    Parameters
    ----------
    investment_t0: float
        first investment at the beginning of the project made at year 0
    lifetime: int
        time period over which investments and re-investments can occur. can be equal to, longer or shorter than project_life
    project_life: int
        time period over which the costs of the system occur
    discount_factor: float
        weighted average cost of capital, which is the after-tax average cost of various capital sources
    tax: float
        compulsory financial charge paid to the government

    Returns
    -------
    specific_capex: float
        Specific capital expenditure for an asset over project lifetime

    specific_replacement_costs_optimized: float
       Specific replacement costs for the asset capacity to be optimized, needed for E2

    specific_replacement_costs_already_installed: float
       replacement costs per unit for the currently already installed assets, needed for E2

    Notes
    -----
    Tested with
    - test_capex_from_investment_lifetime_equals_project_life()
    - test_capex_from_investment_lifetime_smaller_than_project_life()
    - test_capex_from_investment_lifetime_bigger_than_project_life()
    """

    first_time_investment = investment_t0 * (1 + tax)
    # Specific replacement costs for the asset capacity to be optimized
    specific_replacement_costs_optimized = get_replacement_costs(
        0, project_life, lifetime, first_time_investment, discount_factor
    )
    # Specific capex for the optimization
    specific_capex = first_time_investment + specific_replacement_costs_optimized

    # Calculating the replacement costs per unit for the currently already installed assets
    specific_replacement_costs_installed = get_replacement_costs(
        age_of_asset, project_life, lifetime, first_time_investment, discount_factor
    )
    return (
        specific_capex,
        specific_replacement_costs_optimized,
        specific_replacement_costs_installed,
    )


def get_replacement_costs(
    age_of_asset,
    project_lifetime,
    asset_lifetime,
    first_time_investment,
    discount_factor,
):
    r"""
    Calculating the replacement costs of an asset

    Parameters
    ----------
    age_of_asset: int
        Age in years of an already installed asset

    project_lifetime: int
        Project duration in years

    asset_lifetime: int
        Lifetime of an asset in years

    first_time_investment: float
        Investment cost of an asset to be installed

    discount_factor: float
        Discount factor of a project

    Returns
    -------
    Per-unit replacement costs of an asset. If age_asset == 0, they need to be added to the lifetime_specific_costs of the asset.
    If age_asset > 0, it will be needed to calculate the future investment costs of a previously installed asset.
    """

    # Calculate number of investments' rounds
    if project_lifetime + age_of_asset == asset_lifetime:
        number_of_investments = 1
    else:
        number_of_investments = int(
            round((project_lifetime + age_of_asset) / asset_lifetime + 0.5)
        )

    replacement_costs = 0

    # Latest investment is first investment
    latest_investment = first_time_investment
    # Starting from first investment (in the past for installed capacities)
    year = -age_of_asset
    if abs(year) >= asset_lifetime:
        logging.error(
            f"The age of the asset is with {age_of_asset} lower or equal then the {asset_lifetime}. "
            f"This does not make sense, as a replacement is imminent or should already have happened."
            f"Please check this value."
        )

    present_value_of_capital_expenditures = pd.DataFrame(
        [0 for i in range(0, project_lifetime + 1)],
        index=[j for j in range(0, project_lifetime + 1)],
    )

    # Looping over replacements, excluding first_time_investment in year (0 - age_of_asset)
    for count_of_replacements in range(1, number_of_investments):
        # replacements taking place after an asset ends its lifetime
        year += asset_lifetime

        # Update latest_investment (to be used for residual value)
        latest_investment = first_time_investment / ((1 + discount_factor) ** (year))
        # Add latest investment to replacement costs
        replacement_costs += latest_investment
        # Update cash flow projection (specific)
        present_value_of_capital_expenditures.loc[year] = latest_investment

    # Calculation of residual value / value at project end
    year += asset_lifetime
    if year > project_lifetime:
        # the residual of the capex at the end of the simulation time takes into
        linear_depreciation_last_investment = latest_investment / asset_lifetime
        # account the value of the money by dividing by (1 + discount_factor) ** (project_life)
        value_at_project_end = (
            linear_depreciation_last_investment
            * (year - project_lifetime)
            / (1 + discount_factor) ** (project_lifetime)
        )
        # Subtraction of component value at end of life with last replacement (= number_of_investments - 1)
        replacement_costs -= value_at_project_end
        # Update cash flow projection (specific)
        present_value_of_capital_expenditures.loc[
            project_lifetime
        ] = -value_at_project_end

    return replacement_costs


def annuity(present_value, crf):
    """
    Calculates the annuity which is a fixed stream of payments incurred by investments in assets

    Parameters
    ----------
    present_value: float
        current equivalent value of a set of future cash flows for an asset
    crf: float
        ratio used to calculate the present value of an annuity

    Returns
    -------
    annuity: float
        annuity, i.e. payment made at equal intervals

    Notes
    -----
    Tested with test_annuity()
    """
    annuity = present_value * crf
    return annuity


def present_value_from_annuity(annuity, annuity_factor):
    """
    Calculates the present value of future instalments from an annuity

    Parameters
    ----------

    annuity: float
        payment made at equal intervals
    annuity_factor: float
        financial value

    Returns
    -------

    present_value: float
        present value of future payments from an annuity
    """
    present_value = annuity * annuity_factor
    return present_value


'''
Currently unused function.

def fuel_price_present_value(economics,):
    """
    Calculates the present value of the fuel price over the lifetime of the project, taking into consideration the annual price change

    Parameters
    ----------
    economics: dict
        dict with fuel data values
    :return: present value of the fuel price over the lifetime of the project

    Notes
    -----
    Tested with
    - test_present_value_from_annuity()
    """
    cash_flow_fuel_l = 0
    fuel_price_i = economics["fuel_price"]
    # todo check this calculation again!
    if economics["fuel_price_change_annual"] == 0:
        economics.update({"price_fuel": fuel_price_i})
    else:
        for i in range(0, economics[PROJECT_DURATION]):
            cash_flow_fuel_l += fuel_price_i / (1 + economics[DISCOUNTFACTOR]) ** (i)
            fuel_price_i = fuel_price_i * (1 + economics["fuel_price_change_annual"])
        economics.update({"price_fuel": cash_flow_fuel_l * economics[CRF]})
'''


def simulation_annuity(annuity, days):
    """
    Scaling annuity to timeframe
    Updating all annuities above to annuities "for the timeframe", so that optimization is based on more adequate
    costs. Includes project_cost_annuity, distribution_grid_cost_annuity, maingrid_extension_cost_annuity for
    consistency eventhough these are not used in optimization.

    Parameters
    ----------
    annuity: float
        Annuity of an asset

    days: int
        Days to be simulated

    Returns
    -------
    Simulation annuity that considers the lifetime cost for the optimization of one year duration.

    Notes
    -----
    Tested with
    - test_simulation_annuity_week
    - test_simulation_annuity_year
    """
    simulation_annuity = annuity / 365 * days
    return simulation_annuity


def determine_lifetime_price_dispatch(dict_asset, economic_data):
    """
    Determines the price of dispatch of an asset LIFETIME_PRICE_DISPATCH and updates the asset info.

    It takes into account the asset's future expenditures due to dispatch. Depending on the price data provided, another function is executed.

    Parameters
    ----------
    dict_asset: dict
        Data of an asset

    economic_data: dict
        Economic data, including CRF and ANNUITY_FACTOR

    Returns
    -------
    Updates asset dict

    Notes
    -----
    Tested with
    - test_determine_lifetime_price_dispatch_as_int()
    - test_determine_lifetime_price_dispatch_as_float()
    - test_determine_lifetime_price_dispatch_as_list()
    - test_determine_lifetime_price_dispatch_as_timeseries ()
    """
    # Dispatch price is provided as a scalar value
    if isinstance(dict_asset[DISPATCH_PRICE][VALUE], float) or isinstance(
        dict_asset[DISPATCH_PRICE][VALUE], int
    ):
        lifetime_price_dispatch = get_lifetime_price_dispatch_one_value(
            dict_asset[DISPATCH_PRICE][VALUE], economic_data
        )

    # Multiple dispatch prices are provided as asset is connected to multiple busses
    elif isinstance(dict_asset[DISPATCH_PRICE][VALUE], list):
        lifetime_price_dispatch = get_lifetime_price_dispatch_list(
            dict_asset[DISPATCH_PRICE][VALUE], economic_data
        )

    # Dispatch price is provided as a timeseries
    elif isinstance(dict_asset[DISPATCH_PRICE][VALUE], pd.Series):
        lifetime_price_dispatch = get_lifetime_price_dispatch_timeseries(
            dict_asset[DISPATCH_PRICE][VALUE], economic_data
        )

    else:
        raise ValueError(
            f"Type of dispatch_price neither int, float, list or pd.Series, but of type {dict_asset[DISPATCH_PRICE][VALUE]}. Is type correct?"
        )

    # Update asset dict
    dict_asset.update(
        {
            LIFETIME_PRICE_DISPATCH: {
                VALUE: lifetime_price_dispatch,
                UNIT: dict_asset[UNIT] + "/" + UNIT_HOUR,
            }
        }
    )


def get_lifetime_price_dispatch_one_value(dispatch_price, economic_data):
    """
    Lifetime dispatch price is a scalar value that is calulated with the annuity

    By doing this, the operational expenditures, in the simulation only taken into account for a year,
    can be compared to the investment costs.

    .. math::
        lifetime_price_dispatch = DISPATCH_PRICE \cdot ANNUITY_FACTOR

    Parameters
    ----------
    dispatch_price: float or int
        dispatch_price of the asset

    economic_data: dict
        Economic data

    Returns
    -------
    lifetime_price_dispatch: float
        Float that the asset dict is to be updated with

    Notes
    -----
    Tested with
    - test_determine_lifetime_price_dispatch_as_int()
    - test_determine_lifetime_price_dispatch_as_float()
    - test_get_lifetime_price_dispatch_one_value()
    """
    lifetime_price_dispatch = dispatch_price * economic_data[ANNUITY_FACTOR][VALUE]
    return lifetime_price_dispatch


def get_lifetime_price_dispatch_list(dispatch_price, economic_data):
    r"""
    Determines the lifetime dispatch price in case that the dispatch price is a list.

    The dispatch_price can be a list when for example if there are two input flows to a component, eg. water and electricity.
    There should be a lifetime_price_dispatch for each of them.

    .. math::
        lifetime\_price\_dispatch\_i = DISPATCH\_PRICE\_i \cdot ANNUITY\_FACTOR \forall i

    with :math:`i` for all list entries

    Parameters
    ----------
    dispatch_price: list
        Dispatch prices of the asset as a list

    economic_data: dict
        Economic data

    Returns
    -------
    lifetime_price_dispatch: list
        List of floats of lifetime dispatch price that the asset will be updated with


    Notes
    -----
    Tested with
    - test_determine_lifetime_price_dispatch_as_list()
    - test_get_lifetime_price_dispatch_list()
    """
    lifetime_price_dispatch = []
    for price_entry in dispatch_price:
        if isinstance(price_entry, float) or isinstance(price_entry, int):
            lifetime_price_dispatch.append(
                price_entry * economic_data[ANNUITY_FACTOR][VALUE]
            )
        elif isinstance(price_entry, pd.Series):
            lifetime_price_dispatch_entry = get_lifetime_price_dispatch_timeseries(
                price_entry, economic_data
            )
            lifetime_price_dispatch.append(lifetime_price_dispatch_entry)
        else:
            raise ValueError(
                f"Type of a dispatch_price entry of the list is neither int, float or pd.Series, but of type {type(price_entry)}. Is type correct?"
            )

    return lifetime_price_dispatch


def get_lifetime_price_dispatch_timeseries(dispatch_price, economic_data):
    r"""
    Calculates the lifetime price dispatch for a timeseries.
    The dispatch_price can be a timeseries, eg. in case that there is an hourly pricing.
    .. math::

        lifetime\_price\_dispatch(t) = DISPATCH\_PRICE(t) \cdot ANNUITY\_FACTOR \forall t

    Parameters
    ----------
    dispatch_price: :class:`pandas.Series`
        Dispatch price as a timeseries (eg. electricity prices)

    economic_data: dict
        Dict of economic data

    Returns
    -------
    lifetime_price_dispatch: float
        Lifetime dispatch price that the asset will be updated with

    Notes
    -----
    Tested with
        - test_determine_lifetime_price_dispatch_as_timeseries()
        - test_get_lifetime_price_dispatch_timeseries()

    """

    lifetime_price_dispatch = dispatch_price.multiply(
        economic_data[ANNUITY_FACTOR][VALUE], fill_value=0
    )
    return lifetime_price_dispatch
