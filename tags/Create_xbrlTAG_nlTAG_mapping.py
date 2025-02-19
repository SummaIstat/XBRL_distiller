import xml.etree.ElementTree as ET
from lxml import etree

my_parser = etree.XMLParser(load_dtd=True, dtd_validation=False, encoding="UTF-8")
xsd_file = "C:/py/XBRL_distiller/tags/2018-11-04/itcc-ci-2018-11-04.xsd"
xml_file = "C:/py/XBRL_distiller/tags/2018-11-04/itcc-ci-lab-it-2018-11-04.xml"
output_file = "xbrlTag_nlTag_mapping.csv"


def extract_attribute_value_from_xsd(xsd_file, attribute_name):
    #tree = ET.parse(xsd_file)
    tree = ET.parse(xsd_file, parser=my_parser)
    root = tree.getroot()
    attribute_value_list = []

    for element in root.iter():
        if "element" in element.tag:  # consider just "element" elements
            if attribute_name in element.attrib.keys():
                attribute_value = element.attrib[attribute_name]
                attribute_value_list.append(attribute_value)
                #print(attribute_value)
    return attribute_value_list


def extract_labels_from_xml(xml_file, my_dict):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    attribute_value_list = []

    for element in root.iter():
        if element.tag.split("}")[1] == "label":  # consider just "label" elements
            label_id = element.attrib["{http://www.w3.org/1999/xlink}label"]
            role = element.attrib["{http://www.w3.org/1999/xlink}role"].split("/")[-1]
            tag_id = label_id[:-4]
            if role == "label":
                my_dict[tag_id][2] = element.text
            elif role == "verboseLabel":
                my_dict[tag_id][3] = element.text
    return my_dict


def write_list_to_file(file_path, string_list):
    with open(file_path, "w", encoding="UTF-8") as file:
        for string in string_list:
            file.write(string + "\n")


def write_mapping_to_file(file_path, my_dict):
    with open(file_path, "w") as file:
        file.write("tag_id" + "\t" + "tag_name" + "\t" + "tag_label_id" + "\t" + "tag_nl_label" + "\t" + "tag_nl_verbose_label" + "\n")
        for key in my_dict.keys():
            file.write(str(key) + "\t" + str(my_dict[key][0]) + "\t" + str(my_dict[key][1]) + "\t" + str(my_dict[key][2]) + "\t" + str(my_dict[key][3]) + "\n")




# Step 1: get all the ids and names of the xbrl tags
id_list = extract_attribute_value_from_xsd(xsd_file, "id")
name_list = extract_attribute_value_from_xsd(xsd_file, "name")

# Step 2: add the suffix "_lbl" to each id collected
label_id_list = [x + "_lbl" for x in id_list]
my_dict = {}
for i, id in enumerate(id_list):
    my_dict[id] = [name_list[i], label_id_list[i], "", ""]

# Step 3: retrieve the label and the verbose label values from the xml file
my_dict = extract_labels_from_xml(xml_file, my_dict)

# Step 4: write the mapping to file
write_mapping_to_file(output_file, my_dict)
