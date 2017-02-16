import numpy as np

def generate_random_invertible_matrix(n, range_lower, range_upper):
    return np.triu(np.random.random_integers(range_lower, range_upper, (n, n)))

def get_inverse(matrix):
    return np.linalg.inv(matrix)

def get_transpose(matrix):
    return matrix.T

def matrix_multiplication(matrix_1, matrix_2):
    return np.dot(matrix_1, matrix_2)

def vsm_hash_to_vsm(n, vsm_hash, query_indices):
    vsm = [0] * n

    for index in query_indices:
        try:
            vsm[index] = vsm_hash[index]
        except KeyError:
            pass
