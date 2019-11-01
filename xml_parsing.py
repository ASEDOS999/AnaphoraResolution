import xml.etree.ElementTree as ET

def extract_dataset(name_file):
	tree = ET.parse(name_file)
	root = tree.getroot()
	for doc in root:
		print(dir(doc))
		print(doc.tag, doc.attrib)
		for chain in doc:
			print('new_chain')
			for child in chain:
				print(child.tag, child.attrib, child.text)
				for cont in child:
					print(cont.text)
if __name__ == '__main__':
	extract_dataset('LearnSet/anaph_new.xml')
