class Node(object):

    def __init__(self, vsm_hash = None, filename = None, left = None, right = None, encrypted_vsm_hash_1 = None, encrypted_vsm_hash_2 = None):
        self.filename = filename
        self.left = left
        self.right = right
        # vsm_hash is:
        #     list: for internal nodes
        #     dict: for file nodes
        self.vsm_hash = vsm_hash
        self.encrypted_vsm_hash_1 = encrypted_vsm_hash_1
        self.encrypted_vsm_hash_2 = encrypted_vsm_hash_2

    def get_file_nodes(self):
        if self:
            if self.left is None or self.right is None:
                print(self.filename)
            if self.left:
                self.left.get_file_nodes()
            if self.right:
                self.right.get_file_nodes()
