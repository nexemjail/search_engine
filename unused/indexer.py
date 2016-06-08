from collections import defaultdict
import pickle
import base64
import codecs
import os
from logic.natural_language import to_doc_terms

class Indexer(object):
    def __init__(self):
        self.saved_files_dir = None
        self.forward_index = dict()
        self.inverted_index = defaultdict(list)
        self.id_to_url = dict()
        self.current_id = 0
        self.current_part = 0

    def make_index(self, saved_files_dir):
        self.saved_files_dir = saved_files_dir
        for files_enumerated, filename in enumerate(os.listdir(self.saved_files_dir)):
            print 'indexed {} files'.format(files_enumerated)
            real_filename = str.decode(base64.b64decode(filename), encoding='UTF-8')
            with codecs.open(os.path.join(self.saved_files_dir, filename), 'r', encoding='UTF-16') as f:
                text = f.read()
                doc_terms = to_doc_terms(text)
                self.current_id += 1
                self.id_to_url[str(self.current_id)] = real_filename
                self.forward_index[str(self.current_id)] = doc_terms
                for word_position, term in enumerate(doc_terms):
                    self.inverted_index[term.stem].append([self.current_id, word_position])

    def save_to_file(self, dir):
        def dump_to_file(filename, obj):
            with open(os.path.join(dir, filename), 'w') as f:
                pickle.dump(obj, f)

        dump_to_file('forward_indices.pickle', self.forward_index)
        dump_to_file('inverted_indices.pickle', self.inverted_index)
        dump_to_file('id_to_url.pickle', self.id_to_url)

    def load_from_file(self, dir):
        # backup = sys.modules.get('natural_language', None)
        # sys.modules['natural_language'] = natural_language

        def load_from_file(filename):
            with open(os.path.join(dir, filename), 'r') as f:
                obj = pickle.load(f)
            return obj

        self.forward_index = load_from_file('forward_indices.pickle')
        self.inverted_index = load_from_file('inverted_indices.pickle')
        self.id_to_url = load_from_file('id_to_url.pickle')
        # if backup is None:
        #     del sys.modules['natural_language']
        # else:
        #     sys.modules['natural_language'] = backup