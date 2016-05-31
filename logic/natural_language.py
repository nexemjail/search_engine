from nltk.stem import WordNetLemmatizer
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import sent_tokenize, TreebankWordTokenizer
from nltk.corpus import stopwords
import itertools
import string
_stopwords = stopwords.words('english')


class Term(object):
    def __init__(self, full_word):
        self.full_word = full_word
        self.stem = str(PorterStemmer().stem(full_word).lower().encode('utf8'))

    def __eq__(self, other):
        return self.stem == other.stem

    def __hash__(self):
        return hash(self.stem)

    def __repr__(self):
        return 'Term {}: {}'.format(self.stem.encode('utf8'),
                                    self.full_word.encode('utf8'))

    def __str__(self):
        return self.__repr__()

    def is_punctuation(self):
        return self.stem in string.punctuation

    def is_stop_word(self):
        return self.full_word in _stopwords


def stem_and_tokenize(text):
    sents = sent_tokenize(text)
    tokens = list(itertools.chain(*[TreebankWordTokenizer().tokenize(sent) for sent in sents]))
    terms = [Term(token) for token in tokens]
    return filter(lambda term: not term.is_punctuation(), terms)


def to_query_terms(raw_query):
    return stem_and_tokenize(raw_query)


def to_doc_terms(doc_raw):
    return stem_and_tokenize(doc_raw)


if __name__ == '__main__':
    # print stem_and_tokenize('lelouche math')
    import nltk
    nltk.download('stopwords')
