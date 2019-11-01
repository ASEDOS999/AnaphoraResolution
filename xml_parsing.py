import xml.etree.ElementTree as ET

def extract_dataset(name_file):
	tree = ET.parse(name_file)
	root = tree.getroot()
	for doc in root:
		for child in doc:
			print(child.tag, child.attr)
