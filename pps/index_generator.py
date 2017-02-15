from os import listdir
from pickle import load, dump
from math import ceil

from textblob import TextBlob as tb

from pps.helpers.tf_idf_generator import tf, n_containing, idf, tfidf
from pps.bbt import Node

token_map = dict()
corpus_textblobs = dict()
# Term count in corpus
n = 0

def find_two_exponent(number):
    """x4u on Mark Byers -- limit:   v < 2**33"""
    r = 0

    if number > 0xffff : 
        number >>= 16
        r = 16
    if number > 0x00ff :
        number >>=  8
        r += 8
    if number > 0x000f :
        number >>=  4
        r += 4
    if number > 0x0003 : 
        number >>=  2
        r += 2

    return r + (number >> 1)

def load_documents(directory):
    from pps.helpers.text_processor import doc_to_text
    global corpus_textblobs

    files = listdir(directory)

    for filename in files:
        text = doc_to_text(directory + "/" + filename)
        textblob = tb(text)
        corpus_textblobs[filename] = textblob

def generate_token_map():
    global token_map
    global corpus_textblobs
    global n

    index = 0

    for file_content in corpus_textblobs.values():
        for word in file_content.words:
            if word not in token_map:
                token_map[word] = index
                index += 1

    n = len(token_map)

def build_bbt(corpus_textblobs):
    global n

    try:
        current_processing_list = list()

        # For each file to be indexed
        for filename, textblob in corpus_textblobs.items():
            # Calculate score of all words in the textblob corresponding to that file
            word_score_index = {word: tfidf(word, textblob, corpus_textblobs) for word in textblob.words}
            # Index each word into the plain search index
            
            # Create VSM
            vsm = [0] * n

            for word in word_score_index:
                vsm[token_map[word]] = word_score_index[word] 

            # Create node & add to processing list
            file_node = Node(vsm, filename = filename)       
            current_processing_list.append(file_node)
    
        # 2^(Stage) stages of processing for a balanced binary tree
        for stage in range(find_two_exponent(n)):
            new_processing_list = list()

            for i in range(0, len(current_processing_list), 2):
                new_vsm = [ceil(x or y) for x,y in zip(current_processing_list[i].vsm, current_processing_list[i + 1].vsm)]
                new_internal_node = Node(new_vsm, left = current_processing_list[i], right = current_processing_list[i + 1])
                new_processing_list.append(new_internal_node)
            
            current_processing_list = new_processing_list

        root_node = current_processing_list[0]
        # To verify
        print(len(current_processing_list))

    except KeyboardInterrupt:
        pass

def save_object(filename, index):
    with open(filename, "wb") as output:
        dump(index, output, -1)

def load_object(index_file):
    with open(index_file, "rb") as inpt:
        index = load(inpt)
    return index

def start_plain_index_generation(prepared_documents_path):
    print("Generating textblobs...")
    load_documents(prepared_documents_path)
    print("Preparing index...")
    generate_token_map()
