class Node(object):

    def __init__(self, vsm_hash, filename = None, left = None, right = None):
        self.filename = filename
        self.left = left
        self.right = right
        self.vsm_hash = vsm_hash

    def associate(self, left_child, right_child):
        self.left = left_child
        self.right = right_child
