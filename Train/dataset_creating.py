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
		if not parent is None:
			morph = parent.morph
			for i in morph:
				new_elem['ParentMorph:'+i] = morph[i]
		return new_elem
	new_dataset = dict()
	for i in dataset:
		ant, anaph = dataset[i]
		new_ant, new_anaph = [], []
		for j in ant:
			new_ant.append(transform(j))
		for j in anaph:
			new_anaph.append(transform(j))
		new_dataset[i] = new_ant, new_anaph
	return new_dataset

def create_binarizator(dataset):
	def get_features(some_list):
		features = dict()
		for i in some_list:
			for j in i:
				features[j] = []
		for i in some_list:
			for key in features:
				if key in i:
					if type(i[key]) == list:
						features[key] += i[key]
					elif type(i[key]) == str:
						features[key].append(i[key])
		features = {i:list({j:[] for j in features[i]}.keys()) for i in features}
		return features
	name_f = 'binarizator.pickle'
	if name_f in os.listdir('../'):
		return None
	ant, anaph = [], []
	for i in dataset:
		ant1, anaph1 = dataset[i]
		ant += ant1
		anaph += anaph1
	feat = get_features(ant), get_features(anaph)
	f = open('../' + name_f, 'wb')
	pickle.dump(feat, f)
	f.close()
	return feat

def binarize(dataset):
	def transform_elem(elem , features):
		new_elem = dict()
		for i in features:
			if len(features[i]) == 0:
				new_elem[i] = elem[i]
			else:
				for j in features[i]:
					new_elem[i+':'+j] = int(elem[i]==j)
		return new_elem
	def transform(some_list, features):
		return [transform_elem(i, features) for i in some_list]
	f = open('../binarizator.pickle')
	feat_ant, feat_anaph = pickle.load(f)
	f.close()
	new_dataset = {}
	for i in dataset:
		ant, anaph = dataset[i]
		new_ant = transform(ant, feat_ant)
		new_feat = transform(anaph, feat_anaph)
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
				if not (num_ant, num_anaph) in matching:
					negative_samples.append((key, i,j))
	return positive_samples, negative_samples


def train_dataset(dataset, matching):
	positive_samples, negative_samples = get_marking(dataset, matching)
	f = open('pos.pickle', 'wb')
	pickle.dump(positive_samples, f)
	f.close()
	f = open('neg.pickle', 'wb')
	pickle.dump(negative_samples, f)
	f.close()
	return None

def condition_gender(ant, anaph):
	key = 'TokenMorph:Gender'
	if key in ant and key in anaph and anaph['TokenMorph:fPOS'] == 'PRON':
		mark = ant[key] == anaph[key]
		if anaph[key] in _ and ant[key] in _:
			mark = True
		if anaph['TokenLemma'] == 'свой':
			mark = True
	else:
		mark = True
	return mark

def get_candidates(dataset):
	for i in dataset:
		ant, anaph = dataset[i]
		start = 0
		cand_list = []
		for j in anaph:
			sent_num = j['sent_num']
			candidates = []
			while sent_num - ant[start] > 3:
				start += 1
			if sent_num-ant[start] < 0:
				candidates.append(ant[start])
			ind = start
			while 0 <= sent_num - ant[ind]['sent_num'] <= 3:
				ind += 1
				if condition_gender(ant[ind], j):
					candidates.append(ant[ind])
			cand_list.append(candidates)
		dataset[i] = (cand_list, anaph)
	return dataset

if __name__ == '__main__':
	folder = 'LearnSet/AnaphFiles/'
	print('Number Of Files',len(get_all_files(folder)))
	dataset_from_xml = xml_parsing.extract_dataset('LearnSet/anaph_new.xml')
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
		my_dataset = transform_dataset(my_dataset)
		f = open(name_pickle, 'wb')
		pickle.dump(my_dataset, f)
		f.close()
	create_binarizator(my_dataset)
