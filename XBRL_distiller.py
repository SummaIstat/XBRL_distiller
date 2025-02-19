import os
import sys
#import xml.etree.ElementTree as ET
#from lxml import etree
import lxml.etree as ET
from tempfile import mkstemp
from datetime import datetime
from shutil import move, copymode
from os import fdopen, remove
import re
import logging
import util
import config
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logger.debug(__name__ + ' logger initialized')

conf = ""
cf_xbrl_list = []
problematic_file_list = []
tuple_list = []  # list of tuples each being (XBRL_tag_name, desired_name_in_output_file)
file_date_time = ""
output_filename = ""
legitimate_out_filename = ""
problematic_out_filename = ""

my_parser = ""
#my_parser = ET.XMLParser(recover=True, load_dtd=True, dtd_validation=False, encoding="utf-8")
#my_parser = ET.XMLParser(recover=True, load_dtd=True, dtd_validation=False, encoding="ISO-8859-1")


def main(argv):
    global conf
    global logger
    global my_parser

    conf = config.Config(argv)
    logger = conf.LOGGER

    for h in logger.handlers:
        h.setLevel(logging.getLevelName(conf.LOG_LEVEL))
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    for log in loggers:
        log.setLevel(logging.getLevelName(conf.LOG_LEVEL))

    my_parser = ET.XMLParser(recover=True, load_dtd=True, dtd_validation=False, encoding=conf.ENCODING)

    logger.info("*******************************************")
    logger.info("**********   XBRL_distiller   *************")
    logger.info("*******************************************\n")
    now = datetime.now()
    starting_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    logger.info("Starting datetime: " + starting_date_time)
    logger.info("XBRL_FOLDER_PATH = " + conf.XBRL_FOLDER_PATH)
    logger.info("OUTPUT_FOLDER_PATH = " + conf.OUTPUT_FOLDER_PATH)
    logger.info("LOG_FOLDER_PATH = " + conf.LOG_FOLDER_PATH)
    global tuple_list
    tuple_list = load_tuple_list(conf.INPUT_TAG_LIST_FILE_PATH)
    global file_date_time
    file_date_time = conf.FILE_DATE_TIME
    global legitimate_out_filename
    legitimate_out_filename = str(conf.OUTPUT_FOLDER_PATH) + "/" + str(conf.LEGITIMATE_FILE_NAME)
    global problematic_out_filename
    problematic_out_filename = str(conf.OUTPUT_FOLDER_PATH) + "/" + str(conf.PROBLEMATIC_FILE_NAME)
    global output_filename
    output_filename = str(conf.OUTPUT_FOLDER_PATH) + "/" + str(conf.PROGRAM_NAME + "_year" + conf.YEAR + "_" + conf.FILE_DATE_TIME + ".csv")
    write_header_on_output_file()
    xbrl_file_list = load_xbrl_file_list(conf.XBRL_FOLDER_PATH)
    num_of_xbrl_files = len(xbrl_file_list)
    for num, xbrl_file in enumerate(xbrl_file_list):
        logger.info("processing file " + str(num + 1) + " / " + str(num_of_xbrl_files))
        logger.debug("=========> " + str(xbrl_file))

        identifier = get_extracted_cf(xbrl_file)
        if identifier != -1:
            cf_xbrl_list.append("\t".join([str(identifier), str(xbrl_file), "original"]))
            # line_to_append = "\t".join([str(identifier), str(xbrl_file), "original"])
            # append_line_on_file(legitimate_out_filename, line_to_append)
            extract_values_from_tags(xbrl_file)
        else:
            identifier = recover_and_retry(xbrl_file)
            if identifier == -1:
                logger.error("File modified but still unreadable !")
            elif identifier == -2:
                logger.error("File unmodifiable and still unreadable !")
            else:
                cf_xbrl_list.append("\t".join([str(identifier), str(xbrl_file), "recovered"]))
                # line_to_append = "\t".join([str(identifier), str(xbrl_file), "recovered"])
                # append_line_on_file(legitimate_out_filename, line_to_append)
                extract_values_from_tags(xbrl_file)

    cf_xbrl_set = set()
    for elem in cf_xbrl_list:
        cf_xbrl_set.add(elem.split("\t")[0])
    logger.info("numero CF nei file xbrl rilevati list = " + str(len(cf_xbrl_list)))
    logger.info("numero CF nei file xbrl rilevati set = " + str(len(cf_xbrl_set)))

    if len(problematic_file_list) == 0:
        logger.info("\n\nNo problematic files found !")

    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    logger.info("\n\n")
    logger.info("Starting datetime: " + starting_date_time)
    logger.info("Ending datetime: " + date_time)


# ==========================================================================
# functions
# ==========================================================================

def write_header_on_output_file():
    global output_filename
    global tuple_list
    global conf
    sep = conf.OUTPUT_FILE_FIELD_SEPARATOR
    with open(output_filename, 'a+') as f:
        static_header = "filePath" + sep +\
                     "fileName" + sep +\
                     "chiave_bilancio_filename" + sep +\
                     "identifier_filename" + sep +\
                     "identifier_xbrl"
        dynamic_header = ""
        for t in tuple_list:
            dynamic_header = dynamic_header + sep + t[1]
        dynamic_header = dynamic_header + "\n"
        header = static_header + dynamic_header
        f.writelines(header)


def append_line_on_output_file(my_dict):
    global output_filename
    global tuple_list
    global conf
    # In Python 3.7+ the insertion-order preservation nature of dict objects has been declared to be an official part
    # of the Python language spec. Therefore, you can depend on it.
    sep = conf.OUTPUT_FILE_FIELD_SEPARATOR
    with open(output_filename, 'a+', encoding="utf-8", errors='replace') as f:
        static_line = my_dict["filePath"] + sep +\
                     my_dict["fileName"] + sep +\
                     my_dict["chiave_bilancio_filename"] + sep +\
                     my_dict["identifier_filename"] + sep +\
                     my_dict["identifier_xbrl"]
        dynamic_line = ""
        for t in tuple_list:
            dynamic_line = dynamic_line + sep + my_dict[t[1]]
        dynamic_line = dynamic_line + "\n"
        line = static_line + dynamic_line
        f.writelines(line)


def extract_values_from_tags(xbrl_file):
    global conf
    tree = ET.parse(xbrl_file, parser=my_parser)
    root = tree.getroot()
    logger.debug(xbrl_file)
    identifier = root.findtext(
        ".{http://www.xbrl.org/2003/instance}context/{http://www.xbrl.org/2003/instance}entity/{http://www.xbrl.org/2003/instance}identifier")
    identifier = "".join(identifier.split())
    if len(identifier) == 0:
        identifier = "NO_ID_PROVIDED"
        logger.warning("NO_ID_PROVIDED in the identifier tag for the file " + str(xbrl_file))

    # retrieve the namespace
    ns = root.nsmap["itcc-ci"]
    ns = "{" + ns + "}"
    default_value = "null"
    my_dict = {}
    my_dict["filePath"] = xbrl_file
    xbrl_file_name = get_file_name_from_file_path(xbrl_file)
    my_dict["fileName"] = xbrl_file_name

    try:
        chiave_bilancio_filename = xbrl_file_name.split("_")[1]
        my_dict["chiave_bilancio_filename"] = chiave_bilancio_filename
    except IndexError:
        my_dict["chiave_bilancio_filename"] = ""

    try:
        identifier_filename = xbrl_file_name.split("_")[0]
        my_dict["identifier_filename"] = identifier_filename
    except IndexError:
        my_dict["identifier_filename"] = ""

    my_dict["identifier_xbrl"] = identifier

    # collect all contexts in order to associate the correct date to each tag with multiple values
    # such as TotaleImmobilizzazioniImmateriali
    contexts_dict = get_contexts(root)

    global tuple_list
    for t in tuple_list:

        result_list = root.findall(ns + t[0])
        if len(result_list) == 1:
            # è stato trovato un solo tag con il nome specificato
            my_dict[t[1]] = manage_single_tag(result_list)
        else:
            # sia che ci sono più tag con il nome specificato, sia che non ce ne sono proprio
            my_dict[t[1]] = manage_multiple_tags(result_list, contexts_dict)
    append_line_on_output_file(my_dict)


def manage_single_tag(result_list):
    global conf
    tag_value = ""
    if result_list[0].text is not None:
        tag_value = result_list[0].text.strip()
        if conf.ENABLE_HTML_TAG_REMOVAL:
            tag_value = get_html_stripped_version(result_list[0].text.strip())
    return tag_value


def manage_multiple_tags(result_list, contexts_dict):
    global conf
    list_of_values = []
    for elem in result_list:
        elem_children = [element for element in elem.iter() if element is not elem]
        if len(elem_children) == 0:  # elementi che contengono direttamente un valore
            id = elem.attrib.get("contextRef")
            value = ""
            if elem.text is not None:
                value = elem.text.strip()
            if id is not None:
                list_of_values.append(value + "@" + contexts_dict[id])
            else:
                list_of_values.append(value)
        else:  # elementi che contengono sottoelementi da cui estrarre il valore (consalvi)
            child_values = []
            for child in elem_children:
                value = ""
                if child.text is not None:
                    value = child.text.strip()
                child_values.append(value)
            list_of_values.append(":".join(child_values))

    tag_values = (";").join(list_of_values)
    if conf.ENABLE_HTML_TAG_REMOVAL:
        tag_values = get_html_stripped_version((";").join(list_of_values))
    return tag_values


def get_contexts(root):
    contexts_dict = {}
    contexts = root.findall("{http://www.xbrl.org/2003/instance}" + "context")
    for context in contexts:
        id = context.attrib["id"]
        # root.findall(".//{http://www.xbrl.org/2003/instance}context[@id='cntxCorr_d']")
        instants = context.findall(".//{http://www.xbrl.org/2003/instance}period//")
        if len(instants) == 0:
            contexts_dict[id] = "_"
        elif len(instants) == 1:
            instant = ""
            if instants[0].text is not None:
                instant = instants[0].text.strip()
            contexts_dict[id] = instant
        else:  # si suppone che len(instants) sia 2
            start_date = ""
            end_date = ""
            if instants[0].text is not None:
                start_date = instants[0].text.strip()
            if instants[1].text is not None:
                end_date = instants[1].text.strip()
            contexts_dict[id] = start_date + "_" + end_date
    return contexts_dict


def recover_and_retry(xbrl_file):
    logger.warning("\nproblem with the file: " + str(xbrl_file))

    # aggiungo nel file l'intestazione del DTD
    was_modified = modify_file(xbrl_file, util.wrongStart, util.rightStart)
    if was_modified:
        identifier = get_extracted_cf(xbrl_file)
        if identifier != -1:
            return identifier
        else:
            problematic_file_list.append("\t".join([str(xbrl_file), "modified"]))
            line_to_append = "\t".join([str(xbrl_file), "modified"])
            append_line_on_file(problematic_out_filename, line_to_append)
            return -1
    else:
        problematic_file_list.append("\t".join([str(xbrl_file), "original"]))
        line_to_append = "\t".join([str(xbrl_file), "original"])
        append_line_on_file(problematic_out_filename, line_to_append)
        return -2


def modify_file(file_path, pattern, subst):
    # Create temp file
    fh, abs_path = mkstemp()
    try:
        with fdopen(fh, 'w', errors='replace') as new_file:
            with open(file_path, encoding="utf-8", errors='replace') as old_file:
                for line in old_file:

                    if line.startswith("<!-->"):
                        if "<xbrl " not in line:
                            line = "\n" # remove <!-->  XBRLCOMPILER;COMPNAME=Sistemi S.p.A.;COMPCODE=08245660017;TOOL=Gestione Bilanci;VER=2017.5;TS=2017-09-26 11:09:12 </!-->
                        else:
                            # rimuovi il commento errato ad inizio riga quando nella stessa riga c'è anche <xbrl
                            new_line = line.split("<xbrl ")[1]
                            line = "<xbrl " + new_line

                    if pattern in line:
                        try:
                            new_file.write(line.replace(pattern, subst))
                        except UnicodeEncodeError as ude:
                            line = line.encode('utf-8', 'replace').decode('utf-8')
                            line = line.replace('\ufffd', ' ')
                            line = line.replace('\uf0a7', ' ')
                            logger.info("UnicodeEncodeError solved!")
                            new_file.write(line.replace(pattern, subst))
                    else:
                        try:
                            new_file.write(line)
                        except UnicodeEncodeError as ude:
                            line = line.encode('utf-8', 'replace').decode('utf-8')
                            line = line.replace('\ufffd', ' ')
                            line = line.replace('\uf0a7', ' ')
                            logger.info("UnicodeEncodeError solved!")
                            new_file.write(line)

        #  Copy the file permissions from the old file to the new file
        copymode(file_path, abs_path)
        # Remove original file
        # remove(file_path)
        # Rename original file
        # os.rename(file_path, file_path + ".original")

        if not os.path.isfile(file_path + ".original"):
            # solo nel caso in cui già non esiste il file con estensione .original
            os.replace(file_path, file_path + ".original")  # rename and possibly overwrite !

        # Move new file
        move(abs_path, file_path)
        logger.info("File successfully modified !")
        return True
    except FileExistsError as fee:
        logger.error("FileExistsError: " + str(fee.strerror))
        logger.error("File recovery attempt failed !")
        return False
    except Exception as e:
        #logger.debug("error description: " + str(e.msg))
        logger.error("File recovery attempt failed !")
        return False


def load_xbrl_file_list(xbrl_folder_path):
    counter = 0
    xbrl_file_list = []
    for root, dirs, files in os.walk(xbrl_folder_path):
        for file in files:
            if file.endswith(".xbrl"):
                logger.debug(str(counter)+")"+os.path.join(root, file))
                xbrl_file_list.append(os.path.join(root, file))
                counter = counter + 1
    logger.info("Num of xbrl files detected = " + str(counter) + "\n")
    return xbrl_file_list


def load_tuple_list(input_tag_list_file_path):
    tuple_list = []
    with open(input_tag_list_file_path, "rt") as f:
        for line in f.readlines():
            if not line.startswith("#"):
                if len(line.strip()) != 0:
                    pattern = ".+,.+"
                    tokens = line.split(",")
                    if len(tokens) == 2 and re.match(pattern, line):
                        if (" " in str(tokens[0].strip())) or (" " in str(tokens[1].strip())):
                            error_message = "Whitespaces are not allowed in the input tag list file !"
                            logger.error(error_message)
                            sys.exit(error_message)
                        my_tuple = (str(tokens[0].strip()), str(tokens[1].strip()))
                        tuple_list.append(my_tuple)
                    else:
                        error_message = "Each line in the input tag list file must must be in the form: XBRL_tag_name,desired_name_in_output_file"
                        logger.error(error_message)
                        sys.exit(error_message)

    return tuple_list


def get_extracted_cf(xbrl_file):
    try:
        tree = ET.parse(xbrl_file, parser=my_parser)
        root = tree.getroot()
        identifier = root.findtext(
                ".{http://www.xbrl.org/2003/instance}context/{http://www.xbrl.org/2003/instance}entity/{http://www.xbrl.org/2003/instance}identifier")
        logger.debug(identifier)
        return identifier
    except Exception as e:
        logger.debug("error description: " + str(e.msg))
        logger.warning("Unreadable file !")
        return -1


def append_line_on_file(out_filename, line_to_append):
    out_filename = out_filename + "_" + file_date_time + ".txt"
    with open(out_filename, 'a+') as f:
        f.writelines(str(line_to_append))
        f.writelines("\n")
        f.flush()


def get_file_name_from_file_path(file_path):
    if "\\" in file_path:
        return file_path.split("\\")[-1]
    elif "/" in file_path:
        return file_path.split("/")[-1]
    else:
        return file_path


def get_html_stripped_version(html_content):
    soup = BeautifulSoup(html_content, 'html.parser', from_encoding="utf-8")
    stripped_text = soup.get_text(separator=' ')  # remove html tags
    stripped_text = re.sub(r'\s+\t*', ' ', stripped_text)  # replace tabs and multiple spaces with single spaces
    stripped_text = stripped_text.replace("|", " ")  # da rimuovere a regime
    stripped_text = stripped_text.replace("'", " ")  # da rimuovere a regime
    stripped_text = stripped_text.replace('"', ' ')  # da rimuovere a regime
    return stripped_text


if __name__ == "__main__":
    main(sys.argv[1:])


