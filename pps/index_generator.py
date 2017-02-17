from os import listdir
from random import randint

from textblob import TextBlob as tb

from pps.bbt import Node
from pps.helpers.tf_idf_generator import tf, n_containing, idf, tfidf
from pps.helpers.operations import load_object, save_object, generate_random_invertible_matrix, get_transpose, get_inverse, matrix_multiplication, vsm_hash_to_vsm

token_map = dict()
corpus_textblobs = dict()
secret = list()
# Term count in corpus
n = 0

# Encryption matrices
m1t = 0
m2t = 0
m1i = 0
m2i = 0

def find_two_exponent(number):
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

def generate_token_map_and_secret(index_directory, key_directory):
    global token_map
    global corpus_textblobs
    global n
    global secret

    index = 0

    for file_content in corpus_textblobs.values():
        for word in file_content.words:
            if word not in token_map:
                token_map[word] = [index, idf(word, corpus_textblobs)]
                index += 1

    n = len(token_map)

    # Generate secret
    secret = [randint(0, 1) for i in range(n)]

    save_object(index_directory + "/token_map.pkl", token_map)
    save_object(key_directory + "/secret.pkl", secret)

def create_vsm_hash(vsm_hash_1, vsm_hash_2):
    builder_set = set()
    new_vsm_hash = dict()

    for key in vsm_hash_1.keys():
        builder_set.add(key)

    for key in vsm_hash_2.keys():
        builder_set.add(key)

    new_vsm_hash = list(builder_set)
    return new_vsm_hash

def encrypt_vsm(vsm_hash):
    global n
    global secret
    global m1t
    global m2t

    encrypted_vsm_hash_1 = vsm_hash
    encrypted_vsm_hash_2 = vsm_hash

    for index in range(len(secret)):
        if secret[index] == 1:
            if index in vsm_hash:
                # Split randomly such that their addition equals the original value
                encrypted_vsm_hash_1[index] = vsm_hash[index]/(randint(2, 6))
                encrypted_vsm_hash_2[index] = vsm_hash[index] - encrypted_vsm_hash_1[index]

    encrypted_vsm_hash_1 = matrix_multiplication(m1t, vsm_hash_to_vsm(n, encrypted_vsm_hash_1))
    encrypted_vsm_hash_2 = matrix_multiplication(m2t, vsm_hash_to_vsm(n, encrypted_vsm_hash_2))

    return (encrypted_vsm_hash_1, encrypted_vsm_hash_2)


def build_bbt(corpus_textblobs, index_directory):
    global n

    try:
        current_processing_list = list()

        # For each file to be indexed
        for filename, textblob in corpus_textblobs.items():
            # Calculate score of all words in the textblob corresponding to that file
            word_score_index = {word: tfidf(word, textblob, corpus_textblobs) for word in textblob.words}
            # Index each word into the plain search index
           
            vsm_hash = dict()

            for word in word_score_index:
                vsm_hash[token_map[word][0]] = word_score_index[word] 

            # Encrypt vsm hash of file node, create file node & add to processing list
            (encrypted_vsm_hash_1, encrypted_vsm_hash_2) = encrypt_vsm(vsm_hash)

#            encrypted_vsm_hash_1 = None
#            encrypted_vsm_hash_2 = None
            file_node = Node(vsm_hash = vsm_hash, filename = filename, encrypted_vsm_hash_1 = encrypted_vsm_hash_1, encrypted_vsm_hash_2 = encrypted_vsm_hash_2)       
            current_processing_list.append(file_node)

        stages_of_processing = find_two_exponent(len(current_processing_list))
    
        # First stage handled separately as internal nodes store vsm indices as list from vsm_hash of file nodes
        new_processing_list = list()
        for i in range(0, len(current_processing_list), 2):
            new_vsm_hash = create_vsm_hash(current_processing_list[i].vsm_hash, current_processing_list[i + 1].vsm_hash)

            current_processing_list[i].vsm_hash = None
            current_processing_list[i + 1].vsm_hash = None

            new_internal_node = Node(vsm_hash = new_vsm_hash, left = current_processing_list[i], right = current_processing_list[i + 1])
            new_processing_list.append(new_internal_node)

        current_processing_list = new_processing_list

        # 2^(Stage)-1 stages of processing for a balanced binary tree
        # Generating internal nodes
        for stage in range(stages_of_processing - 1):
            new_processing_list = list()

            for i in range(0, len(current_processing_list), 2):
            #    new_vsm = [ceil(x or y) for x,y in zip(current_processing_list[i].vsm, current_processing_list[i + 1].vsm)]
            #    new_vsm_hash = create_vsm_hash(current_processing_list[i].vsm_hash, current_processing_list[i + 1].vsm_hash)
                new_vsm_hash = list(set().union(current_processing_list[i].vsm_hash, current_processing_list[i + 1].vsm_hash))
                new_internal_node = Node(vsm_hash = new_vsm_hash, left = current_processing_list[i], right = current_processing_list[i + 1])
                new_processing_list.append(new_internal_node)
            
            current_processing_list = new_processing_list

        root_node = current_processing_list[0]

        save_object(index_directory + "/semi_encrypted_bbt.pkl", root_node)

    except KeyboardInterrupt:
        pass

def start_index_generation(prepared_documents_path, index_directory, key_directory):
    global corpus_textblobs
    global m1t
    global m2t
    global m1i
    global m2i

    print("Generating textblobs...")
    load_documents(prepared_documents_path)
    print("Preparing index...")
    generate_token_map_and_secret(index_directory, key_directory)

    # Create random invertible matrices and store Mt and Mi
    m1 = generate_random_invertible_matrix(n, 3, 100)
    m2 = generate_random_invertible_matrix(n, 3, 100)

    # Get transpose of matrices
    m1t = get_transpose(m1)
    m2t = get_transpose(m2)

    # Get matrix inverses
    m1i = get_inverse(m1)
    m2i = get_inverse(m2)

    # Save matrices
    save_object(index_directory + "/m1t.pkl", m1t)
    save_object(index_directory + "/m2t.pkl", m2t)
    save_object(index_directory + "/m1i.pkl", m1i)
    save_object(index_directory + "/m2i.pkl", m2i)

    build_bbt(corpus_textblobs, index_directory)
