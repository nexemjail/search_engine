import os
import json
import base64
import codecs
from collections import defaultdict
from metadata import INDICES_DIR

class Indexer(object):
    def __init__(self, saved_files_directory):
        self.saved_files_dir = saved_files_directory
        self.forward_index = dict()
        self.inverted_index = defaultdict(list)
        self.id_to_url = dict()
        self.current_id = 0

    def make_index(self):
        for filename in os.listdir(self.saved_files_dir):
            real_filename = str.decode(base64.b64decode(filename), encoding='UTF-8')
            with codecs.open(os.path.join(self.saved_files_dir, filename), 'r', encoding='UTF-16') as f:
                text = f.read()
                words = list(filter(lambda word: not word.isspace(), text.split()))
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
    indexer = Indexer(saved_files_dir)
    indexer.make_index()
    indexer.save_to_file(INDICES_DIR)
