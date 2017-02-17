from pps.index_generator import start_index_generation
from pps.helpers.operations import load_object

# Test 1
start_index_generation("document_corpus/prepared_documents", "index", "keys")

# Test 2
root = load_object("index/semi_encrypted_bbt.pkl")
root.get_file_nodes()
