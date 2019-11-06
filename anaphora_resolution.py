from isanlp import PipelineCommon
from isanlp.processor_remote import ProcessorRemote
from isanlp.ru.converter_mystem_to_ud import ConverterMystemToUd

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
			res.append((root, append))
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
