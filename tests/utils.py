# MIT License
# 
# Copyright (c) 2022, Alex M. Maldonado
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Utilities for tests."""

import numpy as np
import scipy as sp

def _pdist(r, lat_and_inv=None):
    """
    Compute pairwise Euclidean distance matrix between all atoms.

    Parameters
    ----------
    r : :obj:`numpy.ndarray`
        Array of size 3N containing the Cartesian coordinates of
        each atom.
    lat_and_inv : :obj:`tuple` of :obj:`numpy.ndarray`, optional
        Tuple of 3x3 matrix containing lattice vectors as columns and its inverse.

    Returns
    -------
    :obj:`numpy.ndarray`
        Array of size N x N containing all pairwise distances between atoms.
    """

    r = r.reshape(-1, 3)
    n_atoms = r.shape[0]

    if lat_and_inv is None:
        pdist = sp.spatial.distance.pdist(r, 'euclidean')
    else:
        pdist = sp.spatial.distance.pdist(
            r, lambda u, v: np.linalg.norm(_pbc_diff(u - v, lat_and_inv))
        )

    tril_idxs = np.tril_indices(n_atoms, k=-1)
    return sp.spatial.distance.squareform(pdist, checks=False)[tril_idxs]