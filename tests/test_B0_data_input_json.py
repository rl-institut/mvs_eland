import os
import shutil

import mock

import src.A0_initialization as initializing
import src.A1_csv_to_json as load_data_from_csv
import src.B0_data_input_json as data_input
from src.constants_json_strings import SIMULATION_SETTINGS
from .constants import (
    JSON_PATH,
    CSV_PATH,
    CSV_FNAME,
    CSV_ELEMENTS,
    JSON_CSV_PATH,
    CSV_EXT,
    PATH_INPUT_FOLDER,
    PATH_OUTPUT_FOLDER,
    PATH_OUTPUT_FOLDER_INPUTS,
    TEST_REPO_PATH,
    PARSER_ARGS
)


def test_load_json_overwrite_output_folder_from_json():
    dict_values = data_input.load_json(JSON_PATH, path_output_folder="test")
    assert dict_values[SIMULATION_SETTINGS][PATH_OUTPUT_FOLDER] == "test"
    assert dict_values[SIMULATION_SETTINGS][PATH_OUTPUT_FOLDER_INPUTS] == os.path.join(
        "test", "inputs"
    )


def test_load_json_overwrite_input_folder_from_json():
    dict_values = data_input.load_json(JSON_PATH, path_input_folder="test")
    assert dict_values[SIMULATION_SETTINGS][PATH_INPUT_FOLDER] == "test"


PARSER = initializing.create_parser()


class TestTemporaryJsonFileDisposal:

    test_in_path = os.path.join(TEST_REPO_PATH, "inputs")
    test_out_path = os.path.join(TEST_REPO_PATH, "MVS_outputs")

    def setup_class(self):
        """ """
        shutil.rmtree(test_out_path, ignore_errors=True)

    @mock.patch(
        "argparse.ArgumentParser.parse_args",
        return_value=PARSER.parse_args(
            PARSER_ARGS(input_folder=test_in_path, output_folder=test_out_path, ext=CSV_EXT)
        ),
    )
    def test_load_json_removes_json_file_from_inputs_folder(self, m_args):
        initializing.process_user_arguments()

        load_data_from_csv.create_input_json(input_directory=CSV_PATH, pass_back=True)
        dict_values = data_input.load_json(
            JSON_CSV_PATH, path_output_folder=self.test_out_path, move_copy=True
        )

        assert os.path.exists(os.path.join(CSV_PATH, CSV_ELEMENTS, CSV_FNAME,)) is False

        assert os.path.exists(os.path.join(CSV_PATH, CSV_FNAME,)) is False

    @mock.patch(
        "argparse.ArgumentParser.parse_args",
        return_value=PARSER.parse_args(
            PARSER_ARGS(input_folder=test_in_path, output_folder=test_out_path, ext=CSV_EXT)
        ),
    )
    def test_load_json_copies_json_file_to_output_folder(self, m_args):
        initializing.process_user_arguments()

        load_data_from_csv.create_input_json(input_directory=CSV_PATH, pass_back=True)
        dict_values = data_input.load_json(
            JSON_CSV_PATH, path_output_folder=self.test_out_path, move_copy=True
        )

        assert (
            os.path.exists(
                os.path.join(
                    dict_values[SIMULATION_SETTINGS][PATH_OUTPUT_FOLDER_INPUTS],
                    CSV_FNAME,
                )
            )
            is True
        )

    def teardown_method(self):
        if os.path.exists(self.test_out_path):
            shutil.rmtree(self.test_out_path, ignore_errors=True)
