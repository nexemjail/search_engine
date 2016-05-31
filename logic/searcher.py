from __future__ import unicode_literals
import json
import os
from logic.metadata import INDICES_DIR
from collections import defaultdict
from natural_language import to_query_terms

class Searcher(object):
    def __init__(self, indices_directory):
        self.indices_dir = indices_directory
        self.inverted_index = dict()
        self.forward_index = dict()
        self.id_to_url = dict()
        self._load_json()

    def _load_json(self):
        def load_json(filename):
            with open(os.path.join(self.indices_dir, filename), 'r') as f:
                return json.load(f)

        self.inverted_index = load_json('inverted_indices.json')
        self.forward_index = load_json('forward_indices.json')
        self.id_to_url = load_json('id_to_url.json')

    def find_document(self, query_words):
        return sum([self.inverted_index[word] for word in to_query_terms(query_words)], [])

    def find_document_AND(self, query_words):
        query_words_in_document = defaultdict(set)
        query_words_count = len(query_words)
        for word in to_query_terms(query_words):
            for doc_id, position in self.inverted_index.get(word, []):
                query_words_in_document[doc_id].add(word)
        return [doc_id for doc_id, unique_hits in query_words_in_document.items()
                if len(unique_hits) == query_words_count]

    def find_document_OR(self, query_words):
        doc_ids = set()
        for query_word in to_query_terms(query_words):
            for doc_id, position in self.inverted_index.get(query_word, []):
                doc_ids.add(doc_id)
        return doc_ids

    def generate_snippet(self, doc_id, query_words):

        document = self.forward_index[str(doc_id)]
        query_terms_in_window = []
        shortest_window_length = len(document)
        best_window = []
        best_words_in_window = 0

        for pos, word in enumerate(document):
            if word in to_query_terms(query_words):
                query_terms_in_window.append((word, pos))
                if len(query_terms_in_window) > 1 and query_terms_in_window[0][0] == word:
                    query_terms_in_window.pop(0)
                current_window_len = pos - query_terms_in_window[0][1] + 1
                window_width = len(set(query_terms_in_window))
                if window_width > best_words_in_window \
                    or (window_width == best_words_in_window
                        and current_window_len < shortest_window_length):
                    best_window = list(query_terms_in_window)
                    shortest_window_length = current_window_len

        begin_index = max(0, best_window[0][1] - 10)
        end_index = min(len(document), (best_window[len(best_window)-1][1] + 1) + 10)
        pre_ellipsis = '...'
        post_ellipsis = '...'
        if begin_index == 0:
            pre_ellipsis = ''
        if end_index == len(document):
            post_ellipsis = ''
        return '{} {} {}'.format(pre_ellipsis, ' '.join(document[begin_index:end_index]), post_ellipsis)

    def get_url(self, doc_id):
        return self.id_to_url[str(doc_id)]

if __name__ == '__main__':
    searcher = Searcher(INDICES_DIR)
    docs = searcher.find_document_OR(['hi', 'kun'])
