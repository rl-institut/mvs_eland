# This script generates a report of the simulation automatically, with all the important data.

import base64
import os

# Imports for generating pdf automatically
import threading
import time
import webbrowser

# Importing necessary packages
import dash
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objs as go
import plotly.express as px
import dash_table
import folium
import git
import pandas as pd
import reverse_geocoder as rg
import staticmap
import asyncio
import textwrap
import copy

import pyppdf.patch_pyppeteer
from pyppeteer import launch

# This removes extensive logging in the console for pyppeteer.
import logging

pyppeteer_level = logging.WARNING
logging.getLogger("pyppeteer").setLevel(pyppeteer_level)

# This removes extensive logging in the console for the dash app (it runs on Flask server)
flask_log = logging.getLogger("werkzeug")
flask_log.setLevel(logging.ERROR)

from src.constants import (
    PATH_OUTPUT_FOLDER,
    REPO_PATH,
    REPORT_PATH,
    OUTPUT_FOLDER,
    INPUTS_COPY,
    CSV_ELEMENTS,
    ECONOMIC_DATA,
    PROJECT_DATA,
)
from src.constants_json_strings import (
    LABEL,
    SECTORS,
    VALUE,
    SIMULATION_SETTINGS,
    EVALUATED_PERIOD,
    START_DATE,
    TIMESTEP,
    TOTAL_FLOW,
    ANNUAL_TOTAL_FLOW,
    KPI,
    KPI_SCALAR_MATRIX,
    PROJECT_NAME,
    PROJECT_ID,
    SCENARIO_NAME,
    SCENARIO_ID,
    PEAK_FLOW,
    AVERAGE_FLOW,
)

from src.E1_process_results import (
    convert_demand_to_dataframe,
    convert_components_to_dataframe,
    convert_scalar_matrix_to_dataframe,
    convert_cost_matrix_to_dataframe,
    convert_kpi_matrix_to_dataframe,
)
from src.F1_plotting import (
    extract_plot_data_and_title,
    convert_plot_data_to_dataframe,
    parse_simulation_log,
    create_plotly_line_fig,
    create_plotly_capacities_fig,
    create_plotly_flow_fig,
)

# TODO link this to the version and date number @Bachibouzouk
from src.utils import get_version_info

version_num, version_date = get_version_info()

OUTPUT_FOLDER = os.path.join(REPO_PATH, OUTPUT_FOLDER)
CSV_FOLDER = os.path.join(REPO_PATH, OUTPUT_FOLDER, INPUTS_COPY, CSV_ELEMENTS)


async def _print_pdf_from_chrome(path_pdf_report):
    r"""
    This function generates the PDF report from the web app rendered on a Chromimum-based browser.

    Parameters
    ----------
    path_pdf_report: os.path
        Path and filename to which the pdf report should be stored
        Default: Default: os.path.join(OUTPUT_FOLDER, "out.pdf")

    Returns
    -------
    Does not return anything, but saves a PDF file in file path provided by the user.
    """

    browser = await launch()
    page = await browser.newPage()
    await page.goto("http://127.0.0.1:8050", {"waitUntil": "networkidle0"})
    await page.waitForSelector("#main-div")
    await page.pdf({"path": path_pdf_report, "format": "A4", "printBackground": True})
    await browser.close()
    print("*" * 10)
    print("The report was saved under {}".format(path_pdf_report))
    print("You can now quit with ctlr+c")
    print("*" * 10)


def print_pdf(app=None, path_pdf_report=os.path.join(OUTPUT_FOLDER, "out.pdf")):
    r"""Runs the dash app in a thread and print a pdf before exiting

    Parameters
    ----------
    app: instance of the Dash class of the dash library
        Default: None

    path_pdf_report: str
        Path where the pdf report should be saved.

    Returns
    -------
    None, but saves a pdf printout of the provided app under the provided path
    """

    # if an app handle is provided, serve it locally in a separated thread
    if app is not None:
        td = threading.Thread(target=app.run_server)
        td.daemon = True
        td.start()

    # Emulates a webdriver
    asyncio.get_event_loop().run_until_complete(_print_pdf_from_chrome(path_pdf_report))

    if app is not None:
        td.join(20)


def open_in_browser(app, timeout=600):
    r"""Runs the dash app in a thread an open a browser window

    Parameters
    ----------
    app: instance of the Dash class, part of the dash library

    timeout: int or float
        Specifies the number of seconds that the web app should be open in the browser before timing out.

    Returns
    -------
    Nothing, but the web app version of the auto-report is displayed in a browser.
    """

    td = threading.Thread(target=app.run_server)
    td.daemon = True
    td.start()
    webbrowser.open("http://127.0.0.1:8050", new=1)
    td.join(timeout)


def make_dash_data_table(df, title=None):
    r"""
    Function that creates a Dash DataTable from a Pandas dataframe.

    Parameters
    ----------
    df: :pandas:`pandas.DataFrame<frame>`
        This dataframe holds the data from which the dash table is to be created.

    title: str
        An optional title for the table.
        Default: None

    Returns
    -------
    html.Div()
        This element contains the title of the dash table and the dash table itself encased in a
        child html.Div() element.

    """
    content = [
        html.Div(
            className="tableplay",
            children=dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict("records"),
                style_cell={
                    "padding": "8px",
                    "height": "auto",
                    "width": "auto",
                    "fontFamily": "Courier New",
                    "textAlign": "center",
                    "whiteSpace": "normal",
                },
                style_data_conditional=[
                    {
                        "if": {"row_index": "odd"},
                        "backgroundColor": "rgb(248, 248, 248)",
                    }
                ],
                style_header={
                    "fontWeight": "bold",
                    "color": "#8c3604",
                    "whiteSpace": "normal",
                    "height": "auto",
                },
            ),
        )
    ]

    if title is not None:
        content = [html.H4(title, className="report_table_title")] + content

    return html.Div(className="report_table", children=content)


def insert_subsection(title, content, **kwargs):
    r"""
    Inserts sub-sections within the Dash app layout, such as Input data, simulation results, etc.

    Parameters
    ----------
    title : str
        This is the title or heading of the subsection.

    content : list
        This is typically a list of html elements or function calls returning html elements, that make up the
        body of the sub-section.

    kwargs : Any possible optional arguments such as styles, etc.

    Returns
    -------
    html.Div()
        This returns the sub-section of the report including the tile and other information within the sub-section.


    """
    if "className" in kwargs:
        className = "cell subsection {}".format(kwargs.pop("className"))
    else:
        className = "cell subsection"

    # TODO if content is a list

    if not isinstance(content, list):
        content = [content]

    return html.Div(
        className=className,
        children=[html.H3(title), html.Hr(className="cell small-12 horizontal_line")]
        + content,
        **kwargs,
    )


# Function that creates the headings
def insert_headings(heading_text):
    r"""
    This function is for creating the headings such as information, input data, etc.

    Parameters
    ----------
    heading_text: str
        Big headings for several sub-sections.

    Returns
    -------
    html.P()
        A html element with the heading text encased container.
    """

    return html.H2(
        className="cell", children=heading_text, style={"page-break-after": "avoid"}
    )


# Functions that creates paragraphs
def insert_body_text(body_of_text):
    r"""
    This function is for rendering blocks of text within the sub-sections.

    Parameters
    ----------
    body_of_text: str
        Typically a single-line or paragraph of text.

    Returns
    -------
    html.P()
        A html element that renders the paragraph of text in the Dash app layout.
    """

    return html.P(className="cell large-11 blockoftext", children=body_of_text)


def insert_log_messages(log_dict):
    r"""
    This function inserts logging messages that arise during the simulation, such as warnings and error messages,
    into the auto-report.
    
    Parameters
    ----------
    log_dict: dict
        A dictionary containing the logging messages collected during the simulation.

    Returns
    -------
    html.Div()
        This html element holds the children html elements that produce the lists of warnings and error messages
        for both print and screen versions of the auto-report.
    """

    return html.Div(
        children=[
            # this will be displayed only in the app
            html.Div(
                className="grid-x no-print",
                children=[
                    html.Div(
                        className="cell grid-x",
                        children=[
                            html.Div(children=k, className="cell small-1 list-marker"),
                            html.Div(children=v, className="cell small-11 list-log"),
                        ],
                    )
                    for k, v in log_dict.items()
                ],
            ),
            # this will be displayed only in the printed version
            html.Div(
                className="list-log print-only",
                children=html.Ul(children=[html.Li(v) for k, v in log_dict.items()]),
            ),
        ],
    )


def insert_plotly_figure(
    fig, id_plot=None, print_only=False,
):
    r"""
    Insert a plotly figure in a dash app layout

    Parameters
    ----------
    fig: :plotly:`plotly.graph_objs.Figure`
        figure object

    id_plot: str
        Id of the graph. Each plot gets an unique ID which can be used to manipulate the plot later.
        Default: None

    print_only: bool
        Used to determine if a web version of the plot is to be generated or not.
        Default: False

    Returns
    -------
    :dash:`dash_html_components.Div`
        Html Div component containing an image for the print-only version and a plotly figure for
        the online (no-print) app (in the app the user can interact with plotly figure,
        whereas the image is static).

    """

    # Specific modifications for print-only version
    fig2 = copy.deepcopy(fig)
    # Make the legend horizontally oriented so as to prevent the legend from being cut off
    fig2.update_layout(legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center"))

    # Static image for the pdf report
    rendered_plots = [
        html.Img(
            className="print-only dash-plot",
            src="data:image/png;base64,{}".format(
                base64.b64encode(
                    fig2.to_image(format="png", height=500, width=900)
                ).decode(),
            ),
        )
    ]

    # Dynamic plotly figure for the app
    if print_only is False:
        rendered_plots.append(
            dcc.Graph(className="no-print", id=id_plot, figure=fig, responsive=True,)
        )

    return html.Div(children=rendered_plots)


def ready_timeseries_plots(df_pd, dict_of_labels, only_print=False):
    r"""
    This function prepares the data for and calls insert_single_plot for plotting line and bar plots.

    Parameters
    ----------
    df_pd: :pandas:`pandas.DataFrame<frame>`
        The dataframe containing all of the data to be plotted.

    dict_of_labels: dict
        Dictionary holding the titles to be used for the plots generated.

    only_print: bool
        Default: False

    results_file: json results file
        This is the JSON results file that contains the user-specified path where the plots are to be saved as images.
        Default: None

    Returns
    -------
    plots: list
        This list holds the html.Div elements which have the plots encased.
    """

    list_of_keys = list(df_pd.columns)
    list_of_keys.remove("timestamp")
    plots = []
    # TODO if the number of plots is larger than this list, it will not plot more
    colors_list = [
        "royalblue",
        "#3C5233",
        "firebrick",
        "#002500",
        "#DEB841",
        "#4F3130",
    ]
    for (component, color_plot) in zip(list_of_keys, colors_list):
        comp_id = component + "-plot"
        fig = create_plotly_line_fig(
            x_data=df_pd["timestamp"],
            y_data=df_pd[component],
            plot_title=dict_of_labels[component],
            x_axis_name="Time",
            y_axis_name="kW",
            color_for_plot=color_plot,
        )
        plots.append(insert_plotly_figure(fig, id_plot=comp_id, print_only=only_print,))
    return plots


def ready_capacities_plots(df_kpis, json_results_file, only_print=False):
    r""" Call function to produce capacities bar plot and return the plot.

    This function prepares the data to be used for plotting the capacities bar plots, from the simulation results
    and calls the appropriate plotting function that generates the plots.

    Parameters
    ----------
    df_kpis: :pandas:`pandas.DataFrame<frame>`
        This dataframe holds the data required for the capacities bar plot.

    json_results_file: json
        This is the results file, output of the simulation.

    only_print: bool
        Setting this value true results in the function creating only the plot for the PDF report, but not the web app
        version of the auto-report.
        Default: False

    Returns
    -------
    plot: list
        This list holds the html.Div element(s) which themselves contain the plotly plots.
    """

    x_values = []
    y_values = []

    for kpi, cap in zip(list(df_kpis["label"]), list(df_kpis["optimizedAddCap"])):
        if cap > 0:
            x_values.append(kpi)
            y_values.append(cap)

    plot = insert_single_plot(
        x_data=x_values,
        y_data=y_values,
        plot_type="bar",
        plot_title="Optimal additional capacities (kW/kWh/kWp): "
        + json_results_file[PROJECT_DATA][PROJECT_NAME]
        + ", "
        + json_results_file[PROJECT_DATA][SCENARIO_NAME],
        x_axis_name="Items",
        y_axis_name="Capacities",
        id_plot="capacities-plot",
        print_only=only_print,
        path_file=json_results_file,
    )
    return plot


def ready_flows_plots(dict_values):
    r"""Generate figure for each assets' flow of the energy system.

    Parameters
    ----------
    dict_values: dict
        Dict with all simulation parameters

    Returns
    -------
        multi_plots: list
        This list holds all the plots generated by the function calls to the function insert_flows_plots
    """

    buses_list = list(dict_values[OPTIMIZED_FLOWS].keys())
    multi_plots = []
    for bus in buses_list:
        comp_id = bus + "-plot"
        title = (
            bus
            + " flows in LES: "
            + dict_values[PROJECT_DATA][PROJECT_NAME]
            + ", "
            + dict_values[PROJECT_DATA][SCENARIO_NAME]
        )

        df_data = dict_values[OPTIMIZED_FLOWS][bus]
        df_data.reset_index(level=0, inplace=True)
        df_data = df_data.rename(columns={"index": "timestamp"})

        fig = create_plotly_flow_fig(
            df_plots_data=df_data,
            x_legend="Time",
            y_legend=bus + " flow in kWh",
            plot_title=title,
        )
        multi_plots.append(
            insert_plotly_figure(
                fig,
                pdf_only=False,
                plot_id=comp_id,
                file_path=dict_values[SIMULATION_SETTINGS][PATH_OUTPUT_FOLDER],
                file_name=bus + "_flows_in_LES",
            )
        )

    return multi_plots


def insert_pie_plots(
    title_of_plot,
    names,
    values,
    color_scheme,
    plot_id,
    print_only=False,
    name_file=None,
    path_file_dict=None,
):
    r"""Function that creates and returns a html.Div element with a list of the pie plots.

    Parameters
    ----------
    title_of_plot: str

    names: list
        List containing the labels of the pies in the pie plot.

    values: list
        List containing the values of the labels to be plotted in the pie plot.

    color_scheme: instance of the px.colors class of the Plotly express library
        This parameter holds the color scheme which is palette of colors (list of hex values) to be applied to the pie
        plot to be created.

    plot_id: str
        Unique alphanumeric value assigned to each pie plot, which can be used for further manipulation of the pie plot.

    print_only: bool
        Setting this value true results in the function creating only the plot for the PDF report, but not the web app
        version of the auto-report.
        Default: False

    name_file: str
        This forms part of the name of the file to be used when saving the image of the plot generated to disk.
        Default: None

    path_file_dict: json
        This is the results json file which contains the path defined by the user using which the images of the plots
        generated are saved in the output folder.
        Default: None

    Returns
    -------
    html.Div() element
        Contains the list of the pie plots generated, both for the print and web app versions.
    """

    # Wrap the text of the title into next line if it exceeds the length given below
    title_of_plot = textwrap.wrap(title_of_plot, width=75)
    title_of_plot = "<br>".join(title_of_plot)

    fig = go.Figure(
        go.Pie(
            labels=names,
            values=values,
            textposition="inside",
            insidetextorientation="radial",
            texttemplate="%{label} <br>%{percent}",
            marker=dict(colors=color_scheme),
        ),
    )

    fig.update_layout(
        title={
            "text": title_of_plot,
            "y": 0.9,
            "x": 0.5,
            "font_size": 23,
            "xanchor": "center",
            "yanchor": "top",
            "pad": {"r": 5, "l": 5, "b": 5, "t": 5},
        },
        font_family="sans-serif",
        height=500,
        width=700,
        autosize=True,
        legend=dict(orientation="v", y=0.5, yanchor="middle", x=0.95, xanchor="right",),
        margin=dict(l=10, r=10, b=50, pad=2),
        uniformtext_minsize=18,
    )
    fig.update_traces(hoverinfo="label+percent", textinfo="label", textfont_size=18)

    # Function call to save the Plotly plot to the disk
    save_plots_to_disk(
        fig_obj=fig,
        file_path_dict=path_file_dict,
        file_name=name_file,
        width=1200,
        height=600,
        scale=6,
    )

    # Specific modifications for print version
    fig2 = copy.deepcopy(fig)
    # Make the legend horizontally oriented so as to prevent the legend from being cut off
    fig2.update_layout(legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"))

    plot_created = [
        html.Img(
            className="print-only dash-plot",
            src="data:image/png;base64,{}".format(
                base64.b64encode(
                    fig2.to_image(format="png", height=500, width=900)
                ).decode(),
            ),
        )
    ]

    if print_only is False:
        plot_created.append(
            dcc.Graph(className="no-print", id=plot_id, figure=fig, responsive=True,)
        )
    return html.Div(children=plot_created)


def ready_pie_plots(df_pie_data, json_results_file, only_print=False):
    r"""Process data for the pie plots and call the relevant functions, resulting in the generation of the pie plots.
    
    Parameters
    ----------
    df_pie_data: :pandas:`pandas.DataFrame<frame>`
        This dataframe contains the costs data necessary to create the pie plots.


    json_results_file: json
        This is json file with all the results necessary to create the elements of the autoreport. In this case, it is
        required to determine the user-provided outputs folder path.


    only_print: bool
        Setting this value true results in the function creating only the plot for the PDF report, but not the web app
        version of the auto-report.
        Default: False

    Returns
    -------

    """
    # Initialize an empty list and a dict for use later in the function
    pie_plots = []
    pie_data_dict = {}

    # df_pie_data.reset_index(drop=True, inplace=True)
    columns_list = list(df_pie_data.columns)
    columns_list.remove(LABEL)

    # Loop to iterate through the list of columns of the DF which are nothing but the KPIs to be plotted
    for kp_indic in columns_list:

        # Assign an id for the plot
        comp_id = kp_indic + "plot"

        kpi_part = ""

        # Make a copy of the DF to make various manipulations for the pie chart plotting
        df_temp = df_pie_data.copy()

        # Get the total value for each KPI to use in the title of the respective pie chart
        df_temp2 = df_temp.copy()
        df_temp2.set_index(LABEL, inplace=True)
        total_for_title = df_temp2.at["Total", kp_indic]

        # Drop the total row in the dataframe
        df_temp.drop(df_temp.tail(1).index, inplace=True)

        # Gather the data for each asset for the particular KPI, in a dict
        for row_index in range(0, len(df_temp)):
            pie_data_dict[df_temp.at[row_index, LABEL]] = df_temp.at[
                row_index, kp_indic
            ]

        # Remove negative values (such as the feed-in sinks) from the dict
        pie_data_dict = {k: v for (k, v) in pie_data_dict.items() if v > 0}

        # Get the names and values for the pie chart from the above dict
        names_plot = list(pie_data_dict.keys())
        values_plot = list(pie_data_dict.values())

        # Below loop determines the first part of the plot title, according to the kpi being plotted
        if "annuity" in kp_indic:
            kpi_part = "Annuity Costs ("
            file_name = "annuity"
            scheme_choosen = px.colors.qualitative.Set1
        elif "investment" in kp_indic:
            kpi_part = "Upfront Investment Costs ("
            scheme_choosen = px.colors.diverging.BrBG
            file_name = "upfront_investment_costs"
        elif "om" in kp_indic:
            kpi_part = "Operation and Maintenance Costs ("
            scheme_choosen = px.colors.sequential.RdBu
            file_name = "operation_and_maintainance_costs"

        # Title of the pie plot
        plot_title = (
            kpi_part
            + str(round(total_for_title, 2))
            + "$): "
            + json_results_file[PROJECT_DATA][PROJECT_NAME]
            + ", "
            + json_results_file[PROJECT_DATA][SCENARIO_NAME]
        )

        # Append the plot to the list by calling the plotting function directly
        pie_plots.append(
            insert_pie_plots(
                title_of_plot=plot_title,
                names=names_plot,
                values=values_plot,
                color_scheme=scheme_choosen,
                plot_id=comp_id,
                print_only=only_print,
                name_file=file_name,
                path_file_dict=json_results_file,
            )
        )
    return pie_plots


# Styling of the report


def create_app(results_json):
    r"""Initializes the app and calls all the other functions, resulting in the web app as well as pdf.

    This function specifies the layout of the web app, loads the external styling sheets, prepares the necessary data
    from the json results file, calls all the helper functions on the data, resulting in the auto-report.

    Parameters
    ----------
    results_json: json results file
        This file is the result of the simulation and contains all the data necessary to generate the auto-report.

    Returns
    -------
    app: instance of the Dash class within the dash library
        This app holds together all the html elements wrapped in Python, necessary for the rendering of the auto-report.
    """

    # external CSS stylesheets
    external_stylesheets = [
        {
            "href": "https://cdnjs.cloudflare.com/ajax/libs/foundation/6.6.3/css/foundation.min.css",
            "rel": "stylesheet",
            "integrity": "sha256-ogmFxjqiTMnZhxCqVmcqTvjfe1Y/ec4WaRj/aQPvn+I=",
            "crossorigin": "anonymous",
            "media": "screen",
        },
    ]

    app = dash.Dash(
        __name__,
        assets_folder=os.path.join(REPORT_PATH, "assets"),
        external_stylesheets=external_stylesheets,
    )

    # Reading the relevant user-inputs from the json_with_results.json file into Pandas dataframes
    dfprojectData = pd.DataFrame.from_dict(results_json[PROJECT_DATA])
    dfeconomicData = pd.DataFrame.from_dict(results_json[ECONOMIC_DATA]).loc[VALUE]

    # Obtaining the latlong of the project location
    latlong = (
        float(dfprojectData.latitude),
        float(dfprojectData.longitude),
    )

    # Determining the geographical location of the project
    geoList = rg.search(latlong)
    geoDict = geoList[0]
    location = geoDict["name"]

    # Adds a map to the Dash app
    mapy = folium.Map(location=latlong, zoom_start=14)
    tooltip = "Click here for more info"
    folium.Marker(
        latlong,
        popup="Location of the project",
        tooltip=tooltip,
        icon=folium.Icon(color="red", icon="glyphicon glyphicon-flash"),
    ).add_to(mapy)
    mapy.save(os.path.join(REPORT_PATH, "assets", "proj_map"))

    # Adds a staticmap to the PDF

    longitude = latlong[1]
    latitude = latlong[0]
    coords = longitude, latitude

    map_static = staticmap.StaticMap(600, 600, 80)
    marker = staticmap.CircleMarker(coords, "#13074f", 15)
    map_static.add_marker(marker)
    map_image = map_static.render(zoom=14)
    map_image.save(os.path.join(REPORT_PATH, "assets", "proj_map_static.png"))

    dict_projectdata = {
        "Country": dfprojectData.country,
        "Project ID": dfprojectData.project_id,
        "Scenario ID": dfprojectData.scenario_id,
        "Currency": dfeconomicData.currency,
        "Project Location": location,
        "Discount Factor": dfeconomicData.discount_factor,
        "Tax": dfeconomicData.tax,
    }

    df_projectData = pd.DataFrame(
        list(dict_projectdata.items()), columns=["Label", "Value"]
    )

    dict_simsettings = {
        "Evaluated period": results_json[SIMULATION_SETTINGS][EVALUATED_PERIOD][VALUE],
        "Start date": results_json[SIMULATION_SETTINGS][START_DATE],
        "Timestep length": results_json[SIMULATION_SETTINGS][TIMESTEP][VALUE],
    }

    # Dict that gathers all the flows through various buses
    data_flows = results_json["optimizedFlows"]

    df_simsettings = pd.DataFrame(
        list(dict_simsettings.items()), columns=["Setting", "Value"]
    )

    projectName = (
        results_json[PROJECT_DATA][PROJECT_NAME]
        + " (ID: "
        + str(results_json[PROJECT_DATA][PROJECT_ID])
        + ")"
    )
    scenarioName = (
        results_json[PROJECT_DATA][SCENARIO_NAME]
        + " (ID: "
        + str(results_json[PROJECT_DATA][SCENARIO_ID])
        + ")"
    )

    releaseDesign = "0.0x"

    # Getting the branch ID
    repo = git.Repo(search_parent_directories=True)
    # TODO: also extract branch name
    branchID = repo.head.object.hexsha

    simDate = time.strftime("%Y-%m-%d")

    ELAND_LOGO = base64.b64encode(
        open(
            os.path.join(REPORT_PATH, "assets", "logo-eland-original.jpg"), "rb"
        ).read()
    )

    MAP_STATIC = base64.b64encode(
        open(os.path.join(REPORT_PATH, "assets", "proj_map_static.png"), "rb").read()
    )

    # Determining the sectors which were simulated

    sectors = list(results_json[PROJECT_DATA][SECTORS].keys())
    sec_list = """"""
    for sec in sectors:
        sec_list += "\n" + f"\u2022 {sec.upper()}"

    df_dem = convert_demand_to_dataframe(results_json)
    dict_for_plots, dict_plot_labels = extract_plot_data_and_title(
        results_json, df_dem=df_dem
    )

    df_comp = convert_components_to_dataframe(results_json)
    df_all_demands = convert_plot_data_to_dataframe(dict_for_plots, "demands")
    df_all_res = convert_plot_data_to_dataframe(dict_for_plots, "supplies")
    df_scalar_matrix = convert_scalar_matrix_to_dataframe(results_json)
    df_cost_matrix = convert_cost_matrix_to_dataframe(results_json)
    df_kpis = convert_kpi_matrix_to_dataframe(results_json)

    # Add dataframe to hold all the KPIs and optimized additional capacities
    df_capacities = results_json[KPI][KPI_SCALAR_MATRIX]
    df_capacities.drop(
        columns=[TOTAL_FLOW, ANNUAL_TOTAL_FLOW, PEAK_FLOW, AVERAGE_FLOW], inplace=True,
    )
    df_capacities.reset_index(drop=True, inplace=True)

    warnings_dict = parse_simulation_log(log_type="WARNING")
    errors_dict = parse_simulation_log(log_type="ERROR")

    # App layout and populating it with different elements
    app.layout = html.Div(
        id="main-div",
        className="grid-x align-center",
        children=[
            html.Div(
                className="cell small-10 small_offset-1 header_title_logo",
                children=[
                    html.Img(
                        id="mvslogo",
                        src="data:image/png;base64,{}".format(ELAND_LOGO.decode()),
                        width="500px",
                    ),
                    html.H1("MULTI VECTOR SIMULATION - REPORT SHEET"),
                ],
            ),
            html.Section(
                className="cell small-10 small_offset-1 grid-x",
                children=[
                    insert_headings("Information"),
                    html.Div(
                        className="cell imp_info",
                        children=[
                            html.P(f"MVS Release: {version_num} ({version_date})"),
                            html.P(f"Branch-id: {branchID}"),
                            html.P(f"Simulation date: {simDate}"),
                            html.Div(
                                className="cell imp_info2",
                                children=[
                                    html.Span(
                                        "Project name   : ",
                                        style={"font-weight": "bold"},
                                    ),
                                    f"{projectName}",
                                ],
                            ),
                            html.Div(
                                className="cell imp_info2",
                                children=[
                                    html.Span(
                                        "Scenario name  : ",
                                        style={"font-weight": "bold"},
                                    ),
                                    f"{scenarioName}",
                                ],
                            ),
                            html.Div(
                                className="blockoftext",
                                children=[
                                    "The energy system with the ",
                                    html.Span(
                                        f"{projectName}", style={"font-style": "italic"}
                                    ),
                                    " for the scenario ",
                                    html.Span(
                                        f"{scenarioName}",
                                        style={"font-style": "italic"},
                                    ),
                                    " was simulated with the Multi-Vector simulation tool MVS 0.0x developed from the E-LAND toolbox "
                                    "developed in the scope of the Horizon 2020 European research project. The tool was developed by "
                                    "Reiner Lemoine Institute and utilizes the OEMOF framework.",
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Section(
                className="cell small-10 small_offset-1 grid-x",
                style={"pageBreakBefore": "always"},
                children=[
                    insert_headings("Input Data"),
                    insert_subsection(
                        title="Project Data",
                        content=[
                            insert_body_text(
                                "The most important simulation data will be presented below. "
                                "Detailed settings, costs, and technological parameters can "
                                "be found in the appendix."
                            ),
                            html.Div(
                                className="grid-x ",
                                id="location-map-div",
                                children=[
                                    html.Div(
                                        className="cell small-6 location-map-column",
                                        children=[
                                            html.H4(["Project Location"]),
                                            html.Iframe(
                                                srcDoc=open(
                                                    os.path.join(
                                                        REPORT_PATH,
                                                        "assets",
                                                        "proj_map",
                                                    ),
                                                    "r",
                                                ).read(),
                                                height="400",
                                                style={
                                                    "margin": "30px",
                                                    "width": "30%",
                                                    "marginBottom": "1.5cm",
                                                },
                                            ),
                                            html.Div(
                                                className="staticimagepdf",
                                                children=[
                                                    insert_body_text(
                                                        "The blue dot in the below map indicates "
                                                        "the location of the project."
                                                    ),
                                                    html.Img(
                                                        id="staticmapimage",
                                                        src="data:image/png;base64,{}".format(
                                                            MAP_STATIC.decode()
                                                        ),
                                                        width="400px",
                                                        style={"marginLeft": "30px"},
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="cell small-6 location-map-column",
                                        children=make_dash_data_table(
                                            df_projectData, "Project at a Glance"
                                        ),
                                    ),
                                ],
                            ),
                            make_dash_data_table(df_simsettings, "Simulation Settings"),
                        ],
                    ),
                    insert_subsection(
                        title="Energy demand",
                        content=[
                            insert_body_text(
                                "The simulation was performed for the energy system "
                                "covering the following sectors: "
                            ),
                            insert_body_text(f"{sec_list}"),
                            html.H4("Electricity Demand"),
                            insert_body_text(
                                "Electricity demands " "that have to be supplied are:"
                            ),
                            make_dash_data_table(df_dem),
                            html.Div(
                                children=ready_timeseries_plots(
                                    df_all_demands, dict_plot_labels,
                                )
                            ),
                            html.H4("Resources"),
                            html.Div(
                                children=ready_timeseries_plots(
                                    df_all_res, dict_plot_labels,
                                )
                            ),
                        ],
                    ),
                    insert_subsection(
                        title="Energy system components",
                        content=[
                            insert_body_text(
                                "The energy system is comprised of "
                                "the following components:"
                            ),
                            make_dash_data_table(df_comp),
                        ],
                    ),
                ],
            ),
            html.Section(
                className="cell small-10 small_offset-1 grid-x",
                style={"pageBreakBefore": "always"},
                children=[
                    html.H2(className="cell", children="Simulation Results"),
                    insert_subsection(
                        title="Dispatch & Energy Flows",
                        content=[
                            insert_body_text(
                                "The capacity optimization of components that were to be used resulted in:"
                            ),
                            make_dash_data_table(df_scalar_matrix),
                            insert_body_text(
                                "With this, the demands are met with the following dispatch schedules:"
                            ),
                            html.Div(
                                children=ready_flows_plots(dict_values=results_json,)
                            ),
                            html.Div(
                                className="add-cap-plot",
                                children=ready_capacities_plots(
                                    df_kpis=df_capacities,
                                    json_results_file=results_json,
                                    only_print=False,
                                ),
                            ),
                            insert_body_text(
                                "This results in the following KPI of the dispatch:"
                            ),
                            # TODO the table with renewable share, emissions, total renewable generation, etc.
                        ],
                    ),
                    insert_subsection(
                        title="Economic Evaluation",
                        content=[
                            insert_body_text(
                                "The following installation and operation costs "
                                "result from capacity and dispatch optimization:"
                            ),
                            make_dash_data_table(df_cost_matrix),
                            html.Div(
                                className="add-pie-plots",
                                children=ready_pie_plots(
                                    df_pie_data=df_kpis,
                                    json_results_file=results_json,
                                    only_print=False,
                                ),
                            ),
                        ],
                    ),
                ],
            ),
            html.Section(
                className="cell small-10 small_offset-1 grid-x",
                children=[
                    html.Div(
                        className="cell",
                        children=[insert_headings(heading_text="Logging Messages"),],
                    ),
                    html.Div(
                        children=[
                            insert_subsection(
                                title="Warning Messages",
                                content=insert_log_messages(log_dict=warnings_dict),
                            ),
                            insert_subsection(
                                title="Error Messages",
                                content=insert_log_messages(log_dict=errors_dict),
                            ),
                        ]
                    ),
                ],
            ),
        ],
    )
    return app


if __name__ == "__main__":
    from src.constants import REPO_PATH, OUTPUT_FOLDER
    from src.B0_data_input_json import load_json

    dict_values = load_json(
        os.path.join(REPO_PATH, OUTPUT_FOLDER, "json_with_results.json")
    )

    test_app = create_app(dict_values)
    open_in_browser(test_app)
