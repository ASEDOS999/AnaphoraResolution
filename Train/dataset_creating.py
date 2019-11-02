import sys
import os
sys.path.append('..')
import xml_parsing
import anaphora_resolution
import pickle
import threading

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

import time
def get_dataset(files):
	def process_text(file, dataset):
		f = open(file, 'r')
		text  = f.read()
		dataset[file] = anaphora_resolution.get_antecedent_anaphor(text)
		f.close()
	dataset = dict()
	t = []
	s = time.time()
	for file in files:
		t.append(threading.Thread(target = process_text, args = (file, dataset)))
	for thread in t:
		thread.start()
	for thread in t:
		thread.join()
	print(time.time()-s)
	return dataset

if __name__ == '__main__':
	folder = '../LearnSet/AnaphFiles/'
	print('Number Of Files',len(get_all_files(folder)))
	dataset_from_xml = xml_parsing.extract_dataset('../LearnSet/anaph_new.xml')
	files = dataset_from_xml.keys()
	files = [folder + i for i in files]
	print('Number Of Files In xml-file', len(files))
	name_pickle = 'our_dataset.pickle'
	try:
		f = open(name_pickle, 'rb')
		my_dataset = pickle.load(f)
		f.close()
	except:
		my_dataset = get_dataset(files)
		f = open(name_pickle, 'wb')
		pickle.dump(my_dataset, f)
		f.close()

