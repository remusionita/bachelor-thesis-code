#!/usr/bin/env python3


"""
Module to manage creation of input features/labels and Embeddings
"""


from abc import ABC, abstractmethod
from gensim.models import KeyedVectors
from numpy import array as nparray
from numpy import random, zeros
from tqdm import tqdm
import pymagnitude as magnitude


class Embeddings(ABC):
    """
    Abstract Base Class for Word Embeddings.
    This class should implement the polymorph function embeddings() to producs Embeddings from a list of tokens
    """

    padding_marker = '__PADDING__'

    def __init__(self, dimensions):
        """
        :param int dimensions: Dimensions of the Word Embedding Vectors
        :return: Embeddings Object
        """

        self.dimensions = dimensions
        super().__init__()

    @abstractmethod
    def embeddings(self, tokens):
        """
        This method will take a list of tokens and returns a list of Word Embeddings with the same size.

        :param list tokens: List of tokens to transform into Embeddings
        """

        raise NotImplementedError


class DummyEmbeddings(Embeddings):
    """
    Generates random numpy arrays as embeddings for development
    """

    def embeddings(self, tokens):
        """
        This method will take a list of tokens and returns a list of Dummy Word Embeddings with the same size.

        :param list tokens: List of tokens to transform into Embeddings
        :return: List of numpy arrays with given dimensions
        """

        return_list = []

        for token in tokens:
            if token == Embeddings.padding_marker:
                return_list.append(zeros(self.dimensions))
            else:
                return_list.append(random.rand(self.dimensions))

        return return_list


class Word2Vec(Embeddings):
    """
    Handles the GoogleNews Word2Vec vectors
    https://code.google.com/archive/p/word2vec/
    """

    def __init__(self, filepath='source/GoogleNews-vectors-negative300.bin', dimensions=300):
        """
        Load the pretrained Word2Vec vectors

        :param string filename: Path to gensim Keyedvectors file as *.bin
        :param int dimensions: Dimensions of the Vectors (to generate zeros for padding)
        """

        self.dimensions = dimensions
        self.word2vec = KeyedVectors.load_word2vec_format(filepath, binary=True)

    def embeddings(self, tokens):
        """
        Transforms a list of tokens into a list of embeddings

        :param list tokens: List of tokens to transform into Embeddings
        :return: List of Word2Vec embeddings for given tokens
        """

        return_list = []

        for token in tokens:
            if token in self.word2vec:
                return_list.append(self.word2vec[token])
            elif token == Embeddings.padding_marker:
                return_list.append(zeros(self.dimensions))
            else:
                # TODO: Add option to find most_similar
                # TODO: I could also save random vectors so they are constant accross corpora
                return_list.append(random.rand(self.dimensions))

        return return_list


class Magnitudes(Embeddings):
    """
    Handles the Embeddings using pymagnitude
    https://github.com/plasticityai/magnitude
    """

    def __init__(self, filepath='source/wiki-news-300d-1M-subword.magnitude', dimensions=300):
        """
        Load the pretrained Embeddings

        :param string filename: Path to pymagnitude file as *.magnitude
        :param int dimensions: Dimensions of the Vectors (to generate zeros for padding)
        """

        self.dimensions = dimensions
        self.filepath = filepath
        self.vectors = magnitude.Magnitude(filepath)

    def embeddings(self, tokens):
        """
        Transforms a list of tokens into a list of embeddings

        :param list tokens: List of tokens to transform into Embeddings
        :return: List of embeddings for given tokens
        """

        return_list = []
        for token in tokens:
            if token == Embeddings.padding_marker:
                return_list.append(zeros(self.dimensions))
            elif token in self.vectors:
                vec = self.vectors.query(token)
                return_list.append(vec)
            else:
                # Magnitude could find most similar, but it takes a while
                return_list.append(random.rand(self.dimensions))

        return return_list


def add_padding(tokens, max_len=50, pad_value='__PADDING__', split_if_too_long=True):
    """
    Pad a list of tokens with value to max_len length.
    Uses the given pad_value to produce dummy tokens for padding

    :param list tokens: List of tokens to add padding to
    :param int max_len: Maximum length of the new padded list
    :param string value: Value to use for padding
    :param bool split_if_too_long: Split lists if they are too long
    :return: List of tokens with padding at the end
    """

    # TODO: Implement split_if_too_long
    if len(tokens) <= max_len:
        # Append value to end of short token list
        return tokens + [pad_value] * (max_len - len(tokens))
    elif len(tokens) >= max_len:
        # Cutoff if sentence is too long
        return tokens[0:max_len]

    return tokens


def compile_input_and_labels_for_sentence(sentence, Vectors, max_len=50):
    """
    Adds padding to the sentence tokens and labels

    :param list sentences: List of sentnces to generated labels from
    :param Embeddings vectors: Embeddings instance to generate embeddings from
    :param int max_len: Maximum length of sentences
    :return: Tuple containing:
    x_inputs as list of Embeddings for a given sentence,
    y_labels as list of labels for a given sentence
    """

    x_inputs = []
    y_labels = []

    # Unpack tuples and pad the sequence to a fixed length
    padded_sentence_tokens = add_padding([token[0] for token in sentence], max_len=max_len)
    padded_sentence_labels = add_padding([token[1] for token in sentence], pad_value=-1, max_len=max_len)

    x_inputs = Vectors.embeddings(padded_sentence_tokens)
    y_labels = padded_sentence_labels

    return x_inputs, y_labels


def generate_input_and_labels(sentences, Vectors, max_len=50):
    """
    Takes a list of sentences and returns a list of
    - Input data x (list of tokens)
    - Corresponding labels y (list of labels)

    :param list sentences: list sentences as list of tuples
    :param Embeddings vectors: Embeddings instance to generate embeddings from
    :param int max_len: Maximum length of the new padded list
    :return: Tuple containing:
    numpy array x, list of lists containing sentences as embeddings
    numpy array y, list if lists containing labels for sentences in x
    """

    list_of_x = []
    list_of_y = []

    for sentence in tqdm(sentences):
        x, y = compile_input_and_labels_for_sentence(sentence, Vectors, max_len=max_len)
        list_of_x.append(x)
        list_of_y.append(y)

    return nparray(list_of_x), nparray(list_of_y)
