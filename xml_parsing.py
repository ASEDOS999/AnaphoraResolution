import xml.etree.ElementTree as ET

def extract_inform_from_chain(chain):
	data = dict()
	keys = ['answer', 'anaphor']
	for ind, child in enumerate(chain):
		attr = child.attrib
		text = [cont.text for cont in child][0]
		data[keys[ind]] = {'text' : text, 'attr' : attr}
	return data

def extract_dataset(name_file):
	tree = ET.parse(name_file)
	root = tree.getroot()
	res = dict()
	for doc in root:
		name_doc = doc.attrib['file']
		cur_list = []
		for chain in doc:
			cur_list.append(extract_inform_from_chain(chain))
		res[name_doc] = cur_list
	return res


if __name__ == '__main__':
	dataset = extract_dataset('LearnSet/anaph_new.xml')
	print('Documents Number', len(dataset.keys()))
	s = 0
	for i in dataset:
		s += len(i)
	print('Chains Number', s)
