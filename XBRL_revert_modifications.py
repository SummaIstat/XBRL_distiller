import os
import sys
import logging
from os import remove
from datetime import datetime

PROGRAM_NAME = "XBRL_revert_modifications"
logger = logging.getLogger(PROGRAM_NAME + 'Logger')
logger.setLevel(logging.DEBUG)
logFormatter = logging.Formatter("%(asctime)s - %(module)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setLevel(logging.DEBUG)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
now = datetime.now()
dateTime = now.strftime("%Y-%m-%d_%H_%M_%S")
LOG_FILE_NAME = "log_" + PROGRAM_NAME + "_" + dateTime + ".log"
fileHandler = logging.FileHandler(LOG_FILE_NAME)
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)


def main(argv):
    xbrl_folder_path = config()
    logger.info("******************************************************")
    logger.info("**********   XBRL_revert_modifications   *************")
    logger.info("******************************************************\n\n")

    # ==========================================================================
    #  mi carico la lista di file original
    # ==========================================================================

    counter = 0
    lista_file_original = []
    for root, dirs, files in os.walk(xbrl_folder_path):
        for file in files:
            if file.endswith(".original"):
                lista_file_original.append(os.path.join(root, file))
                counter = counter + 1
    logger.info("Num of \".original\" files detected = " + str(counter) + "\n")

    # ==========================================================================
    # per ogni file original cancello tutti gli omonimi e rinomino il file
    # original eliminando il suffisso ".original"
    # ==========================================================================

    num_files = len(lista_file_original)
    for i, fileXbrl in enumerate(lista_file_original):
        logger.info("processing file " + str(i+1) + " / " + str(num_files) + "   " + str(fileXbrl))
        current_folder = "\\".join(fileXbrl.split("\\")[:-1])
        file_name_no_ext = fileXbrl.split("\\")[-1].split(".")[0]
        file_to_be_removed = current_folder + "\\" + file_name_no_ext + ".xbrl"
        if os.path.exists(file_to_be_removed):
            remove(file_to_be_removed)
        old_file_name = fileXbrl
        new_file_name = current_folder + "\\" + file_name_no_ext + ".xbrl"
        os.rename(old_file_name, new_file_name)


def config():
    config_file_path = "revert_config.cfg"
    if not os.path.exists(config_file_path):
        error_message = "The \"revert_config.cfg\" configuration file was not found in the executable file directory!"
        logger.error(error_message)
        sys.exit(error_message)

    external_settings = dict()
    with open(config_file_path, "rt") as f:
        for line in f.readlines():
            if not line.startswith("#"):
                tokens = line.split("=")
                if len(tokens) == 2:
                    external_settings[tokens[0].strip()] = tokens[1].strip()

    xbrl_folder_path = str(external_settings['XBRL_FOLDER_PATH']).strip()
    if not os.path.exists(xbrl_folder_path):
        error_message = "The XBRL_FOLDER_PATH directory provided in the revert_config.cfg configuration file does not exist!"
        logger.error(error_message)
        sys.exit(error_message)

    return xbrl_folder_path


if __name__ == "__main__":
    main(sys.argv[1:])
