from isanlp import PipelineCommon
from isanlp.processor_remote import ProcessorRemote
from isanlp.ru.converter_mystem_to_ud import ConverterMystemToUd
import numpy as np
import pandas as pd
import time

class tree:
	def __init__(self, value, sentence = None):
		self.value = value
		self.kids = []
		self.sentence = None

	def add_child(self, value, mytype = None):
		self.kids.append((value, mytype))

class word:
	def __init__(self, lemma, postag, morph, begin , end, index, role = None):
		self.lemma = lemma
		self.postag = postag
		self.morph = morph
		self.index = index
		self.begin = begin
		self.end = end
		self.role = role
		self.anaphor_resolution = None
		
def get_tree(text):
	from isanlp import PipelineCommon
	from isanlp.processor_remote import ProcessorRemote
	from isanlp.ru.converter_mystem_to_ud import ConverterMystemToUd
	from Parser.some_reparser import extract_semantic_relations
	HOST = 'localhost'
	proc_morph = ProcessorRemote(HOST, 3333, 'default')
	proc_syntax = ProcessorRemote(HOST, 3334, '0')

	syntax_ppl = PipelineCommon([
		(proc_morph,
			['text'],
			{'tokens' : 'tokens', 'sentences' : 'sentences', 'postag' : 'postag', 'lemma' : 'lemma'}),
		(proc_syntax,
			['tokens','sentences'],
			{'syntax_dep_tree' : 'syntax_dep_tree'}),
		(ConverterMystemToUd(),
			['postag'],
			{'postag' : 'postag', 'morph' : 'morph'})
		])
	try:
		analysis_res = syntax_ppl(text)
	except:
		return None
	sentences = []
	for i in analysis_res['sentences']:
		sentence = []
		for j in range(i.begin, i.end):
			sentence.append(analysis_res['tokens'][j].text)
		sentences.append(sentence)
	vertices_list_list = []
	relations = extract_semantic_relations(text)
	for j in range(len(analysis_res['lemma'])):
		vertices_list = []
		for i in range(len(analysis_res['lemma'][j])):
			start, end = analysis_res['tokens'][i].begin, analysis_res['tokens'][i].end
			role_vert = []
			for rel in relations:
				if rel['child']['start'] == start and rel['child']['end'] == end:
					role_vert.append(rel['tp'])
			vert = tree(word(analysis_res['lemma'][j][i],
					analysis_res['postag'][j][i],
					analysis_res['morph'][j][i],
					start, end,
					i,
					role = role_vert))
			vertices_list.append(vert)
		vertices_list_list.append(vertices_list)
	root_list = []
	for i in range(len(vertices_list_list)):
		list_ = vertices_list_list[i]
		for j in range(len(analysis_res['syntax_dep_tree'][i])):
			_ = analysis_res['syntax_dep_tree'][i][j]
			if _.parent != -1:
				list_[_.parent].add_child(list_[j], _.link_name)
			else:
				list_[j].sentence = sentences[i]
				root_list.append(list_[j])
	return root_list

def get_subtree(root, postag = 'NOUN', res = None, parent = (None, None)):
	if res is None:
		res = list()
	lemma_list = ['он', 'она', 'они', 'оно']
	lemma_list += ['этот', 'тот', 'такой']
	if root.value.postag == postag:
		if postag == 'PRON':
			if root.value.lemma in lemma_list:
				res.append((root, parent))
		else:
			res.append((root, parent))
	for i in root.kids:
		res = get_subtree(i[0], postag, res, (root.value, i[1]))
	return res

def separation_to_sentences(text):
	list_points = []
	for ind,i in enumerate(text):
		if i in ['?', '.', '!', '\n']:
			list_points.append(ind)
	_, ind = [], 0
	while ind < len(list_points):
		while ind<len(list_points)-1 and list_points[ind+1] - list_points[ind] == 1:
			ind += 1
		_.append(list_points[ind])
		ind+=1
	list_points = [-1] + _
	if list_points[-1] != len(text)-1:
		list_points[-1] = len(text)
	sentences = [text[i+1:list_points[ind+1]+1] for ind, i in enumerate(list_points[:-1])]
	sentences = [(i, len(i.split())) for i in sentences]
	return sentences

def get_antecedents(root, ind, s, s1, sent):
	nouns_subtrees = get_subtree(root, postag = 'NOUN')
	cur_res = []
	for root_subtree in nouns_subtrees:
		root_subtree, parent = root_subtree
		cur_res.append({'subtree' : root_subtree,
			'sent_num' : ind,
			'index_text' : s + root_subtree.value.index,
			'index_sent' : root_subtree.value.index,
			'start_symb' : s1 + root_subtree.value.begin,
			'end_symb' : s1 + root_subtree.value.end,
			'parent_value' : parent[0],
			'dependence' : parent[1],
			'role' : root_subtree.value.role,
			'context' : sent,
			})
	return cur_res

def get_anaphors(root, ind, s, s1, sent):
	pron_subtrees = get_subtree(root, postag = 'PRON')
	cur_res = []
	for root_subtree in pron_subtrees:
		root_subtree, parent = root_subtree
		cur_res.append({'subtree' : root_subtree,
			'sent_num' : ind,
			'index_text' : s + root_subtree.value.index,
			'index_sent' : root_subtree.value.index,
			'start_symb' : s1 + root_subtree.value.begin,
			'end_symb' : s1 + root_subtree.value.end,
			'parent_value' : parent[0],
			'dependence' : parent[1],
			'role' : root_subtree.value.role,
			'context' : sent
			})
	return cur_res

def get_antecedent_anaphor(text):
	sentences = separation_to_sentences(text)
	antecedents, anaphors = [], []
	s, s1 = 0, 0
	for ind, item in enumerate(sentences):
		sentence, num_token = item
		root = get_tree(sentence)
		if not root is None and len(root) > 0:
			root = root[0]
			sent = (root.sentence)
			antecedents = antecedents + get_antecedents(root, ind, s, s1, sent)
			anaphors = anaphors + get_anaphors(root, ind, s, s1, sent)
		s += num_token
		s1 += len(sentence)
	return antecedents, anaphors

def get_dataset(files):
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
	def process_text(file, dataset):
		f = open(file, 'r')
		text  = f.read()
		dataset[file] = get_antecedent_anaphor(text)
		f.close()
	dataset = dict()
	s = time.time()
	for file in files:
		print(file)
		process_text(file,dataset)
	return transform_dataset(dataset)
	
def create_binarizator(dataset):
	def get_features(some_list, token = False):
		features = dict()
		for i in some_list:
			for j in i:
				if j != 'context' and (not 'Token' in j or token):
					features[j] = []
		for i in some_list:
			for key in features:
				if key in i:
					if not('TokenLemma' in key and i['TokenMorph:fPOS'] != 'PRON'):
						if type(i[key]) == list:
							features[key] += i[key]
						elif type(i[key]) == str:
							features[key].append(i[key])
		features = {i:list({j:[] for j in features[i]}.keys()) for i in features}
		return features
	name_f = 'binarizator.pickle'
	if name_f in os.listdir('../'):
		return None
	print('CreateBinarizator')
	ant, anaph = [], []
	for i in dataset:
		ant1, anaph1 = dataset[i]
		ant += ant1
		anaph += anaph1
	feat = get_features(ant), get_features(anaph, True)
	f = open('../' + name_f, 'wb')
	pickle.dump(feat, f)
	f.close()
	print(len(feat[0]), len(feat[1]))
	return feat
	
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

def create_DataFrame(pairs):
	def process_one_file(pairs):
		try:
			f = open('keys.pickle', 'rb')
			keys_ant, keys_anaph = pickle.load(f)
			f.close()
		except:
			keys_ant = pairs[0][0]
			keys_anaph = pairs[0][1]
			keys_ant = ['Ant:'+i for i in keys_ant]
			keys_anaph = ['Anaph:'+i for i in keys_anaph]
			keys_ant.sort()
			keys_anaph.sort()
			f = open('keys.pickle', 'wb')
			pickle.dump((keys_ant, keys_anaph), f)
			f.close()
		keys = keys_ant + keys_anaph
		df = {i:[] for  i in keys}
		for i in pairs:
			anaph, ant = i[1], i[0]
			for key in keys_anaph:
				key_ = ':'.join(key.split(':')[1:])
				df[key].append(anaph[key_])
			for key in keys_ant:
				key_ = ':'.join(key.split(':')[1:])
				df[key].append(ant[key_])
		return pd.DataFrame.from_dict(df)[keys]
	my_dataset = get_dataset(files)
	create_binarizator(my_dataset)
	dataset_candidates = get_candidates(my_dataset)
	binarize_dataset = {j : [binarize_pair(i[0]) for i in marking_dataset[j]] for j in marking_dataset}
	dataset = {i:process_one_file(binarize_dataset[i]) for i in binarize_dataset}
	return dataset

def anaphora_resolve(pairs, model):
	return np.argmax(model.predict_proba(pairs))
