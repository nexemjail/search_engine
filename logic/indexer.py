#!/usr/bin/env python
from natural_language import to_doc_terms
import shelve
from collections import defaultdict
import codecs
import os
import base64
from metadata import INDICES_DIR, CRAWLED_FILES_DIR
import pickle
import sys
import natural_language

#
# class ShelveIndexer(object):
#     def __init__(self, saved_files_directory):
#         self.saved_files_dir = saved_files_directory
#         self.forward_index = None
#         self.inverted_index = defaultdict(list)
#         self.id_to_url = None
#         self.url_to_id = None
#         self.current_id = 0
#         self.index_directory = None
#
#     def start_indexing(self, index_directory):
#         self.index_directory = index_directory
#         self.forward_index = shelve.open(os.path.join(index_directory, 'forward_index'), 'n', writeback=True)
#         self.inverted_index = shelve.open(os.path.join(index_directory, 'inverted_index'), 'n', writeback=True)
#         self.id_to_url = shelve.open(os.path.join(index_directory, 'id_to_url'), 'n', writeback=True)
#
#     def make_index(self):
#         for files_enumerated, filename in enumerate(os.listdir(self.saved_files_dir)):
#             if files_enumerated % 50 == 0:
#                 print 'indexed {} files'.format(files_enumerated)
#             # url is also a filename
#             url = str.decode(base64.b64decode(filename), encoding='utf8')
#             with codecs.open(os.path.join(self.saved_files_dir,filename),'r', encoding='utf16') as f:
#                 raw_text = f.read()
#                 parsed_document = to_doc_terms(raw_text)
#                 self.current_id += 1
#                 self.forward_index[str(self.current_id)] = parsed_document
#                 self.id_to_url[str(self.current_id)] = url
#                 self.url_to_id[str(url)] = self.current_id
#                 for pos, term in enumerate(parsed_document):
#                     self.inverted_index.get(term, []).append((term, pos))
#         self.save_to_disk(INDICES_DIR)
#
#     def sync(self):
#         self.inverted_index.sync()
#         self.forward_index.sync()
#         self.id_to_url.sync()
#
#     def save_to_disk(self):
#         self.inverted_index.close()
#         self.forward_index.close()
#         self.id_to_url.close()
#
#     def load_from_disc(self, index_directory):
#         self.forward_index = shelve.open(os.path.join(index_directory, 'forward_index'), 'r', writeback=True)
#         self.inverted_index = shelve.open(os.path.join(index_directory, 'inverted_index'), 'r', writeback=True)
#         self.id_to_url = shelve.open(os.path.join(index_directory, 'id_to_url'), 'r', writeback=True)
#         self.url_to_id = {v: k for k, v in self.id_to_url.iteritems()}


class ShelveIndexer(object):
    def __init__(self):
        self.saved_files_dir = None
        self.forward_index = None
        self.inverted_index = None
        self.id_to_url = None
        self.current_id = 0

    def start_indexing(self, dir):
        self.forward_index = shelve.open(os.path.join(dir, 'forward_index'), 'n', writeback=True)
        self.inverted_index = shelve.open(os.path.join(dir, 'inverted_index'), 'n', writeback=True)
        self.id_to_url = shelve.open(os.path.join(dir, 'id_to_url'), 'n', writeback=True)

    def make_index(self, saved_files_dir):
        self.saved_files_dir = saved_files_dir
        for files_enumerated, filename in enumerate(os.listdir(self.saved_files_dir)):
            if files_enumerated % 25 == 0:
                print 'indexed {} files'.format(files_enumerated)
            real_filename = str.decode(base64.b64decode(filename), encoding='UTF-8')
            with codecs.open(os.path.join(self.saved_files_dir, filename), 'r', encoding='UTF-16') as f:
                text = f.read()
                doc_terms = to_doc_terms(text)
                self.current_id += 1
                self.id_to_url[str(self.current_id)] = real_filename
                self.forward_index[str(self.current_id)] = doc_terms
                for word_position, term in enumerate(doc_terms):
                    val = (self.current_id, word_position)
                    if self.inverted_index.has_key(term.stem):
                        self.inverted_index[term.stem].append(val)
                    else:
                        self.inverted_index[term.stem] = [val]

    def save_to_file(self):
        self.forward_index.close()
        self.inverted_index.close()
        self.id_to_url.close()
        # def dump_to_file(filename, obj):
        #     with open(os.path.join(dir, filename), 'w') as f:
        #         pickle.dump(obj, f)
        #
        # dump_to_file('forward_indices.pickle', self.forward_index)
        # dump_to_file('inverted_indices.pickle', self.inverted_index)
        # dump_to_file('id_to_url.pickle', self.id_to_url)

    def load_from_file(self, indices_dir):
        backup = sys.modules.get('natural_language', None)
        sys.modules['natural_language'] = natural_language

        self.forward_index = shelve.open(os.path.join(indices_dir, 'forward_index'), 'r', writeback=True)
        self.inverted_index = shelve.open(os.path.join(indices_dir, 'inverted_index'), 'r', writeback=True)
        self.id_to_url = shelve.open(os.path.join(indices_dir, 'id_to_url'), 'r', writeback=True)
        print len(self.inverted_index)
        if backup is None:
            del sys.modules['natural_language']
        else:
            sys.modules['natural_language'] = backup


class Indexer(object):
    def __init__(self):
        self.saved_files_dir = None
        self.forward_index = dict()
        self.inverted_index = defaultdict(list)
        self.id_to_url = dict()
        self.current_id = 0

    def make_index(self, saved_files_dir):
        self.saved_files_dir = saved_files_dir
        for files_enumerated, filename in enumerate(os.listdir(self.saved_files_dir)):
            if files_enumerated % 25 == 0:
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
        backup = sys.modules.get('natural_language', None)
        sys.modules['natural_language'] = natural_language

        def load_from_file(filename):
            with open(os.path.join(dir, filename), 'r') as f:
                obj = pickle.load(f)
            return obj

        self.forward_index = load_from_file('forward_indices.pickle')
        self.inverted_index = load_from_file('inverted_indices.pickle')
        self.id_to_url = load_from_file('id_to_url.pickle')
        if backup is None:
            del sys.modules['natural_language']
        else:
            sys.modules['natural_language'] = backup

if __name__ == '__main__':
    # saved_files_dir = '/media/files/programming/search_engine/crawled_dir'
    indexer = ShelveIndexer()
    indexer.start_indexing(INDICES_DIR)
    indexer.make_index(CRAWLED_FILES_DIR)
    indexer.save_to_file()
    # indexer = Indexer()
    # indexer.make_index(CRAWLED_FILES_DIR)
    # indexer.save_to_file(INDICES_DIR)
    # # indexer.load_from_file(INDICES_DIR)