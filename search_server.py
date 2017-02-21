import threading
import socket
from time import time
from random import randint
from operator import itemgetter
from math import sqrt

from hashlib import sha256

from pps.crypto import aes_decrypt
from pps.network_interface import send_object, receive_object
from pps.communication_objects import Server_Response
from pps.helpers.operations import load_object, matrix_multiplication, vsm_hash_to_vsm
from pps.helpers.text_processor import stem_text

class SearchServer(object):

    def __init__(self, port = 5000, is_cached = False):
        self.port = port
        self.cached = is_cached

        # Load key, salt and secret
        self.aes_key = load_object("index/aes_key.pkl")
        self.salt = load_object("index/salt.pkl")
        self.secret = load_object("index/secret.pkl")

        # Load matrices
        self.m1i = load_object("index/m1i.pkl")
        self.m2i = load_object("index/m2i.pkl")

        # Load encrypted token map & encrypted search index(balanced binary tree)
        self.encrypted_token_map = load_object("index/encrypted_token_map.pkl")
        self.encrypted_bbt = load_object("index/encrypted_bbt.pkl")

        # Initialize server socket to handle incoming connections
        self.serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSock.bind(("0.0.0.0", self.port))
        self.serverSock.listen(128)

    def start(self):
        # Start listening for incoming requests
        while 1:
            connection, address = self.serverSock.accept()
            threading.Thread(target=self.requestHandler, args=(connection, address)).start()

    def requestHandler(self, server_socket, address):
        # Receive query & search parameters from the client
        client_query_object = receive_object(server_socket)

        # Info
        print("Received request for: " + client_query_object.query_string + "\n")

        # Start timer
        start_time = time()

        query = client_query_object.query_string
        top_k = client_query_object.top_k

        # Prepare the hashed query
        stemmed_query = stem_text(query)
        query_terms = list(set(stemmed_query.split()))
        hashed_query_terms = [sha256(self.salt.encode() + query.encode()).hexdigest() for query in query_terms]

        # Prepare hashed index for query indices
        hashed_indices = list()

        for query in hashed_query_terms:
            if query in self.encrypted_token_map:
                hashed_indices.append(sha256(self.salt.encode() + str(self.encrypted_token_map[query][0]).encode()).hexdigest())

        ranked_result = list()

        if hashed_indices:
            # Search in encrypted bbt & get a list of matching file nodes
            file_nodes = list()
            file_nodes = self.encrypted_bbt.search(hashed_indices, file_nodes)

            # Create query map: index:idf
            query_map = {self.encrypted_token_map[query][0] : self.encrypted_token_map[query][1] for query in hashed_query_terms}

            # Create normalized idf for query map
            normalization = sqrt(sum([ pow(idf, 2) for idf in query_map.values()]))
            query_map = { encrypted_index : idf/normalization for encrypted_index, idf in query_map.items() }

            # Generate q1 and q2
            q1 = query_map
            q2 = query_map

            for index in query_map.keys():
                if self.secret[index] == 0:
                    # Split randomly as long as the sum is same
                    q1[index] = query_map[index]/(randint(2,6))
                    q2[index] = query_map[index] - q1[index]

            # Encrypt query vectors
            n = len(self.encrypted_token_map)

            m1iq1 = matrix_multiplication(self.m1i, vsm_hash_to_vsm(n, q1))
            m2iq2 = matrix_multiplication(self.m2i, vsm_hash_to_vsm(n, q2))

            # results_map: {similarity score: filename}
            results_map = { (aes_decrypt(node.filename, self.aes_key)).decode("utf-8") : (matrix_multiplication(node.encrypted_vsm_hash_1, m1iq1) + matrix_multiplication(node.encrypted_vsm_hash_2, m2iq2)) for node in file_nodes }
            print(results_map)

            # Sort by similarity score
            ranked_result = sorted(results_map.items(), key = itemgetter(1), reverse = True)
            ranked_result = [result[0] for result in ranked_result]

        # Note end time
        end_time = time()

        # Get top-k results
        if top_k == 0:
            if len(ranked_result) > 170:
                ranked_result = ranked_result[:170]
        else:
            ranked_result = ranked_result[:top_k]

        # Create response to client
        response = Server_Response(float("{0:.4f}".format(end_time - start_time)), ranked_result)

        # Send response back to the client
        send_object(server_socket, response)

        # Close socket
        server_socket.close()

if __name__ == "__main__":
    # Start the server
    try:
        encrypted_search_server = SearchServer()
        encrypted_search_server.start()
    except KeyboardInterrupt:
        print("Server shutting down...\n")
