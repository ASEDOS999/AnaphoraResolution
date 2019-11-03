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
				if j != 'context' and not 'Token' in j:
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
	_ = ['Mask', 'Neut']
	if key in ant and key in anaph and anaph['TokenMorph:fPOS'] == 'PRON':
		mark = ant[key] == anaph[key]
		if anaph[key] in _ and ant[key] in _:
			mark = True
		if anaph['TokenLemma'] == 'свой':
			mark = True
	else:
		mark = True
	return mark

def get_candidates(dataset, lim = 3):
	for i in dataset:
		ant, anaph = dataset[i]
		start = 0
		candidates = []
		for j in anaph:
			sent_num = j['sent_num']
			while sent_num - ant[start]['sent_num'] > lim:
				start += 1
			if sent_num-ant[start]['sent_num'] < 0:
				candidates.append((ant[start],j))
			ind = start
			while ind < len(ant) and 0 <= sent_num - ant[ind]['sent_num'] <= lim:
				if condition_gender(ant[ind], j):
					candidates.append((ant[ind], j))
				ind += 1
		dataset[i] = candidates
	return dataset

def find_in_xml(pair, xml_dataset):
	mark = -1
	for j in xml_dataset:
		if 'answer' in j and 'anaphor' in j:
			ant, anaph = j['answer']['attr'], j['anaphor']['attr']

			start, ln = int(ant['sh']), int(ant['ln'])
			start_ant, end_ant = start, start+ln
			mark_ant = start_ant >= pair[0]['start_symb'] and end_ant <= pair[0]['end_symb']

			start, ln = int(anaph['sh']), int(anaph['ln'])
			start_anaph, end_anaph = start, start+ln
			mark_anaph = start_anaph >= pair[1]['start_symb'] and end_anaph <= pair[1]['end_symb']
			if mark_anaph and mark_ant:
				return 1
			if mark_anaph:
				mark = 0
	return mark

def get_matching_for_candidates(dataset, xml_dataset):
	for i in dataset:
		key = '/'.join(i.split('/')[-2:])
		cur, xml_ = dataset[i], xml_dataset[key]
		new = []
		for pair in cur:
			mark = find_in_xml(pair, xml_)
			new.append((pair, mark))
		dataset[i] = new
	return dataset

def binarize_pair(pair):
	def transform_elem(elem , features):
		new_elem = dict()
		for i in features:
			if i in elem:
				if len(features[i]) == 0:
					new_elem[i] = elem[i]
				else:
					for j in features[i]:
						new_elem[i+':'+j] = int(elem[i]==j)
			else:
				if len(features[i]) == 0:
					new_elem[i] = 0
				else:
					for j in features[i]:
						new_elem[i+':'+j] = 0
		return new_elem
	f = open('../binarizator.pickle', 'rb')
	feat_ant, feat_anaph = pickle.load(f)
	f.close()
	ant, anaph = pair
	new_ant = transform_elem(ant, feat_ant)
	new_anaph = transform_elem(anaph, feat_anaph)
	return new_ant, new_anaph

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
	dataset_candidates = get_candidates(my_dataset)
	marking_dataset = get_matching_for_candidates(dataset_candidates, dataset_from_xml)
	all, pos = 0, 0
	for i in marking_dataset:
		marking_dataset[i] = [j for j in marking_dataset[i] if j[1] >= 0]
	for i in marking_dataset:
		cur = marking_dataset[i]
		all += len([i for i in cur if i[1] > -1])
		pos += len([i for i in cur if i[1] == 1])
	print(all, pos, pos/all)
	binarize_dataset = {j : [(binarize_pair(i[0]),i[1]) for i in marking_dataset[j]] for j in marking_dataset}
