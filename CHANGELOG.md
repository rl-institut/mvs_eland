# Changelog
All notable changes to this project will be documented in this file.

The format is inspired from [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and the versioning aim to respect [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

Here is a template for new release sections

```
## [_._._] - 20XX-MM-DD

### Added
-
### Changed
-
### Removed
-
### Fixed
-
```

## [Unreleased]

### Added
- Warning for missing parameter when parsing inputs from epa to mvs (#656)
- New module `exceptions.py` in `multi_vector_simulator.utils` to gather custom MVS exceptions (#656)
- New argument for functions `E1.convert_demand_to_dataframe`, `F1.plot_timeseries`, `F2.ready_timeseries_plots` (#665)
- File .github/workflow/main.yml for github actions (#668)

### Changed
- Function `utils.compare_input_parameters_with_reference` accepts parameters as dict for json comparison (#656)
- Move A1 and C0 custom exceptions into `multi_vector_simulator.utils.exceptions.py` (#656)
- Adapt `E1.convert_demand_to_dataframe` for multiple sectors (#656)
- Improve the demands section of the autoreport: Divide the demand tables and plots sector-wise (#665)

### Removed
- File .travis.yml (#668)

### Fixed


## [0.5.2] - 2020-11-11

### Added
- Create function `utils.copy_inputs_template` to copy input_template from package data_files (#608)
- Create `MANIFEST.in` file (#608)
- Add entrypoint for `mvs_create_input_template` in `setup.py` (#608)
- Create script `prepare_package.py` to add data to package and build dist folder (#608)
- Five new KPI's added to E3: Onsite energy fraction, Onsite energy matching, Degree of autonomy, total_feedin_electricity_equivalent and internal generation (#624)
- Add definition of `renewable share of local generation` in RTD, `E3.add_renewable_share_of_local_generation` and pytests (#637)
- Add calculation of electricity equivalents in `E3.weighting_for_sector_coupled_kpi()` (#637)
- Add benchmark test for  the calculation of: `TOTAL_NON_RENEWABLE_GENERATION_IN_LES`, `TOTAL_RENEWABLE_GENERATION_IN_LES`, `TOTAL_NON_RENEWABLE_ENERGY_USE`, `TOTAL_RENEWABLE_ENERGY_USE`, `RENEWABLE_FACTOR`, `RENEWABLE_SHARE_OF_LOCAL_GENERATION` for one sector (#637)
- New constant variable: `DATA="data"` (#651)

### Changed
- Moved `get_nested_value`, `set_nested_value`, `split_nested_path` from `tests/test_sensitivity.py` to `src/multi_vector_simulator/utils/__init__.py` (#650)
- Rename PACKAGE_PATH to PACKAGE_DATA_PATH (#608)
- Update release protocol within `Contributing.md` (#608)
- Definition of renewable share (RES), now renewable factor (#637)
- Refactoring of `RENEWABLE_SHARE` into `RENEWABLE_FACTOR` and some functions in E3 (now `E3.add_total_renewable_and_non_renewable_energy_origin` and `E3.add_renewable_factor`) (#637)
- Rename: `Minimal renewable share constraint` to `Minimal renewable factor constraint` in all files (python, messages, RTD, json, tests, csv), so that this is in line with the definition and does not cause any confusion, explained in RTD (#637)
- Modify `B0_data_input_json.py` to read "input_timeseries" into `pandas.Series` from epa formated input json (#651)
- Modify `convert_mvs_params_to_epa` in `utils.data_parser` to convert `pandas.Series` back to "input_timeseries" (#651)

### Removed
- Variable `TEMPLATE_INPUT_PATH` (#608)
- Field `data_files` from `setup.py` (#608)

### Fixed
- Calculation of the renewable share relative taking into account energy carrier weighting (#637)

## [0.5.1 - 2020-11-10]

### Added
- `E-Land_Requirements.rst`: Official E-Land requirement list as well as progress on functional and non-functional requirements (#590)
- Add pytests for `E4.detect_excessive_excess_generation_in_bus()` (#591)
- Add pypi release to release protocol and update/simplify protocol (#601)
- Remove REPORT_PATH constant (#607)
- Add report assets and example simulation to package_data in `setup.py` (#607)
- Add a util function `copy_report_assets` to copy report asset to simulation output folder when user generates the report (#607)
- Add entrypoints for `mvs_tool` and `mvs_report` in `setup.py` (this can be simply typed directly in terminal) (#607)
- Updated readthedocs: Validation plan - Implemented tests and possible future ones (#593)
- Updated readthedocs: Gather the MVS parameters in a csv file and parse it to a sphinx RTD file (#620)
- Added more energy carriers and their weights to the list of already available energy carriers in constants.py (#621)
- Three new KPI's added to MVS_output.rst read the docs page: Onsite energy fraction, Onsite energy matching, Degree of autonomy (#609)
- New constant variables: `LOGS = "logs"`, `WARNINGS = "warnings"`, `ERRORS = "errors"` (#623)
- Tests for `D1.transformer()` (#596)
- Add economic model equations in readthedocs (#581)
- Add component model equations and energy balance adapted to sector coupled example (#581)
- Create function `F0.select_essential_results` to select main results out of `dict_values` (#625)
- Create mapping between EPA and MVS parameter names (#625)
- Create parameter parser from EPA to MVS (#625)
- Create parameter parser from MVS to EPA (#625)

### Changed
- Order of readthedocs content (#590)
- Make sure report can be generated even if figures are missing from simulation outputs (#607)
- Move the code located in `mvs_report.py` into `multi_vector_simulator.cli:report` (#607)
- Update installation steps in README and in RTD (#607)
- If default folder does not exist when code is executed, example simulation's inputs are used from package_data (#607)
- Rename `PATH_SIM_OUTPUT` to `ARG_PATH_SIM_OUTPUT` (#607)
- Rename function `A0.create_parser` to `A0.mvs_arg_parser` (#607)
- Update validation plan description in RTD (#593)
- Column headers of csv input files need to be unique amongst all files, info added to documentation (#602)
- Change mvs_eland to multi_vector_simulator in `docs/Code.rst` (#620)
- Change mvs_eland to multi-vector-simulator in `docs/*.rst` `urls (#620)
- Improved the description of assigning weightage to energy carriers in readthedocs (#619)
- Replaced the DSO sub-system image in Modelling Assumptions chapter of readthedocs (#622)
- Fixed several typos in readthedocs (#622)
- Move the function parse_log_messages to F0 and modify it to print log messages in results JSON file (#623)
- Move the function `parse_log_messages` from F1 to F0 and modify it to print log messages in results JSON file (#623)
- If `assets` folder is not found in package look in current folder for `report/assets` folder (#632)
- `D1.transformer_constant_efficiency_fix()` and `D1.transformer_constant_efficiency_optimize()`, as well as their tests to reassign attributes (#596)
- Move `retrieve_date_time_info` from C0 to B0 (#625)
- Conversion from dict to json drop the timeindexes from pandas.Series (#625)
- Conversion from json to dict allow to load a timeindex for pandas.Series (#625)
- Replace `==` by `is` in expression with `True`, `False` or `None` (#625)
- Remove unused `dict_values` argument of function `receive_timeseries_from_csv` (#625)
- Move the end of the function `receive_timeseries_from_csv` into `C0.compute_timeseries_properties()` (#625)
- Fix rendering issues with the PDF report and web app: Tables, ES graph sizing (#643)
- Improve the description of demands in the autoreport: Adapted section so that it applies to all vectors (#647)

### Removed
- Parameter label from input csv files; label is now set by filenames (for `project_data`, `economic_data`, `simulation_settings`) and column headers (for `energyConsumption`, `energyConversion`, `energyProduction`, `energyProviders`), special for storage: `filename` + `column header` (#602)
- Remove reference to git branch ID in the report (#607)

### Fixed
- RTD entry for defining parameters as timeseries (#597)
- Math equations of RTD in files `Model_Assumptions.rst` and `MVS_Output.rst` (#604)
- Repaired the broken links to input CSV files (#618)
- Outdated RTD info and mistakenly deleted sentence (#629)
- All `variable_costs`, `efficiency` and `nominal_value` of transformers on output flows. Before they were inconsistently assigned to input or output flows. (#596)
- Calculation of the renewable share relative taking into account energy carrier weighting (#637)

## [0.5.0] - 2020-10-05

### Added
- Instruction to install graphviz on windows in `docs/troubleshooting.rst` (#572)
- Benchmark test `test_benchmark_feature_parameters_as_timeseries` to ensure that parameters can always also be defined as a timeseries. Applied to `efficiency` of an energyConversion asset and `electricity_price` of an energyProduction asset (#542)
- Input files for benchmark tests `test_benchmark_feature_input_flows_as_list` (`Feature_input_flows_as_list`) and `test_benchmark_feature_output_flows_as_list` (`Feature_output_flows_as_list`), but not the benchmark assertions (#542)
- Error message if time series of non-dispatchable sources do not meet requirement: values betw. 0 and 1. (#498)
- Requirement for time series of non-dispatchable sources in readthedocs (#498)
- Provide a warning in case of excessive excess generation (#498)
- Pytests for `C0.add_maximum_cap()`, renamed function into `C0.process_maximum_cap_constraint()` (#498)
- Description of the inherited MVS limitations as well as the ones that can be addressed (#580)

### Changed
- Modify `setup.py` to upload the code as package on pypi.org (#570)
- Improve message when the `tests/test_input_folder_parameters.py` fails (#578)
- Modify PR template to precise to add assert message and link to example docstring 
- Update CONTRIBUTING to add a "Write test for your code" section before the "Run tests locally" one (#579)
- Modified readthedocs page describing the parameters of MVS (#479)
- Changed `E2.calculate_dispatch_expenditures()` so that it can process parameters defined as lists (#542)
- Rename `E4` to `E4_verification.py` (#498)
- Rename package name `mvs_eland` to `multi-vector-simulator` in `setup.py` (#587)
- Rename `src/mvs_eland` to `src/multi_vector_simulator` (#587)
- Rename repository from `mvs_eland` to `multi-vector-simulator` (#587)
- Refactor modules calls (`mvs_eland.` is replaced by `multi_vector_simulator.`) (#587)
- Update `README.md` and `CONTRIBUTING.md` replacing `mvs_eland` or `mvs-eland` by `multi-vector-simulator` (#587)

### Removed
- Remove unused function `mvs_eland.utils.get_version_info` (#587)

### Fixed
- Update the release protocol in `CONTRIBUTING.md` file (#576)
- Fix reading timeseries for parameters in `C0` (#542)
- Constraint for `optimizedAddCap` of non-dispatchable sources: multiply `maximumCap` by `max(timeseries(kWh/kWp))` to fix issue #446 (#562, #498)
-`timeseries_normalized` are calculated for all `timeseries` of non-dispatchable sources now (before only if `optimizeCap==True`) (#562, #498)
- Input files of benchmark test `Test_Constraints.test_benchmark_minimal_renewable_share_constraint()` (#498)

## [0.4.1] - 2020-09-21

### Added
- Evaluation of excess energy for each of the energy carriers and for the whole system. The excess per sector and their energy equivalent may currently be faulty (comp. issue #559) (#555)
- Debug messages for pytests: `C0`, `D2` (#555, #560)
- Labels on capacity barplot bars (#567)

### Changed
- `C1.total_demand_each_sector()` to `C1.total_demand_and_excess_each_sector()`, now also evaluating the excess energy flows (#555)
- `energyBusses` now is defined by: `LABEL, ASSET_LIST, ENERGY_VECTOR`, all functions using `energyBusses` now follow this nomenclature (#555)
- Energy excess sinks now also have parameter `ENERGY_VECTOR` (#555)
- `C0.define_sink` now always defines a sink that is capacity-optimized (#555)
- `D1.sink_dispatchable()`, renamed to `D1.sink_dispatchable_optimize()` now adds a capacity-optimized, dispatchable sink. (#555) 
- Simulation data `tests/inputs`: Oemof-solph results are not stored (#555)
- Change logging level of some messages from `logging.info` to `logging.debug` (#555)
- Move and rename json input files for D0 and D1 tests (`test_data_for_D0.json` to `tests/test_data/inputs_for_D0/mvs_config.json`, `test_data_for_D1.json` to `tests/test_data/inputs_for_D1/mvs_config.json`), add required parameters (#555) 
- Change requirements/test.txt: `black==19.10b0`, as otherwise there are incompatabilities (#555)
- `D2.prepare_constraint_minimal_renewable_share`, including logging messages and pytest (#560)
- Change the import path of the modules for automatic docstrings import in `docs/Code.rst` (#564)
- Fix the docstrings with math expressions (need to add `r` before the `"""` of the docstring
) (#564)
- Rename the function in F1 module `plot_flows` to `plot_instant_power` (#567)
- Change flow to power in the instanteous power figures (#567)
- `F1.plot_piecharts_of_costs()` now cites costs with currect currency and avoids decimal numbers (#561)

### Fixed
- `C1.check_feedin_tariff()` now also accepts `isinstance(diff, int)` (#552)
- Feed-in sinks of the DSOs now are capacity-optimized and can actually be used (#555)
- Incorrectly applied minimal renewable share criterion (#560)
- Pdf report generation (#566)
- Update fresh install instructions for developers (#565)
- Graphs of the report now use appropriate currency (#561)

## [0.4.0] - 2020-09-01

### Added
- Docstrings for E2 (#520)
- New constant variable: `SIMULATION_RESULTS="simulation_results"` (#520)
- Explicit calculation of replacement costs (`C2.get_replacement_costs()`), so that they can be used in `E2` for installed capacities and optimal additional capacities (#520)
- New constant variable: JSON_WITH_RESULTS="json_with_results.json" (#520)
- Benchmark test "Economic_KPI_C2_E2" to test economic evaluations in C2 and E2 (#520)
- Possibility to add an upper bound  on the number of days to display in a timeseries' plot (#526)
- Graph of the energy system model to the report (#528)
- Function to encode images into dash app's layout (#528)
- System KPI now printed in automatic report (section "Energy system key performance indicators"), draft (#525)
- Added units to system-wide cost KPI in excel and in report. Some of these changes might need to be reworked when elaborating on units for the report (#525)
- `References.rst` to the readthedocs, which should gather all the references of the MVS (#525)
- New system-wide KPI:
    - Demand per energy carrier, in original unit and electricity equivalent with `E3.total_demand_each_sector()` (#525)
    - Attributed cost per energy carrier, related to the its share in the total demand equivalent  with `E3.total_demand_each_sector()` (#525)
    - LCOE per energy carrier `E3.add_levelized_cost_of_energy_carriers()` (#525)
- Default values for energy carrier "Heat" for `DEFAULT_WEIGHTS_ENERGY_CARRIERS` with `{UNIT: "KWh_eleq/kWh_therm", VALUE: 1}`. This is still TBD, as there is no source for this ratio yet (#525)
- Default unit for energy carriers defined in `DEFAULT_WEIGHTS_ENERGY_CARRIERS`: ENERGY_CARRIER_UNIT. Might be used to define the units of flows and LCOE. (#525)
- New constant variables: TIMESERIES_TOTAL, TIMESERIES_AVERAGE, LOGFILE, RENEWABLE_SHARE, TOTAL_DEMAND, SUFFIX_ELECTRICITY_EQUIVALENT, ATTRIBUTED_COSTS, LCOeleq, DEGREE_OF_SECTOR_COUPLING (#525)
- New constant variable: OEMOF_BUSSES, MINIMAL_RENEWABLE_SHARE, CONSTRAINTS (#538)
- New required input csv: `constraints.csv` including possible constraints for the energy system. Added to all input folders. (#538)
- Added error message: New energy carriers always have to be added to `DEFAULT_WEIGHTS_ENERGY_CARRIERS` (`C0.check_if_energy_carrier_is_defined_in_DEFAULT_WEIGHTS_ENERGY_CARRIERS()`, applied to `ENERGY_VECTOR` and to fuel sources) (#538)
- Added minimal renewable share contraint though  `D2.constraint_minimal_renewable_share()` and added description of the constraint in `Model_Assumptions.rst` (#538)
- Benchmark test for minimal renewable share constraint (#538)
- Benchmark test `test_benchmark_AFG_grid_heatpump_heat` for a sector-coupled energy system, including electricity and heat, with a heat pump and an energy price as time series (#524)
- Benchmark test descriptions for `test_benchmark_simple_scenarios.py` (#524)
- Create `src/mvs_eland/utils` subpackage (contains `constants.py`, `constants_json_string.py
`, `constants_output.py` (#501)


### Changed
- Changed structure for `E2.get_cost()` and complete disaggregation of the formulas used in it (#520)
- Added pytest for many `E2` functions (#520)
- Changed and added pytests in for `C2` (#520)
- All energyProviders that have key `FILENAME` (and, therefore, a timeseries), are now of `DISPATCHABILITY = False`(#520)
- Changed structure of `E2.lcoe_assets()` so that each asset has a defined LCOE_ASSET. If `sum(FLOW)==0` of an asset, the LCOE_ASSET (utilization LCOE) is defined to be 0 (#520)
- Color lists for plots are provided by user and are not hard coded anymore (#527)
- Replace function `F1.draw_graph` by the class `F1.ESGraphRenderer` and use `graphviz` instead of
 `networkx` to draw the graph of the energy system model (#528) 
- Rename variable `PLOTS_NX` to `PLOTS_ES` (#528)
- Changed `requirements.txt` (removing and updating dependencies) (#528)
- A png of the energy system model graph is only saved if either `-png` or `-pdf` options are chosen (#530)
- Accepting string "TRUE"/"FALSE" now for boolean parameters (#534)
- Order of pages in the readthedocs.io (#525)
- Reactivated KPI: Renewable share. Updated pytests (#525)
- Extended `DEFAULT_WEIGHTS_ENERGY_CARRIERS` by `Diesel` and `Gas`, added explaination in `Model_Assumptions.rs` (#538)
- Create `dict_model` with constant variables in `D0` and update in `D1` (#538)
- Separate the installation of the packages needed for the report generation from the mvs
 simulation (#501)
- Move all source files in `src/mvs_eland` (#501)
- Move the content of the previous `src/utils.py` module to  `src/mvs_eland/utils/__init__.py` (#501)
- Rename `tests/constants.py` --> `tests/_constants.py` (#501)
- Refactor modules calls (mostly `src.` is replaced by `mvs_eland.`) (#501)
- Move `mvs_eland_tool` folder's content in `src/mvs_eland` (#501)
- Gather all requirements files in a `requirements` folder and read the requirement from there for `setup.py` (#501)
- Update `install_requires` and `extra_requires` in `setup.py` (#501)

### Removed
- `E2.add_costs_and_total`() (#520)
- Calculation of energy expenditures using `price` (#520)
- Function `F1.plot_input_timeseries` which is based on `matplotlib` (#527)
- Dependency to `matplotlib` (#528)
- Remove `STORE_NX_GRAPH` and `DISPLAY_NX_GRAPH` variables (#530)
- Remove `tests/__init__.py` (#501)
- Delete `mvs_eland_tool` folder (#501)

### Fixed
- Calculation of `cost_upfront` required a multiplication (#520)
- Fixed `E2.convert_components_to_dataframe()`, Key error (#520)
- Fixed `F1.extract_plot_data_and_title()`, Key error (#520)
- Fixed hard-coded energy vector of ENERGY_PRODUCTION units in E1.convert_components_to_dataframe(#520)
- Generating report for multiple sectors (#534)
- Fixed hard-coded energy vector of `ENERGY_PRODUCTION` units in `E1.convert_components_to_dataframe` (#520)
- Fixed parsing issue in `A1.conversion()`, incl. pytest (#538)
- Quick fix to read a timeseries for `"price"` in `C0.define_source()` (#524)
- Fix `C1.check_feedin_tariff()`: Now also applyable to timeseries of feed-in tariff or electricity prices (#524)
- Add a warning message if the timeseries of demands or resources are empty (#543)
- Fix failing KPI test (due to newer pandas version) (#501)

## [0.3.3] - 2020-08-19

### Added
- Also components that have no investment costs now have a value (of 0) for COST_INVESTMENT and COST_UPFRONT (#493)
- Display error message when feed-in tariff > electricity price of any  asset in 'energyProvider.csv'. (#497)
- Added pie plots created using Plotly library to the auto-report (#482) 
- Added functions to `F2_autoreport.py` that save the images of plots generated using Plotly to `MVS_outputs` folder as `.png` (#499)
- Inserted docstrings in the definitions of all the functions in `F2_autoreport.py` (#505)
- Functions in F1 to create plotly static `.png` files (#512)
- New argument for MVS execution: `-png` to store plotly graphs to file (#512)
- Benchmark test for peak demand pricing for grid and battery case (#510)
- Logging error message if a cell is left empty for a parameter in the csvs (see `A1`) (#492)
- Logging error message if a bus connects less then three assets including the excess sink, as in that case the energy system model is likely to be incomplete (`C1.check_for_sufficient_assets_on_busses()`) (#492)

### Changed
- Move and rename json converter and parser to B0 module (#464)
- Modified json converter to avoid stringifying special types such as pandas.Dataframes (#464)
- Changed the font family used in the plots in F2_autoreport.py and changed the wording of some comments (#496)
- Changed styling of plots, mainly how legends appear in the PDF report (#482) 
- Move and rename json converter and parser to B0 module (#464)
- Modified json converter to avoid stringifying special types such as pandas.Dataframes (#464)
- Changed the font family used in the plots in F2_autoreport.py and changed the wording of some comments (#496)
- Replaced parameter strings by variables (#500)
- Changed the font family used in the plots in F2_autoreport.py and changed the wording of some comments (#496)
- Moved function `C0.determine_lifetime_price_dispatch()` to C2 with all its sub-functions.  (#495)
- Changed calculation of `LIFETIME_PRICE_DISPATCH` for lists and pd.Series (see dosctrings of `C2.get_lifetime_price_dispatch_list`, `C2.get_lifetime_price_dispatch_timeseries`) (#495)
- Changed dostring format in `C2` to numpy (#495)
- Deactivated function `C2.fuel_price_present_value` as it is not used and TBD (#495)
- Modified the doc-strings in the definitions of some functions to abide by the formatting rules of numpy doc-strings (#505)
- Suppressed the log messages of the Flask server (for report webapp) (#509) 
- Move bulk data preparation code for report from F2 into E1 and F1 modules and into functions (#511, #512)
- F2 now calls functions from F1 to prepare the figures of the report (#512)
- Dispatchable (fuel) sources can now be defined by adding a column to the `energyProduction.csv` and setting `file_name==None` (#492)
- Updated `Model_Assumptions.rst`: Minimal description of dispatchable fuel sources (#492)
- `tests/inputs` energyAssets are updated (#492)
- Fixed test_benchmark_AD_grid_diesel() - now this one tests fuel source and diesel at once (#492)

### Removed
- Functions to generate plots with matplotlib in F1 (#512)
- Many tests that checked if matplot lib plots were stored to file, not replaced by new tests for storing plotly graphs to file (#512)

### Fixed
- Image path for readthedocs (Model_Assumpation.rst) (#492)

## [0.3.2] 2020-08-04

### Added
- `Model_Assumptions` added, including outline for component models, bulletpoints on limitations, energyProviders and peak demand pricing model. (#454)

### Changed
- Definition of busses from assets: Now all INFLOW_DIRECTION / OUTFLOW_DIRECTION are translated into ENERGY_BUSSES (#454, #387)
- An excess sink is created for each and every bus (#454)
- Splitting functions in `C0` and adding tests for them: `C0.define_sink()`, `C0.define_source()` and `C0.define_dso_sinks_and_sources()` (#454)
- Instead of defining multiple DSO sources for modelling peak demand pricing, now a single source is defined and another level added with transformers that, with an availability limited to a peak demand pricing period, only represent the costs of peak demand pricing in the specific period. (#454)
- Moved function `C0.plot_input_timeseries()` to `F1.plot_input_timeseries()` (#454)
- Add required parameter "unit" to energyProviders.csv. Used for defining the units of the peak demand pricing transformer. (#454)
- Updated `F2` for new DSO/excess sink structure: DSO feedin and excess sink removal from demands now universal (#454)
- Replace `logging.warning` for dispatch price of sources in case of DSOs - this is now only an `logging.info`
- Added global variables for KPI connected to renewable energy use (TOTAL_RENEWABLE_GENERATION_IN_LES = "Total internal renewable generation", TOTAL_NON_RENEWABLE_GENERATION_IN_LES = "Total internal non-renewable generation", TOTAL_RENEWABLE_ENERGY_USE = "Total renewable energy use", TOTAL_NON_RENEWABLE_ENERGY_USE = "Total non-renewable energy use") (#454)
- Updated to disagregated `oemof-solph==0.4.1`, which required changing the `requirements.txt` as well as the usage of `oemof` within the MVS (#405)

### Removed
-

### Fixed
- Peak demand pricing feature (#454)


## [0.3.1] - 2020-07-30

### Added
- Release protocol in `CONTRIBUTING.md` file (#353)
- Custom heat demand profile generation (#371)
- Add custom solar thermal collector generation profile (#370)
- Input template folder for easy generation of new simulations (#374), later also for tests of the input folder
- Tests for ABE usecase (grid, PV, battery) (#385)
- Test to verify that input folders have all required parameters (#398)
- New `dict` `REQUIRED_MVS_PARAMETERS` to gather the required parameters from the csv or json
 input type (#398)
- `utils.py` module in `src` to gather the functions `find_input_folders` and `compare_input_parameters_with_reference` which can be used to find and validate input folders (#398)
- Code and test for checking for new parameters in csv and raising warning message if not defined (`A1.check_for_newly_added_parameters`). This then also adds a default value to the new parameter  (#384)
- Exception if an energyVector does not have internal generation or consumption from a DSO, and is only supplied by energy conversion from another sector: renewable share = 0. (#384)
- Tests for source components in D1 (#391)
- Option `-i` for `python mvs_report.py`, `python mvs_report.py -h` for help (#407)
- Pyppeteer package for OS X users in troubleshooting (#414)
- Add an enhancement to the auto-report by printing the log messages such as warnings and errors (#417)
- New `dict` `REQUIRED_JSON_PARAMETERS` to gather the required parameters from the json input files (#432)
- `.readthedocs.yml` configuration file (#435, #436)
- Calculation of levelized cost of energy (`LCOE_ASSET`) of each asset in E2 (#438)
- Tests for LCOE function in `test_E2_economics` (#438)
- Output of `scalars.xlsx`now also includes `INSTALLED_CAP` and `LCOE_ASSET`(#438)
- File `constants_output.py` to contain all keys included in `scalars.xlsx` (#453)
- Installation help for `pygraphviz` on Win10/64bit systems in `troubleshooting.rst` (#379)
- Add Plotly-based blots (line diagrams for energy flows and bar charts) to `F2_autoreport.py` (#439)
- LCOE_ASSET (Levelized Cost of Energy of Asset) explaination in KPI documentation (#458)
- Heat demand profiles with option of using monitored weather data (ambient temperature) at the use case UVtgV. note: file not provided so far (#474)
- Solar generation profiles with option of using monitored weather data (ambient temp, ghi, dhi) at the use case uvtgv. note: file not provided so far (#475)
- Benchmark test for simple case grid and diesel without test for fuel consumption (#386)
- Example docstring to readthedocs (#489)

### Changed
- Use selenium to print the automatic project report, `python mvs_report.py -h` for help (#356)
- Sort parameters in csv´s within the input folder (#374)
- Change relative folder path to absolute in tests files (#396)
- Replace all variables wacc, discount_factor and project_lifetime in the project (#383)
- Improve styling of the pdf report (#369)
- `LIST_OF_NEW_PARAMETERS` renamed `EXTRA_CSV_PARAMETERS` and moved from `A1` to `constants.py
` (#384)
- Order of parameters in `tests/inputs`, fixed missing parameters  (#384)
- Only a single output flow for sources (instead of multiple possible) as discussed in #149  (#391)
- Move `existing` parameter into Investment objects of D1 components (was before added to output flow) (#391)
- Use pyppeteers instead of selenium to emulate the webbrowser and print the pdf report
 automatically (#407)
- Update flowchart again (#409)
- Label of storage components (storage capacity, input power, output power) will by default be redefined to the name of the storage and this component (#415)
- Version number and date is only to be edited in one file (#419)
- Add `ìnputs` folder to `.gitignore` (#401)
- Change the calculation of the residual value for specific capex in C2 and test_C2 (#289, #247, PR #431): Now the present value of the residual value is considered
- Explicitly return the dataframe with parameters value in function
 `check_for_newly_added_parameter` (#428)
- Rename function `check_for_newly_added_parameter` in `check_for_official_extra_parameters` (#428)
- Add `ìnputs` folder to `.gitignore` (#401)
- Readthedocs links to simple scenario `tests/inputs` (#420)
- Adapt and add logging messages for components added to the model in D1 (#429)
- Moved list of keys to be printed in `scalars.xlsx` to `constants_output.py` (#453)
- Renamed `"peak_flow"` to `PEAK_FLOW` and `"average_flow"` to `AVERAGE_FLOW` (#453)
- Changed function `E2.lcoe_asset()` and its tests, now processes one asset at a time (#453)
- Added arguments ``-f`, `-log`, `warning`` to all `parse_args` and `main()` in `tests` (#456)
- File `Developing.rst` with new description of tests and conventions (#456)
- Added a `setup_class` (remove dir) to `test_B0.TestTemporaryJsonFileDisposal` (#379)
- Created function to read version number and date from file instead of importing it from module
 (#463)
- Fixed `E0.store_results_matrix()`, now available types: `str`, `bool`, `None`, dict (with key VALUE), else (`int`/`float`). If KPI not in asset, no value is attributed. Added test for function (#468, #470)
- Fixed `main()` calls in `test_F1_plotting.py` (#468)
- Added `pyppdf==0.0.12` to `requirements.txt` (#473)
- Tests for A0: Now new dirs are only created if not existant
- Function `A0.check_output_folder()`, now after `shutil.rmtree` we still `try-except os.mkdirs`, this fixes local issues with `FileExistsError`.  (#474)
- Added `pyppdf==0.0.12` to `requirements.txt` (#473)

### Removed
- Selenium to print the automatic project report for help (#407)
- `MaximumCap` from list of required parameters for `energyStorage` assets (#415)
- `inputs` folder (#401)
- `tests/test_benchmark.py` module (#401)
- Outdated table of tests of MVS `docs/tables/table_tests.csv` (#456)
- Removed function `C0.complete_missing_cost_data()` as this should be covered by A1 for csv files (#379)
- Old plots in `F2_autoreport.py` generated with matplotlib (#439)
- Parameter `restore_from_oemof_file` from all files (inputs, tests) (#483)
- Deleted columns from `fixcost.csv` as this is currently not used (#362)

### Fixed
- Bug connected to global variables (#356)
- Duplicate of timeseries files (#388)
- Warnings from local readthedocs compilation (#426)
- Bug on local install (#437)
- Input folder `tests/inputs` with simple example scenario (#420)
- Description of storage efficiency in readthedocs (#457)
- MVS can now be run with argument `-pdf` (fix pyppeteer issue) (#473)
- Adapted benchmark tests input folders to template (#386)
- Local failing pytests (`FileExistsError`) on Ubuntu and Win10 (#474, #483)
- 9 Warnings due to excess parameter `restore_from_oemof_file` (#483)

## [0.3.0] - 2020-06-08

### Added
- Test for re-running a simulation with `json_input_processed.json` file (#343)

### Changed
- Test input files (#343)
- All parameters of the json/csv input files are now defined by constant variables (i.e, `CRATE="crate"` instead of string `"crate"`) (#346)
- Use `is` instead of `==` in if clauses for True, False and None (#346)
- Categorize constants in `constants_json_strings.py` (#347)
- Renaming CAPEX_FIX = "capex_fix" into COST_DEVELOPMENT = "development_costs" (#347, #350)
- Renaming CAPEX_VAR = "capex_var" into SPECIFIC_COST = "specific_costs" (#347, #350)
- Renaming OPEX_FIX = "opex_fix" into SPECIFIC_COST_OM = "specific_costs_om" (#347, #350)
- Renaming OPEX_VAR = "opex_var" into PRICE_DISPATCH = "dispatch_price" (#347, #350)
- Change last strings into global constants in "constants_json_strings.py" (#349)
- Autoreport now refers to actual project and scenario name + ID (#349)


## [0.2.1] - 2020-05-28

### Added
- Tests for the module B0 (#140, #255)
- Tests for the module A1 (#141)
- Tests for the module E3 (#143)
- Tests for the module F0 (#142, #304, #335)
- Some tests for E2 (#144)
- Tests function names for E1 (#145)
- Tests for the module E0 (#146)
- Tests for module D2 (#147)
- Some tests for module C0 (#148)
- Tests for the module D1 (still - partly - open: transformers, sources. finished: sinks, storages, other functions) (#149)
- Tests for the module D0 (#150)
- Tests for module C2 (#151)
- Tests for the module C1 (only used function) (#152)
- Tests for module F1 (#157, #297, #284)
- Pull request template (#198)
- Issue template (#212)
- File `troubleshooting.rst` to readthedocs (#229)
- File `simulating_with_the_mvs.rst` to readthedocs: How to use the input files (csv/json) (#130), how to create an own simulation/project
tipps for module building, and hint that units in the MVS are not checked (#229)
- Images for `simulating_with_the_mvs.rst`: images/energy_system.png, images/energy_system_model
.png, images/folder_structure_inputs.png (#229)
- Tables for `simulating_with_the_mvs.rst`: files_to_be_displayed/example_multiple_inputs_energyConversion.csv
, files_to_be_displayed/example_scalar_as_timeseries_energyConversion.csv (#229)
- Benchmark test for csv inputs (#254)
- Benchmark test with only PV and grid (#258)
- Module F2 for auto-reporting results of MVS simulation (#232)
- Json entries including paths to all plotted graphs (#232)
- Technical parameters: Energy flows (aggregated) per asset, Renewable share (#223, #257)
- Save network graph as png to output folder if new parameter `store_nx_graph` is true (#242)
- Tests for storage for the module A1 (#299)
- Benchmark test with only battery and grid (#302)
- Flowchart and relative description (#305)
- Reference to license (#305)
- Description of validation scheme into readthedocs (#306)
- Possibility to save the report generated in F2 as a pdf (#284)
- Possibility to run benchmark tests selectively and make sure they are all run on master branch
 (#320)
- Possibility to deploy the report of the results in a browser (#323)
- A main() function to be used by a server which only accepts json variable and returns json
 variable (not saving to a file) (#327)
- Add information about the feature to view the web app and generate PDF of the automatic report to readthedocs (#283)

### Changed
- Default input files from "inputs": Changed some parameters (#143)
- Moved some functions between F0 and F1, rearranged functions in F1 (#157)
- Shore power randomization improved + amount of available docks can be chosen (#202)
- Update kwargs of main func in docstring and in documentation (#208)
- `troubleshooting.rst`: Added help for `pygraphviz` (#218), `xlrd` (#11), `json.decoder.JSONDecodeError` (#206)
- FileNotFoundError messages in A0 (#227)
- Update json file `mvs_config.json`: Default with no peak demand pricing. Replace string "False" by boolean `false`. Remove depreciated parameters from `simulation_settings`(`input_file_name`, `overwrite`, `path_input_file`, `path_input_folder`, `path_input_sequences`, `path_output_folder`, `path_output_folder_inputs`) (#234)
- Renamed `plot_nx_graph` to `display_nx_graph` and added `store_nx_graph` (#242)
- Variables `required_files_list` and `ALLOWED_FILES` have been replaced by `REQUIRED_FILES` (#251)
- The columns of the storage_xx files are renamed and the specific parameters for each column are
 checked in A1 (#259)
- Possibility to move the json file after reading it (useful if json file created from csv files
) (#255)
- Call timeseries plot function for each bus (#278)
- The input from the csv files produce the same json than the json file (#286)
- Rename "storage" parameter in A1 and tests_A1 to "asset_is_a_storage" (#300)
- Serialize the DataFrame and arrays into the json_with_results.json (#304)
- Convert serialized DataFrame and arrays back into these types in the B0.load_json function
 (#304, #322, #326)
- Move the CSS styling code to a style sheet (#317)
- Change the input data for creating the dataframes for generating the optimization and costs' tables from xlsx file to json (#317) 
- Rename mvs_eland_tool/mvs_eland_tool.py --> mvs_eland_tool/local_deploy.py (#327)
- Now main (local use) and run_simulation (server use) are available in mvs_eland_tool package
  (#327)

 
### Removed
- Removed parameter `oemof_file_name` from `simulation_settings.csv`, as well as from all input
 files etc. The name is hardcoded now (#150)

### Fixed
- Fix naming error for storages (#166)
- Fix json file (#203)
- Delete duplicated entry of `plot_nx_graph` from json file (#209)
- Rename "boolean" to "bool" in example json file (#214)
- Fix searching for dict key "input_bus_name" (#210) and using input_name instead of output_name (#219)
- Fix plotting error in F1, plot only if Data frame is not empty (#230, #234)
- Benchmark test that the simulation is running with default settings (#254)
- Fix specific parameters for each storage column (#259)
- Overwrite local results when running through brenchmark tests (#260)
- Allow more than one separator for csv files(#263)
- Fix plotting pie chart for costs, if statement added if no costs are available (#267)
- Fix long label resulting from total project costs (#270)
- Bug when the output path had contained an unexisting folder within an unexisting folder it
 would return an error (#278)
- Display SOC (#278)
- Automatic update of the test coverage with coveralls.io (#307)
- Logging message for maximumCap value (#310)
- Create_app function in F0 for standalone execution (#317)
- Crashing evaluation when `evaluated_period < 365/peak_demand_pricing_periods` by raising an
 error (#331) 

## [0.2.0] - 2020-03-13

### Added
- Readthedocs documentation for input parameters (#128)
- Doctring of module A0 (#138)
- Constants in `src/constants.py` (#153, #154)
- Readthedocs documentation for installation (#162)
- Plotting an networkx graph can now be turned of/on via "plot_nx_graph" in simulation_settings (#172)
- Plot all timeseries used as input data (#171)
- Integrate new parameter maximumCap as nominal value for energyProduction assets, ie. PV or wind plants (#125 )
- Integrate new parameter maximumCap as nominal value for storage assets and transformers (PR #243, comp. issue #125)

### Changed
- Give priority from kwargs on command line arguments (#112, #138)
- Docstrings of module A1 (#113)
- Changed keyword argument to positional argument for `create_input_json` function (#113)
- function `get_user_inputs` renamed `process_user_arguments` (#138)
- Tests for the module A0 (#138)
- Terminal commands (#135)
- PR request template (open/done/not applicable) (#205)
- URL of coverall badge (#265) 
- Function converting json to dict (#142)

### Removed
- Function welcome from module A0 (#138)
- Parameters `input_file_name`, `overwrite`, `path_input_file`, `path_input_folder`, `path_input_sequences`, `path_output_folder`, `path_output_folder_inputs` from `simulation_settings.csv` (#178)

### Fixed
- Input directory of csv files specified by user is handed to `load_data_from_csv.create_input_json()` (#112)
- \#111 & \#114 fix user choice of output folder via command line arguments(#115)
- Demand is no longer aggregated across sectors when processing/plotting in E1 (#169)
- Optimized storage capacities are printed into results matrix (#188)
- Sector diagrams now also include SOC diagrams (#189)
- Sources can now have variable costs (#173)
- \#182 Boolean simulation settings now also take affect
- Demand is no longer aggregated across sectors when processing/plotting in E1 (#169)

## [0.1.1] -2020-01-30

### Added
- test for running the main function (#109)
- the user can run the tool simply with `python mvs_tool.py` (#109)
### Fixed
- \#108 (#109)


## [0.1.0] - 2020-01-29

### Added
- tests for the A0 module (#87)
- badge for coveralls.io (#90)
- tests for the parsing of arguments (#97)
- exceptions for missing input file/folder (#98)
### Changed 
- removed unused class structure in all modules, execution stay the same (#86)
- link to build for this repository instead of previous one (#95)
- use argparser to parse the arguments from command line (#97)
- the full path of input folder containing csv is now required (#98)
### Removed
- argument parsing using sys.argv (#97)

## [0.0.3] - 2020-01-22

### Added
- LICENSE.md with GPL v2.0 (#38, smartie2076)
- folder "docs" and content to generate readthedocs (#39, smartie2076)
- Started readthedocs homepage (not working): https://readthedocs.org/projects/mvs-eland/ (#39, smartie2076, #57, Bachibouzouk)
- new feature to create the input json file from a collection of csv files (@Piranias)
- new module added: A1_csv_to_json.py (@Piranias)
- Badges for build and docs (#70, Bachibouzouk)
- Setup file (#72, Bachibouzouk)
- Parameters can now be a list of values, eg. efficiencies for two busses or multiple input/output vectors (#52, @marc-juanpera) 
- Parameters can now be a timeseries (eg. efficiency of a converter, electricity prices) (#37, #82, @marc-juanpera) 
- Parameters can now be defined as a list as well as as a timeseries (#52,#82, @marc-juanpera) 

### Changed
- requirements.txt only includes packages needed for users of MVS (#39, smartie2076)
- test_requirements.txt includes packages used by developers of MVS (#39, smartie2076)
- CONTRIBUTING: Now with read the docs (@smartie2076)
- README: Now with contextualization of MVS, setup & installation, utilization of and contributing to MVS (#47, smartie2076)
- directory structure of input/ (#49 @Piranias)
- json data structure reduced to 2 (main) levels: goup and asset (#49 @smartie2076)
- logging now stores into appropriate logfile (@smartie2076)
- change code_folder to src (#80)

### Removed
- Output files excluded from repro  (@smartie2076)

## [0.0.2] - 2019-11-25

### Added
- Introduced test for correct code formatting (blacks, closed issue #31, #18)
- Now unlimited number of busses possible
- Now with monthly peak demand pricing 
- Two test json files
- Files to create wiki page "Exemplary Workflow"

### Changed
- Introduced new code structure (folder "code") and updated relative import paths (closed #17)
- Introduced (basic) plots of optimized capacities and costs (addresses issue #29)
- CONTRIBUTING
- CHANGELOG
- Tests and travis file
- requirements.txt

### Removed
- Excel input file
- Python files to read from excel

## [0.0.1] - 2019-10-14

### Added
- CONTRIBUTING (#8)
- CHANGELOG (#8)
- Tests (#8, #10)

### Changed
- relative imports (#10)
- moved `mvs_eland_tool`'s content in a function (#10)

### Removed
- yet another thing
