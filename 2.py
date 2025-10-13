import xml.etree.ElementTree as ET

def parse_xml_descriptions(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    descriptions = []

    for event in root.findall(".//Event"):
        desc = event.find("Description")
        if desc is not None and desc.text:
            descriptions.append(desc.text.strip())
    
    return descriptions