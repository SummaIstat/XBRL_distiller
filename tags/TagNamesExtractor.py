import xml.etree.ElementTree as ET


def extract_attribute_value(xml_file, attribute_name):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    attribute_value_list = []

    for element in root.iter():
        if "element" in element.tag:
            if attribute_name in element.attrib.keys():
                attribute_value = element.attrib[attribute_name]
                attribute_value_list.append(attribute_value)
                print(attribute_value)
    return attribute_value_list


def write_list_to_file(file_path, string_list):
    with open(file_path, "w") as file:
        for string in string_list:
            file.write(string + "\n")


xml_file = "C:/py/XBRL_distiller/tags/2018-11-04/itcc-ci-2018-11-04.xsd___"
output_file = "xbrl_full_tag_list.txt"
attribute_name = "name"

attribute_value_list = extract_attribute_value(xml_file, attribute_name)
sorted_list = sorted(attribute_value_list)
write_list_to_file(output_file, sorted_list)