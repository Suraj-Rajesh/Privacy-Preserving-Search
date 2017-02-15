from do_parser import *
from collections import defaultdict
from textblob import TextBlob as tb
import cPickle as pickle
from tf_idf_generator import tf, n_containing, idf, tfidf
from paillier.paillier import *
from crypto import load_keys
from datetime import datetime
import random

def load_documents(directory, corpus_textblobs):
    files = listdir(directory)
    for f in files:
        text = doc_to_text(directory + "/" + f)
        textblob = tb(text)
        corpus_textblobs[f] = textblob

def plain_index_generator(corpus_textblobs):
    try:
        # Log indexing start
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_file = open("../logs/index_log", "w")
        log_file.write(start_time)
        log_file.close()

        count = 1
        plain_index = defaultdict(dict)
        # For each file to be indexed
        for filename, textblob in corpus_textblobs.iteritems():
            print str(count)
            # Calculate score of all words in the textblob corresponding to that file
            word_score_index = {word: tfidf(word, textblob, corpus_textblobs) for word in textblob.words}
            # Index each word into the plain search index
            for word in word_score_index:
                plain_index[word][filename] = word_score_index[word]
            count = count + 1
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_index("../index/plain_index.pkl", plain_index)
        with open("../logs/index_log", "a") as log_file:
                log_file.write(end_time)
                log_file.close()
    except KeyboardInterrupt:
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_index("../index/plain_index.pkl", plain_index)
        with open("../logs/index_log", "a") as log_file:
                log_file.write(end_time)
                log_file.close()

def mask_encrypt(value, offset, public_key):
    offseted = int(value * 100000) + offset
    encrypted_value = encrypt(public_key, offseted)
    return encrypted_value

def encrypted_index_generator(plain_index_file):
    (priv_key, pub_key) = load_keys("../keys/private_key.pkl", "../keys/public_key.pkl")
    plain_index = load_index(plain_index_file)
    # For logging
    # Total no of keywords in plain index
    no_keywords = len(plain_index)
    processing = 1
    offset = random.randint(50, 100)
    for keyword, keyword_index in plain_index.iteritems():
        print "Encrypting " + str(processing) + " of " + str(no_keywords)
        for filename, tf_idf in keyword_index.iteritems():
            plain_index[keyword][filename] = mask_encrypt(tf_idf, offset, pub_key)
        processing = processing + 1
    save_index("../index/encrypted_index.pkl", plain_index)

def save_index(filename, index):
    with open(filename, "wb") as output:
        pickle.dump(index, output, -1)

def load_index(index_file):
    with open(index_file, "rb") as inpt:
        index = pickle.load(inpt)
    return index

def generate_plain_index_driver():
    corpus_textblobs = dict()
    print "Generating textblobs..."
    load_documents("../corpus/prepared_documents", corpus_textblobs)
    print "Preparing index..."
    plain_index_generator(corpus_textblobs)

def generate_encrypted_index_driver():
    encrypted_index_generator("../index/plain_index.pkl")
