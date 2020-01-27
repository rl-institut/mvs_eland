#!/usr/bin/env python
import os
import sys
import shutil
import logging

from oemof.tools import logger


def check_input_directory(path_input_file):
    """
    :param path_input_file:
    :return:
    """

    path_input_folder = os.path.dirname(path_input_file)
    name_input_file = os.path.basename(path_input_file)

    logging.debug("Checking for inputs files")
    if os.path.isdir(path_input_folder) is False:
        logging.critical(
            "Missing folder for inputs! "
            "\n The input folder can not be found. Operation terminated."
        )
        sys.exit()

    if os.path.isfile(path_input_file) is False:
        logging.critical(
            "Missing input excel file! "
            "\n The input excel file can not be found. Operation terminated."
        )
        sys.exit()
    return path_input_folder, name_input_file


def check_output_directory(path_output_folder, overwrite):
    """
    :param path_output_folder:
    :param overwrite:
    :return:
    """
    logging.debug("Checking for output folder")
    if os.path.exists(path_output_folder) is True:
        if overwrite is False:
            user_reply = input(
                "Attention: Output overwrite? "
                "\n Output folder already exists. Should it be overwritten? (y/n)"
            )
            print(user_reply)
            if user_reply in ["y", "Y", "yes", "Yes"]:
                overwrite is True
            else:
                logging.critical(
                    "Output folder exists and should not be overwritten. Please choose other folder."
                )
                raise (
                    FileExistsError(
                        "Output folder exists and should not be overwritten. Please choose other folder."
                    )
                )

        if overwrite is True:
            logging.info("Removing existing folder " + path_output_folder)
            path_removed = os.path.abspath(path_output_folder)
            shutil.rmtree(path_removed, ignore_errors=True)
            logging.info("Creating output folder " + path_output_folder)
            os.mkdir(path_output_folder)

    else:
        logging.info("Creating output folder " + path_output_folder)
        os.mkdir(path_output_folder)


def get_user_input(
    path_input_file="./inputs/working_example.json",
    path_output_folder="./MVS_outputs",
    overwrite=False,  # todo this means that results will be overwritten.
    display_output="-debug",
    lp_file_output=False,
    **kwargs
):
    """
    Read user command from terminal inputs. Command:

    python A_mvs_eland.py path_to_input_file path_to_output_folder overwrite display_output lp_file_output

    :param path_input_file:
        Descripes path to inputs excel file
        This file includes paths to timeseries file
    :param path_output_folder:
        Describes path to folder to be used for terminal output
        Must not exist before
    :param overwrite:
        (Optional) Can force tool to replace existing output folder
        "-f"
    :param display_output:
        (Optional) Determines which messages are used for terminal output
            "-debug": All logging messages
            "-info": All informative messages and warnings (default)
            "-warnings": All warnings
            "-errors": Only errors

    :param lp_file_output:
        Save linear equation system generated as lp file

    :return:
    """

    if "test" in kwargs and kwargs["test"] is True:
        overwrite = True
    else:
        # Read terminal inputs:
        if len(sys.argv) <= 1:
            logging.warning(
                "No inputs file or output folder determined. "
                "\n Will use default values and delete existing output folder (test execution)."
            )
            overwrite = True

        elif len(sys.argv) == 2:
            logging.error(
                "Missing command path_output_folder. " "\n Operation terminated."
            )

        elif len(sys.argv) == 3 or len(sys.argv) == 4:
            # Read user commands from terminal inputs
            path_input_file = str(sys.argv[1])
            path_output_folder = str(sys.argv[2])
            for argument in range(3, len(sys.argv) + 1):
                if str(sys.argv[argument]) == "-f":
                    overwrite = True
                elif str(sys.argv[argument]) in [
                    "-debug",
                    "-info",
                    "-warnings",
                    "-errors",
                ]:
                    display_output = str(sys.argv[argument])
                elif str(sys.argv[argument]) in ["False", "True"]:
                    if str(sys.argv[argument]) == "True":
                        lp_file_output = True
                else:
                    logging.critical(
                        "Invalid command "
                        + str(sys.argv[argument])
                        + " used. "
                        + "\n Operation terminated."
                    )
                    sys.exit()
        else:
            logging.critical("Too many commands. " "Operation terminated.")
            sys.exit()

    path_input_folder, name_input_file = check_input_directory(path_input_file)
    check_output_directory(path_output_folder, overwrite)

    user_input = {
        "label": "simulation_settings",
        "path_input_folder": path_input_folder + "/",
        "path_input_file": path_input_file,
        "path_output_folder": path_output_folder,
        "path_output_folder_inputs": path_output_folder + "/inputs/",
        "lp_file_output": lp_file_output,
        "input_file_name": name_input_file,
        "display_output": display_output,
        "overwrite": overwrite,
    }

    logging.info('Creating folder "inputs" in output folder.')

    os.mkdir(user_input["path_output_folder_inputs"])
    shutil.copy(user_input["path_input_file"], user_input["path_output_folder_inputs"])
    return user_input


def welcome(welcome_text, **kwargs):
    """
    Welcome message and initalization of logging on screen and on file level.
    :param welcome_text: Welcome text defined in main function
    :return: user input settings regarding screen output, input folder/file and output folder
    """
    logging.debug("Get user inputs from console")
    user_input = get_user_input(**kwargs)

    # Set screen level (terminal output) according to user inputs
    console_log = user_input.pop("display_output")

    if console_log == "-debug":
        screen_level = logging.DEBUG
    elif console_log == "-info":
        screen_level = logging.INFO
    elif console_log == "-warning":
        screen_level = logging.WARNING
    elif console_log == "-error":
        screen_level = logging.ERROR
    else:
        screen_level = logging.INFO

    # Define logging settings and path for saving log
    logger.define_logging(
        logpath=user_input["path_output_folder"],
        logfile="mvst_logfile.log",
        file_level=logging.DEBUG,
        screen_level=screen_level,
    )

    # display welcome text
    logging.info(welcome_text)
    return user_input