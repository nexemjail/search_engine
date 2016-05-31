#!/usr/bin/env python
from natural_language import to_doc_terms
import shelve
from collections import defaultdict
import codecs
import os
import base64
from metadata import INDICES_DIR
import json


class ShelveIndexer(object):
    def __init__(self, saved_files_directory):
        self.saved_files_dir = saved_files_directory
        self.forward_index = None
        self.inverted_index = defaultdict(list)
        self.id_to_url = None
        self.url_to_id = None
        self.current_id = 0
        self.index_directory = None

    def start_indexing(self, index_directory):
        self.index_directory = index_directory
        self.forward_index = shelve.open(os.path.join(index_directory, 'forward_index'), 'n', writeback=True)
        self.inverted_index = shelve.open(os.path.join(index_directory, 'inverted_index'), 'n', writeback=True)
        self.id_to_url = shelve.open(os.path.join(index_directory, 'id_to_url'), 'n', writeback=True)

    def make_index(self):
        for files_enumerated, filename in enumerate(os.listdir(self.saved_files_dir)):
            if files_enumerated % 50 == 0:
                print 'indexed {} files'.format(files_enumerated)
            # url is also a filename
            url = str.decode(base64.b64decode(filename), encoding='utf8')
            with codecs.open(os.path.join(self.saved_files_dir,filename),'r', encoding='utf16') as f:
                raw_text = f.read()
                parsed_document = to_doc_terms(raw_text)
                self.current_id += 1
                self.forward_index[str(self.current_id)] = parsed_document
                self.id_to_url[str(self.current_id)] = url
                self.url_to_id[str(url)] = self.current_id
                for pos, term in enumerate(parsed_document):
                    self.inverted_index.get(term, []).append((term, pos))
        self.save_to_disk(INDICES_DIR)

    def sync(self):
        self.inverted_index.sync()
        self.forward_index.sync()
        self.id_to_url.sync()

    def save_to_disk(self):
        self.inverted_index.close()
        self.forward_index.close()
        self.id_to_url.close()

    def load_from_disc(self, index_directory):
        self.forward_index = shelve.open(os.path.join(index_directory, 'forward_index'), 'r', writeback=True)
        self.inverted_index = shelve.open(os.path.join(index_directory, 'inverted_index'), 'r', writeback=True)
        self.id_to_url = shelve.open(os.path.join(index_directory, 'id_to_url'), 'r', writeback=True)
        self.url_to_id = {v: k for k, v in self.id_to_url.iteritems()}


class Indexer(object):
    def __init__(self, saved_files_directory):
        self.saved_files_dir = saved_files_directory
        self.forward_index = dict()
        self.inverted_index = defaultdict(list)
        self.id_to_url = dict()
        self.current_id = 0

    def make_index(self):
        for files_enumerated, filename in enumerate(os.listdir(self.saved_files_dir)):
            if files_enumerated % 25 == 0:
                print 'indexed {} files'.format(files_enumerated)
            real_filename = str.decode(base64.b64decode(filename), encoding='UTF-8')
            with codecs.open(os.path.join(self.saved_files_dir, filename), 'r', encoding='UTF-16') as f:
                text = f.read()
                words = to_doc_terms(text)
                self.current_id += 1
                self.id_to_url[self.current_id] = real_filename
                self.forward_index[self.current_id] = words
                for word_position, word in enumerate(words):
                    self.inverted_index[word].append([self.current_id, word_position])

    def save_to_file(self, dir):

        def dump_to_file(filename, obj):
            with open(os.path.join(dir, filename), 'w') as f:
                json.dump(obj, f, indent=4)

        dump_to_file('forward_indices.json', self.forward_index)
        dump_to_file('inverted_indices.json', self.inverted_index)
        dump_to_file('id_to_url.json', self.id_to_url)


if __name__ == '__main__':
    saved_files_dir = '/media/files/programming/search_engine/crawled_dir'
    indexer = ShelveIndexer(saved_files_dir)
    indexer.start_indexing(INDICES_DIR)
    indexer.make_index()
    indexer.save_to_disk()

    # indexer = Indexer(saved_files_dir)
    # indexer.make_index()
    # indexer.save_to_file(INDICES_DIR)