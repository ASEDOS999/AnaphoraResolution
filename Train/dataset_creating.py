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
	s = time.time()
	for file in files:
		process_text(file,dataset)
	return dataset

def transform_dataset(dataset):
	def transform(elem):
		new_elem = {}
		attention = ['subtree', 'parent_value']
		for i in elem:
			if not i in attention:
				new_elem[i] = elem[i]
		new_elem['TokenLemma'] = elem['subtree'].value.lemma
		morph = elem['subtree'].value.morph
		for i in morph:
			new_elem['TokenMorph:'+i] = morph[i]
		parent = elem['parent_value']
		morph = parent.morph
		for i in morph:
			new_elem['ParentMorph:'+i] = morph[i]
		return new_elem
	new_dataset = dict()
	for i in dataset:
		ant, anaph = dataset[i]
		new_ant, new_anaph = [], []
		for j in ant:
			new_ant.append(transform(i))
		for j in anaph:
			new_anaph.append(transform(i))
		new_dataset[i] = new_ant, new_anaph
	return new_dataset

def contains(words, xml_obj):
	attrib = xml_obj['attr']
	start, ln = int(attrib['sh']), int(attrib['ln'])
	end = start + ln
	def equal(word, start = start, end = end):
		cur_start, cur_end = word['start_symb'], word['end_symb']
		return cur_start>=start and cur_end<=end
	for ind, word in enumerate(words):
		if equal(word):
			return ind
	return None

def get_matching_one(dataset, xml_dataset, key):
	antecedents, anaphors = dataset
	res = list()
	for i in xml_dataset:
		if 'answer' in i and 'anaphor' in i:
			num_ant = contains(antecedents, i['answer'])
			num_anaph = contains(anaphors, i['anaphor'])
			if not (num_ant is None or num_anaph is None):
				res.append((key, num_ant, num_anaph))
	return res

def get_matching(our_dataset, xml_dataset):
	res = list()
	for i in xml_dataset:
		key = '../LearnSet/AnaphFiles/' + i
		if key in our_dataset:
			res += (get_matching_one(our_dataset[key], xml_dataset[i], key))
	return res

import pandas as pd
def get_marking(dataset, matching):
	positive_samples = []
	for i in matching:
		key, num_ant, num_anaph = i
		ant, anaph = dataset[key]
		positive_samples.append((key, ant[num_ant], anaph[num_anaph]))
	negative_samples = []
	for key in dataset:
		ant, anaph = dataset[key]
		print(len(ant), len(anaph), len(ant)*len(anaph))
		for num_ant, i in enumerate(ant):
			for num_anaph, j in enumerate(anaph):
				if (num_ant, num_anaph) in matching:
					negative_samples.append((key, i,j))
	return positive_samples, negative_samples


def train_dataset(dataset, matching):
	positive_samples, negative_samples = get_marking(dataset, matching)
	print(positive_samples[:1])
	return None

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
	match = get_matching(my_dataset, dataset_from_xml)
	print(len(match))
	train_dataset(my_dataset, match)
