import sys
import os
sys.path.append('..')
import xml_parsing
import anaphora_resolution


def get_all_files(folder, files = None):
	if files is None:
		files = []
	for i in os.listdir(folder):
		cur_name = folder + i
		if os.path.isdir(cur_name):
			files = get_all_files(cur_name + '/', files)
		else:
			files.append(cur_name)
	return files

def get_dataset(folder):
	files = (get_all_files(folder))
	dataset = dict()
	for file in files:
		f = open(file)
		text  = f.read()
		dataset[file] = anaphora_resolution.get_antecedent_anaphor(text)
		f.close()
	return dataset


if __name__ == '__main__':
	folder = '../LearnSet/TestSet/'
	my_dataset = get_dataset(folder)
	dataset_from_xml = xml_parsing.extract_dataset('../LearnSet/anaph_new.xml')
	print(files[:10])
	print(dataset_from_xml)
