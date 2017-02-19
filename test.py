from pps.index_generator import start_index_generation
from pps.helpers.operations import load_object

# Test 1
start_index_generation("document_corpus/prepared_documents", "index")

# Test 2
root = load_object("index/encrypted_bbt.pkl")
file_leaves = list()
file_leaves = root.get_file_nodes(file_leaves)

for f in file_leaves:
    print(f)
