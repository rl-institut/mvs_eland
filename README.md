# MVS - Multi-Vector Simulator of the E-Land toolbox

[![Documentation Status](https://readthedocs.org/projects/multi-vector-simulator/badge/?version=latest)](https://multi-vector-simulator.readthedocs.io/en/latest/?badge=latest)
![CI](https://github.com/rl-institut/multi-vector-simulator/workflows/CI/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/rl-institut/multi-vector-simulator/badge.svg)](https://coveralls.io/github/rl-institut/multi-vector-simulator)

Deprecated: [![Build Status](https://travis-ci.com/rl-institut/mvs_eland.svg?branch=dev)](https://travis-ci.com/rl-institut/mvs_eland)

Rights: [Reiner Lemoine Institut (Berlin)](https://reiner-lemoine-institut.de/)

The multi-vector simulator (MVS) allows the evaluation of local sector-coupled energy systems that include the energy carriers electricity, heat and/or gas. The MVS has three main features:

- Analysis of an energy system model, which can be defined from csv or json files, including its
 costs and performance parameters.
 - Near-future investments into power generation and storage assets can be optimized aiming at
  least-cost supply of electricity and heat.
 - Future energy supply scenarios that integrate emerging technologies helping to meet sustainability goals and decrease adverse climate effects can be evaluated, e.g. through high renewable energy shares or sector-coupling technologies.

The tool is being developed within the scope of the H2020 project E-LAND (Integrated multi-vector management system for Energy isLANDs, project homepage [HERE](https://elandh2020.eu/)). A graphical user interface for the MVS will be integrated.

*Latest release*
Check the [latest release](https://github.com/rl-institut/multi-vector-simulator/releases/latest). Please check the [CHANGELOG.md](https://github.com/rl-institut/multi-vector-simulator/blob/master/CHANGELOG.md) for past updates and changes.

*Disclaimer*
As the MVS is still under development, changes might still occur in the code as well as code
 structure. If you want to try the MVS, please make sure to check this project regularly.

For advanced programmers: You can also use the `dev` branch that includes the latest updates and
 changes. You find the changelog [HERE](https://github.com/rl-institut/multi-vector-simulator/blob/dev/CHANGELOG.md).

# Getting started

If you are interested to try out the code, please feel free to do so! In case that you are planning to use it for a specific or a larger-scale project, we would be very happy if you would get in contact with us, eg. via issue. Maybe you have ideas that can help the MVS move forward? Maybe you noticed a bug that we can resolve?

We are still working on including a readthedocs for the MVS. Some information on this tool and code is already available [here](https://multi-vector-simulator.readthedocs.io/en/stable/) (stable version, latest developments [here](https://multi-vector-simulator.readthedocs.io/en/latest/)).

## Setup and installation

To set up the MVS, follow the steps below:

* If python3 is not pre-installed: Install miniconda (for python 3.7: https://docs.conda.io/en/latest/miniconda.html)

* Open Anaconda prompt (or other software as Pycharm) to create and activate a virtual environment

    `conda create -n [your_env_name] python=3.6`
    `activate [your env_name]`


* Install the latest [MVS release](https://github.com/rl-institut/multi-vector-simulator/releases)

    `pip install multi-vector-simulator`


* Download the [cbc-solver](https://projects.coin-or.org/Cbc) into your system from https://ampl.com/dl/open/cbc/ and integrate it in your system, ie. unzip, place into chosen path, add path to your system variables  (Windows: “System Properties” -->”Advanced”--> “Environment Variables”, requires admin-rights). 

    You can also follow the [steps](https://oemof.readthedocs.io/en/latest/installation_and_setup.html) from the oemof setup instructions


* Test if that the cbc solver is properly installed by typing

    `oemof_installation_test`

    You should at least get a confirmation that the cbc solver is working

    ```
    *****************************
    Solver installed with oemof:

    cbc: working
    glpk: not working
    gurobi: not working
    cplex: not working

    *****************************
    oemof successfully installed.
    *****************************

    ```

* Test if the MVS installation was successful by executing

    `mvs_tool`

This should create a folder `MVS_outputs` with the example simulation's results
    
## Using the MVS

To run the MVS with custom inputs you have several options:


##### Use the command line

Edit the json input file (or csv files) and run

    `mvs_tool -i path_input_folder -ext json -o path_output_folder`

With 
`path_input_folder`: path to folder with input data,

`ext`: json for using a json file and csv for using csv files

and `path_output_folder`: path of the folder where simulation results should be stored.

For more information about the possible command lines options

    `mvs_tool -h`

##### Use the `main()` function

You can also execute the mvs within a script, for this you need to import

```
from multi_vector_simulator.cli import main

```
The possible arguments to this functions are:
- `overwrite` (bool): Determines whether to replace existing results in `path_output_folder` with the results of the current simulation (True) or not (False) (Command line "-f"). Default: `False`.
- `input_type` (str): Defines whether the input is taken from the `mvs_config.json` file ("json") or from csv files ('csv') located within <path_input_folder>/csv_elements/ (Command line "-ext"). Default: `json`.
- `path_input_folder` (str): The path to the directory where the input CSVs/JSON files are located. Default: `inputs/` (Command line "-i").
- `path_output_folder` (str): The path to the directory where the results of the simulation such as the plots, time series, results JSON files are saved by MVS E-Lands (Command line "-o"). Default: `MVS_outputs/`.
- `display_output` (str): Sets the level of displayed logging messages. Options: "debug", "info", "warning", "error". Default: "info".
- `lp_file_output` (bool): Specifies whether linear equation system generated is saved as lp file. Default: False.
- `pdf_report` (bool): Specify whether pdf report of the simulation's results is generated or not (Command line "-pdf"). Default: False.
- `save_png` (bool): Specify whether png figures with the simulation's results are generated or not (Command line "-png"). Default: False.


Edit the csv files (or, for devs, the json file) and run the `main()` function. The following `kwargs` are possible:


##### Default settings

If you execute the `mvs_tool` command in a path where there is a folder named `inputs` (you can use the folder
`input_template` for inspiration) this folder will be taken as default input folder and you can simply run

    `mvs_tool`

A default output folder will be created, if you run the same simulation several time you would
 have to either overwrite the existing output file with

    `mvs_tool -f`

Or provide another output folder's path

    `mvs_tool -o <path_to_other_output_folder>`

## Generate pdf report or an app in your browser to visualise the results of the simulation

To use the report feature you need to install extra dependencies first

    `pip install multi-vector-simulator[report]`

### Generate a report after running a simulation

Use the option `-pdf` in the command line  `mvs_tool` to generate a pdf report in the
 simulation's output folder (by default in `MVS_outputs/report/simulation_report.pdf`):

    `mvs_tool -pdf`

### Generate only the figures of a simulation's results

Use the option `-png` in the command line  `mvs_tool` to generate png figures of the results in the
 simulation's output folder (by default in `MVS_outputs/`):

    `mvs_tool -png`


### post-processing
To generate a report of the simulation's results, run the following command **after** a simulation
 generated an output folder:
 
    `mvs_report -i path_simulation_output_folder -o path_pdf_report`

where `path_simulation_output_folder` should link to the folder of your simulation's output, or directly to a json file (default `MVS_outputs/json_input_processed.json`)
and `path_pdf_report` is the path where the report should be saved as a pdf file.


The report should appear in your browser (at http://127.0.0.1:8050) as an interactive Plotly Dash app.

You can then print the report via your browser print functionality (ctrl+p), however the layout of
 the pdf report is only well optimized for chrome or chromimum browser.

It is also possible to automatically save the report as pdf by using the option `-pdf`

    `mvs_report -i path_simulation_output_folder -pdf`

By default, it will save the report in a `report` folder within your simulation's output folder default (`MVS_outputs/report/`).
See `mvs_report.py -h` for more information about possible options. The css and images used to make the report pretty should be located under
`report/assets`.

## Contributing

If you want to contribute to this project, please read [CONTRIBUTING.md](https://github.com/rl-institut/multi-vector-simulator/blob/dev/CONTRIBUTING.md). For less experienced github users we propose a workflow [HERE](https://github.com/rl-institut/multi-vector-simulator/wiki/Examplary-Workflow).
