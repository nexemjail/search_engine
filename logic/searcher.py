import json
import os
from logic.metadata import INDICES_DIR
from collections import defaultdict
from natural_language import to_query_terms
from logic.indexer import Indexer


class Searcher(object):
    def __init__(self, indices_directory, index_implementation):
        self.indices = index_implementation()
        self.indices_directory = indices_directory
        self.indices.load_from_file(indices_directory)

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
        query_terms = to_query_terms(query_words)
        for query_term in query_terms:
            for doc_id, position in self.indices.inverted_index.get(query_term.stem, []):
                doc_ids.add(doc_id)
        return doc_ids

    def generate_snippet(self, doc_id, query_words):

        document = self.indices.forward_index[str(doc_id)]
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
        return '{} {} {}'.format(pre_ellipsis, ' '.join(
            map(lambda term: term.full_word.encode('utf8'), document[begin_index:end_index])), post_ellipsis)

    def get_url(self, doc_id):
        return self.indices.id_to_url[str(doc_id)]

if __name__ == '__main__':
    # from searcher import Searcher
    from metadata import INDICES_DIR

    # searcher = Searcher(INDICES_DIR, Indexer)
    searcher = Searcher(INDICES_DIR, Indexer)
    docs = searcher.find_document_OR('animal')
    print docs
