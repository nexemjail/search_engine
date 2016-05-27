import json
import os

from logic.metadata import INDICES_DIR


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

    def find_document(self, words):
        return sum([self.inverted_index[word] for word in words], [])

    def get_url(self, doc_id):
        return self.id_to_url[unicode(doc_id)]



if __name__ == '__main__':

    searcher = Searcher(INDICES_DIR)