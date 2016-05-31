from natural_language import to_doc_terms
import shelve
import codecs
import base64
import os
import sys
from metadata import INDICES_DIR
from collections import defaultdict
from natural_language import to_query_terms

# class Indexer(object):
#     def __init__(self, saved_files_directory):
#         self.saved_files_dir = saved_files_directory
#         self.forward_index = dict()
#         self.inverted_index = defaultdict(list)
#         self.id_to_url = dict()
#         self.current_id = 0
#
#     def make_index(self):
#         for files_enumerated, filename in enumerate(os.listdir(self.saved_files_dir)):
#             if files_enumerated % 25 == 0:
#                 print 'indexed {} files'.format(files_enumerated)
#             real_filename = str.decode(base64.b64decode(filename), encoding='UTF-8')
#             with codecs.open(os.path.join(self.saved_files_dir, filename), 'r', encoding='UTF-16') as f:
#                 text = f.read()
#                 words = to_doc_terms(text)
#                 self.current_id += 1
#                 self.id_to_url[self.current_id] = real_filename
#                 self.forward_index[self.current_id] = words
#                 for word_position, word in enumerate(words):
#                     self.inverted_index[word].append([self.current_id, word_position])
#
#     def save_to_file(self, dir):
#
#         def dump_to_file(filename, obj):
#             with open(os.path.join(dir, filename), 'w') as f:
#                 json.dump(obj, f, indent=4)
#
#         dump_to_file('forward_indices.json', self.forward_index)
#         dump_to_file('inverted_indices.json', self.inverted_index)
#         dump_to_file('id_to_url.json', self.id_to_url)


class ShelveIndexer(object):
    def __init__(self):
        self.forward_index = None
        self.inverted_index = defaultdict(list)
        self.id_to_url = None
        self.url_to_id = dict()
        self.current_id = 0
        self.index_directory = None

    def start_indexing(self, index_directory):
        self.index_directory = index_directory
        self.forward_index = shelve.open(os.path.join(index_directory, 'forward_index'), 'n', writeback=True)
        self.inverted_index = shelve.open(os.path.join(index_directory, 'inverted_index'), 'n', writeback=True)
        self.id_to_url = shelve.open(os.path.join(index_directory, 'id_to_url'), 'n', writeback=True)

    def make_index(self, saved_files_dir):
        for files_enumerated, filename in enumerate(os.listdir(saved_files_dir)):
            if files_enumerated % 10 == 0:
                print 'indexed {} files'.format(files_enumerated)
            # url is also a filename
            url = base64.b64decode(filename)
            with codecs.open(os.path.join(saved_files_dir,filename),'r', encoding='utf16') as f:
                raw_text = f.read()
                parsed_document = to_doc_terms(raw_text)
                self.current_id += 1
                self.forward_index[str(self.current_id)] = parsed_document
                self.id_to_url[str(self.current_id)] = url
                self.url_to_id[url] = self.current_id
                for pos, term in enumerate(parsed_document):
                    stem = term.stem
                    if stem not in self.inverted_index:
                        self.inverted_index[stem] = []
                    self.inverted_index[stem].append((self.current_id, pos))
                    # self.inverted_index.get(term, []).append((term, pos))
        self.save_to_disk()

    def sync(self):
        self.inverted_index.sync()
        self.forward_index.sync()
        self.id_to_url.sync()

    def save_to_disk(self):
        self.inverted_index.close()
        self.forward_index.close()
        self.id_to_url.close()

    def load_from_disk(self, index_directory):
        self.forward_index = shelve.open(os.path.join(index_directory, 'forward_index'), writeback=True)
        self.inverted_index = shelve.open(os.path.join(index_directory, 'inverted_index'), writeback=True)
        self.id_to_url = shelve.open(os.path.join(index_directory, 'id_to_url'), writeback=True)
        self.url_to_id = {v: k for k, v in self.id_to_url.iteritems()}
        print self.inverted_index.__len__()

    def get_document_terms(self, doc_id):
        return self.forward_index[str(doc_id)]

    def get_url(self, doc_id):
        return self.id_to_url[str(doc_id)]


class Searcher(object):
    def __init__(self, indices_directory, indices_implementation):

        self.indices = indices_implementation()
        self.indices.load_from_disk(indices_directory)
        print 'LOADING DONE'
        # print self.indices.inverted_index
        #
        # self.indices_dir = indices_directory
        # self.inverted_index = dict()
        # self.forward_index = dict()
        # self.id_to_url = dict()
        # self._load_json()
    #
    # def _load_json(self):
    #     def load_json(filename):
    #         with open(os.path.join(self.indices_dir, filename), 'r') as f:
    #             return json.load(f)
    #
    #     self.inverted_index = load_json('inverted_indices.json')
    #     self.forward_index = load_json('forward_indices.json')
    #     self.id_to_url = load_json('id_to_url.json')

    def find_document(self, query_words):
        return sum([self.indices.inverted_index[word] for word in to_query_terms(query_words)], [])

    def find_document_AND(self, query_words):
        query_words_in_document = defaultdict(set)
        query_words_count = len(query_words)
        for word in to_query_terms(query_words):
            for doc_id, position in self.indices.inverted_index.get(word, []):
                query_words_in_document[doc_id].add(word)
        return [doc_id for doc_id, unique_hits in query_words_in_document.items()
                if len(unique_hits) == query_words_count]

    def find_document_OR(self, query_words):
        doc_ids = set()
        for term in to_query_terms(query_words):
            if term.stem in self.indices.inverted_index:
                for doc_id, position in self.indices.inverted_index.get(term.stem, []):
                    doc_ids.add(doc_id)
        return doc_ids

    def generate_snippet(self, doc_id, query_words):
        print sys.modules.keys()
        document_terms = self.indices.get_document_terms(doc_id)
        query_terms_in_window = []
        shortest_window_length = len(document_terms)
        best_window = []
        best_words_in_window = 0

        for pos, term in enumerate(document_terms):
            if term in to_query_terms(query_words):
                query_terms_in_window.append((term, pos))
                if len(query_terms_in_window) > 1 and query_terms_in_window[0][0] == term:
                    query_terms_in_window.pop(0)
                current_window_len = pos - query_terms_in_window[0][1] + 1
                window_width = len(set(query_terms_in_window))
                if window_width > best_words_in_window \
                    or (window_width == best_words_in_window
                        and current_window_len < shortest_window_length):
                    best_window = list(query_terms_in_window)
                    shortest_window_length = current_window_len

        begin_index = max(0, best_window[0][1] - 10)
        end_index = min(len(document_terms), (best_window[len(best_window)-1][1] + 1) + 10)
        pre_ellipsis = '...'
        post_ellipsis = '...'
        if begin_index == 0:
            pre_ellipsis = ''
        if end_index == len(document_terms):
            post_ellipsis = ''
        return '{} {} {}'.format(pre_ellipsis, ' '.join(map(lambda term: term.full_word, document_terms[begin_index: end_index])), post_ellipsis)

    def get_url(self, doc_id):
        return self.indices.forward_index[str(doc_id)]


if __name__ == '__main__':
    pass
    # if not os.path.exists(INDICES_DIR):
    #     os.mkdir(INDICES_DIR)
    # indexer = ShelveIndexer()
    # indexer.start_indexing(INDICES_DIR)
    # indexer.make_index(CRAWLED_FILES_DIR)
    # indexer.save_to_disk()

    searcher = Searcher(INDICES_DIR, ShelveIndexer)
    print searcher.find_document_OR('bepop group')
    #
    # indexer = ShelveIndexer(CRAWLED_FILES_DIR)
    # indexer.load_from_disc(INDICES_DIR)

    # indexer = Indexer(saved_files_dir)
    # indexer.make_index()
    # indexer.save_to_file(INDICES_DIR)