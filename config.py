import os
import sys
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logger.debug(__name__ + ' logger initialized')


class Config:

    def __init__(self, argv):
        global logger
        external_settings = Config.load_external_configuration(argv)

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logFormatter = logging.Formatter("%(asctime)s - %(module)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setLevel(logging.DEBUG)
        consoleHandler.setFormatter(logFormatter)
        logger.addHandler(consoleHandler)
        now = datetime.now()
        file_date_time = now.strftime("%Y-%m-%d_%H_%M_%S")

        try:
            self.PROGRAM_NAME = "XBRL_distiller"
            self.YEAR = str(external_settings['YEAR']).strip()
            self.ENCODING = str(external_settings['ENCODING']).strip()
            self.ENABLE_HTML_TAG_REMOVAL = str(external_settings['ENABLE_HTML_TAG_REMOVAL']).strip()
            self.OUTPUT_FILE_FIELD_SEPARATOR = str(external_settings['OUTPUT_FILE_FIELD_SEPARATOR']).strip()
            self.XBRL_FOLDER_PATH = str(external_settings['XBRL_FOLDER_PATH']).strip()
            self.OUTPUT_FOLDER_PATH = str(external_settings['OUTPUT_FOLDER_PATH']).strip()
            self.INPUT_TAG_LIST_FILE_PATH = str(external_settings['INPUT_TAG_LIST_FILE_PATH']).strip()
            self.LOG_FOLDER_PATH = str(external_settings['LOG_FOLDER_PATH']).strip()
            # self.NS = str(external_settings['NS']).strip()  # now it is automatically detected
            self.LEGITIMATE_FILE_NAME = "legitimate_xbrl_files"
            self.PROBLEMATIC_FILE_NAME = "problematic_xbrl_files"

            if self.OUTPUT_FILE_FIELD_SEPARATOR == "\\t":
                self.OUTPUT_FILE_FIELD_SEPARATOR = "\t"

            try:
                self.ENABLE_HTML_TAG_REMOVAL = int(self.ENABLE_HTML_TAG_REMOVAL)
                if self.ENABLE_HTML_TAG_REMOVAL not in (0, 1):
                    error_message = "The ENABLE_HTML_TAG_REMOVAL parameter in the config.cfg configuration file must be 0 or 1!"
                    logger.error(error_message)
                    sys.exit(error_message)
            except ValueError as e:
                error_message = "The ENABLE_HTML_TAG_REMOVAL parameter in the config.cfg configuration file must be 0 or 1!"
                logger.error(error_message)
                sys.exit(error_message)

            try:
                self.YEAR = int(self.YEAR)
                self.YEAR = str(self.YEAR)
            except ValueError as e:
                error_message = "The YEAR parameter in the config.cfg configuration file must be an integer!"
                logger.error(error_message)
                sys.exit(error_message)

            if not os.path.exists(self.XBRL_FOLDER_PATH):
                error_message = "The XBRL_FOLDER_PATH directory provided in the config.cfg configuration file does not exist!"
                logger.error(error_message)
                sys.exit(error_message)

            if not os.path.exists(self.OUTPUT_FOLDER_PATH):
                error_message = "The OUTPUT_FOLDER_PATH directory provided in the config.cfg configuration file does not exist!"
                logger.error(error_message)
                sys.exit(error_message)

            if not os.path.exists(self.INPUT_TAG_LIST_FILE_PATH):
                error_message = "The INPUT_TAG_LIST_FILE_PATH file provided in the config.cfg configuration file does not exist!"
                logger.error(error_message)
                sys.exit(error_message)

            if not os.path.exists(self.LOG_FOLDER_PATH):
                error_message = "The LOG_FOLDER_PATH directory provided in the config.cfg configuration file does not exist!"
                logger.error(error_message)
                sys.exit(error_message)

            self.FILE_DATE_TIME = file_date_time
            LOG_FILE_NAME = self.LOG_FOLDER_PATH + "\log_" + self.PROGRAM_NAME + "_" + self.FILE_DATE_TIME + ".log"
            fileHandler = logging.FileHandler(LOG_FILE_NAME)
            fileHandler.setLevel(logging.DEBUG)
            fileHandler.setFormatter(logFormatter)
            logger.addHandler(fileHandler)
            self.LOGGER = logger
            self.LOG_LEVEL = str(external_settings['LOG_LEVEL']).strip()

        except Exception as e:
            sys.exit("Missing parameters and/or Invalid parameter values in configuration file")

    @staticmethod
    def load_external_configuration(argv):

        config_file_path = "config.cfg"
        if not os.path.exists(config_file_path):
            error_message = "The \"config.cfg\" configuration file was not found in the executable file directory!"
            logger.error(error_message)
            sys.exit(error_message)

        external_settings = dict()
        with open(config_file_path, "rt") as f:
            for line in f.readlines():
                if not line.startswith("#"):
                    tokens = line.split("=")
                    if len(tokens) == 2:
                        external_settings[tokens[0].strip()] = tokens[1].strip()

        return external_settings
