#!/usr/bin/env python
from natural_language import to_doc_terms
import shelve
import codecs
import os
import base64
from metadata import INDICES_DIR, CRAWLED_FILES_DIR,\
        ALTCHARS , INDEX_WIKI,\
        CRAWLED_FILES_DIR_WIKI,\
        INDEX_WIKI_MINI, H,\
        CRAWLED_FILES_DIR_WIKI_NEW
import pickle
import sys
import natural_language
from collections import defaultdict
sys.modules['natural_language'] = natural_language


class ShelveIndexer(object):
    def __init__(self, index_directory= None):
        self.saved_files_dir = None
        self.forward_index = None
        self.inverted_index = None
        self.id_to_url = None
        self.data = None
        self.current_id = 0
        self.index_dir = index_directory
        self.current_block_id = 0
        self.url_to_id = None

    def start_indexing(self, directory):
        self.index_dir = directory
        self.data = shelve.open(os.path.join(directory, 'data'), 'n', writeback=True)
        self.forward_index = shelve.open(os.path.join(directory, 'forward_index'), 'n', writeback=True)
        self.inverted_index = shelve.open(os.path.join(directory, 'inverted_index'), 'n', writeback=True)
        self.id_to_url = shelve.open(os.path.join(directory, 'id_to_url'), 'n', writeback=True)
        self.url_to_id = {v: k for k, v in self.id_to_url.iteritems()}

    def sync(self):
        print 'Syncing...'
        self.inverted_index.sync()
        self.forward_index.sync()
        self.id_to_url.sync()
        self.data.sync()
        print 'Synced!'

    def _create_new_block(self):
        if self.inverted_index:
            self.inverted_index.close()
        self.inverted_index = shelve.open(os.path.join(
            self.index_dir, 'inverted_index_block_0{}'.format(self.current_block_id)),
            'n', writeback=True)
        self.current_block_id += 1

    def _merge_blocks(self):
        blocks = [shelve.open(
            os.path.join(self.index_dir,
                         'inverted_index_block_0{}'.format(i)))
                            for i in xrange(self.current_block_id)]
        keys = set()

        for block in blocks:
            keys |= set(block.keys())
        print 'keys count ', len(keys)
        merged_index = shelve.open(os.path.join(self.index_dir, 'inverted_index'),'n')
        for key in keys:
            print 'merging ', key
            merged_index[key] = sum([block.get(key,[]) for block in blocks], [])
        merged_index.close()

    def add_document(self, text, url):
        self.current_id = len(self.forward_index.keys())
        self.current_id += 1
        self._add_document(text, url)
        print 'Added {}'.format(url)
        self.sync()

    def _add_document(self, text, url):

        insert_index = self.current_id
        if url in self.url_to_id:
            insert_index = self.url_to_id[url]
        doc_terms = to_doc_terms(text)
        self.id_to_url[str(insert_index)] = url
        self.url_to_id[url] = str(insert_index)
        self.forward_index[str(insert_index)] = doc_terms
        for word_position, term in enumerate(doc_terms):
            if term.is_stop_word():
                continue
            val = (insert_index, word_position)
            if term.stem in self.inverted_index:
                self.inverted_index[term.stem].append(val)
            else:
                self.inverted_index[term.stem] = [val]
        if 'total_doc_length' in self.data:
            self.data['total_doc_length'] += len(doc_terms)
        else:
            self.data['total_doc_length'] = len(doc_terms)

    def make_index(self, saved_files_dir):
        self.saved_files_dir = saved_files_dir
        for files_enumerated, filename in enumerate(os.listdir(self.saved_files_dir)):
            if files_enumerated % 200 == 0:
                self.sync()
                self._create_new_block()
            if files_enumerated % 5 == 0:
                print 'indexed {} files'.format(files_enumerated)

            # TODO : replace it
            real_filename = str.decode(base64.b64decode(filename, ALTCHARS), encoding='UTF-8')
            with codecs.open(os.path.join(self.saved_files_dir, filename), 'r', encoding='utf8') as f:
                text = f.read()
                self.current_id += 1
                self._add_document(text, real_filename)

    def save_to_file(self):
        self._merge_blocks()
        self.forward_index.close()
        self.inverted_index.close()
        self.id_to_url.close()
        self.data.close()

    def get_avg_doc_length(self):
        return float(self.data['total_doc_length']) / self.get_total_docs_count()

    def get_doc_length(self, doc_id):
        return len(self.forward_index[str(doc_id)])

    def get_document(self, doc_id):
        return self.forward_index[str(doc_id)]

    def get_total_docs_count(self):
        if self.current_id == 0:
            self.current_id = len(self.forward_index)
        return self.current_id

    def load_from_file(self, indices_dir):
        # backup = sys.modules.get('natural_language', None)
        # sys.modules['natural_language'] = natural_language
        print 'LOADING!'
        self.data = shelve.open(os.path.join(indices_dir, 'data'), 'r', writeback=True)
        self.forward_index = shelve.open(os.path.join(indices_dir, 'forward_index'), 'r', writeback=True)
        self.inverted_index = shelve.open(os.path.join(indices_dir, 'inverted_index'), 'r', writeback=True)
        self.id_to_url = shelve.open(os.path.join(indices_dir, 'id_to_url'), 'r', writeback=True)
        self.url_to_id = {v: k for k, v in self.id_to_url.iteritems()}
        print 'LOADED!'
        # print len(self.forward_index)
        # if backup is None:
        #     del sys.modules['natural_language']
        # else:
        #     sys.modules['natural_language'] = backup


if __name__ == '__main__':
    # saved_files_dir = '/media/files/programming/search_engine/crawled_dir'
    indexer = ShelveIndexer(H)
    indexer.start_indexing(H)
    indexer.make_index(CRAWLED_FILES_DIR_WIKI_NEW)
    indexer.save_to_file()
    # indexer._merge_blocks()
    # indexer = Indexer()
    # indexer.make_index(CRAWLED_FILES_DIR)
    # indexer.save_to_file(INDICES_DIR)
    # # indexer.load_from_file(INDICES_DIR)