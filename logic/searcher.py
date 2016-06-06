from metadata import INDICES_DIR
from logic.metadata import INDICES_DIR
from collections import defaultdict
from natural_language import to_query_terms
from logic.indexer import ShelveIndexer
import sys
import natural_language
import time
import multiprocessing


def _generate_snippet((document, query_words)):
    query_terms = to_query_terms(query_words)
    query_terms_in_window = []
    shortest_window_length = len(document) - 1
    best_window = []
    terms_count_in_best_window = 0
    # print 'length of document ', len(document)
    t1 = time.time()
    for pos, term in enumerate(document):
        if term in query_terms:
            query_terms_in_window.append((term, pos))
            if len(query_terms_in_window) > 1 and query_terms_in_window[0][0] == term:
                query_terms_in_window.pop(0)
            current_window_len = pos - query_terms_in_window[0][1] + 1
            window_width = len(set(map(lambda x: x[0], query_terms_in_window)))
            if window_width > terms_count_in_best_window \
                    or (window_width == terms_count_in_best_window
                        and current_window_len < shortest_window_length):
                best_window = list(query_terms_in_window)
                shortest_window_length = current_window_len
                terms_count_in_best_window = window_width

    # print 'generating snippet itself took ', time.time() - t1

    begin_index = max(0, best_window[0][1] - 10)
    end_index = min(len(document), (best_window[len(best_window) - 1][1] + 1) + 10)
    # pre_ellipsis = '...'
    # post_ellipsis = '...'
    # if begin_index == 0:
    #     pre_ellipsis = ''
    # if end_index == len(document):
    #     post_ellipsis = ''
    snippet = [(term.full_word, True) if term in query_terms else (term.full_word, False)
               for term in document[begin_index: end_index]]
    return snippet


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
            if query_term.stem in self.indices.inverted_index.keys():
                id_pos_array = self.indices.inverted_index[query_term.stem]
            else:
                id_pos_array = []
            for doc_id, position in id_pos_array:
                doc_ids.add(doc_id)
        return doc_ids

    def generate_snippets(self, doc_ids, query_words):
        if 'natural_language' not in sys.modules:
            sys.modules['natural_language'] = natural_language
        # print 'extracting {} docs'.format(len(doc_ids))
        # documents = {tuple(self.indices.forward_index[str(doc_id)]) for doc_id in doc_ids[:70]}
        current_index = 0
        step = 80
        documents_count = len(doc_ids)
        pool = multiprocessing.Pool()
        snippets = []
        while current_index < documents_count:
            end_index = current_index + step
            if end_index > documents_count:
                end_index = documents_count

            fetched_docs = [self.indices.forward_index[str(doc_id)] for doc_id in doc_ids[current_index: end_index]]
            documents_and_query_words = zip(fetched_docs, [query_words] * len(fetched_docs))
            snippets.extend(pool.map(_generate_snippet, documents_and_query_words))
            # pool.close()
            # pool.join()
            current_index += step
        pool.close()
        pool.join()с
        return snippets

    def generate_snippet(self, doc_id, query_words):
        # print list(self.indices.forward_index.keys())
        # print 'generating snippet for {}'.format(doc_id)
        # backup = sys.modules.get('natural_language', None)
        if 'natural_language' not in sys.modules:
            sys.modules['natural_language'] = natural_language

        t1 = time.time()
        document = self.indices.forward_index[str(doc_id)][:]
        # print 'loading document from shelve ', time.time() - t1
        query_terms = to_query_terms(query_words)
        query_terms_in_window = []
        shortest_window_length = len(document) - 1
        best_window = []
        terms_count_in_best_window = 0
        # print 'length of document ', len(document)
        t1 = time.time()
        for pos, term in enumerate(document):
            if term in query_terms:
                query_terms_in_window.append((term, pos))
                if len(query_terms_in_window) > 1 and query_terms_in_window[0][0] == term:
                    query_terms_in_window.pop(0)
                current_window_len = pos - query_terms_in_window[0][1] + 1
                window_width = len(set(map(lambda x: x[0], query_terms_in_window)))
                if window_width > terms_count_in_best_window \
                    or (window_width == terms_count_in_best_window
                        and current_window_len < shortest_window_length):
                    best_window = list(query_terms_in_window)
                    shortest_window_length = current_window_len
                    terms_count_in_best_window = window_width

        # print 'generating snippet itself took ', time.time() - t1

        begin_index = max(0, best_window[0][1] - 10)
        end_index = min(len(document), (best_window[len(best_window)-1][1] + 1) + 10)
        # pre_ellipsis = '...'
        # post_ellipsis = '...'
        # if begin_index == 0:
        #     pre_ellipsis = ''
        # if end_index == len(document):
        #     post_ellipsis = ''
        snippet = [(term.full_word, True) if term in query_terms else (term.full_word, False)
                   for term in document[begin_index: end_index]]
        return snippet
        # return '{} {} {}'.format(pre_ellipsis, ' '.join(
        #     map(lambda term: term.full_word.encode('utf8'), document[begin_index:end_index])), post_ellipsis)

    def get_url(self, doc_id):
        return self.indices.id_to_url[str(doc_id)]

if __name__ == '__main__':
    # from searcher import Searcher
    # searcher = Searcher(INDICES_DIR, Indexer)
    searcher = Searcher(INDICES_DIR, ShelveIndexer)
    docs = searcher.find_document_OR('bepop')
    print docs
