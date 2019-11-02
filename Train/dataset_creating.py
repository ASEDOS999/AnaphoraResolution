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
			files = get_all_files(cur_name, files)
		else:
			files.append(cur_name)
	return files

if __name__ == '__main__':
	files = (get_all_files('../LearnSet/TestSet/'))
	print(files[:10])
