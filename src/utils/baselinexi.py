"""*
 *     Reccurency Baselines 
 *
 *        File: baselinexi.py
 *
 *     Authors: Deleted for purposes of anonymity 
 *
 *     Proprietor: Deleted for purposes of anonymity --- PROPRIETARY INFORMATION
 * 
 * The software and its source code contain valuable trade secrets and shall be maintained in
 * confidence and treated as confidential information. The software may only be used for 
 * evaluation and/or testing purposes, unless otherwise explicitly stated in the terms of a
 * license agreement or nondisclosure agreement with the proprietor of the software. 
 * Any unauthorized publication, transfer to third parties, or duplication of the object or
 * source code---either totally or in part---is strictly prohibited.
 *
 *     Copyright (c) 2021 Proprietor: Deleted for purposes of anonymity
 *     All Rights Reserved.
 *
 * THE PROPRIETOR DISCLAIMS ALL WARRANTIES, EITHER EXPRESS OR 
 * IMPLIED, INCLUDING BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY 
 * AND FITNESS FOR A PARTICULAR PURPOSE AND THE WARRANTY AGAINST LATENT 
 * DEFECTS, WITH RESPECT TO THE PROGRAM AND ANY ACCOMPANYING DOCUMENTATION. 
 * 
 * NO LIABILITY FOR CONSEQUENTIAL DAMAGES:
 * IN NO EVENT SHALL THE PROPRIETOR OR ANY OF ITS SUBSIDIARIES BE 
 * LIABLE FOR ANY DAMAGES WHATSOEVER (INCLUDING, WITHOUT LIMITATION, DAMAGES
 * FOR LOSS OF BUSINESS PROFITS, BUSINESS INTERRUPTION, LOSS OF INFORMATION, OR
 * OTHER PECUNIARY LOSS AND INDIRECT, CONSEQUENTIAL, INCIDENTAL,
 * ECONOMIC OR PUNITIVE DAMAGES) ARISING OUT OF THE USE OF OR INABILITY
 * TO USE THIS PROGRAM, EVEN IF the proprietor HAS BEEN ADVISED OF
 * THE POSSIBILITY OF SUCH DAMAGES.
 * 
 * For purposes of anonymity, the identity of the proprietor is not given herewith. 
 * The identity of the proprietor will be given once the review of the 
 * conference submission is completed. 
 *
 * THIS HEADER MAY NOT BE EXTRACTED OR MODIFIED IN ANY WAY.
 *"""
from collections import Counter
from utils.utils import score_delta
import numpy as np

def update_distributions(learn_data_ts, ts_edges, obj_dist, 
                         rel_obj_dist, num_rels, cur_ts):
    """ update the distributions with more recent infos, if there is a more recent timestep available, depending on window parameter
    take into account scaling factor
    """
    obj_dist_cur_ts, rel_obj_dist_cur_ts= calculate_obj_distribution(learn_data_ts, ts_edges, num_rels) #, lmbda, cur_ts)
    return  rel_obj_dist_cur_ts, obj_dist_cur_ts

def calculate_obj_distribution(learn_data, edges, num_rels):
    """
    Calculate the overall object distribution and the object distribution for each relation in the data.

    Parameters:
        learn_data (np.ndarray): data on which the rules should be learned
        edges (dict): edges from the data on which the rules should be learned

    Returns:
        obj_dist (dict): overall object distribution
        rel_obj_dist (dict): object distribution for each relation
    """
    obj_dist_scaled = {}

    rel_obj_dist = dict()
    rel_obj_dist_scaled = dict()
    for rel in range(num_rels):
        rel_obj_dist[rel] = {}
        rel_obj_dist_scaled[rel] = {}
    
    for rel in edges:
        objects = edges[rel][:, 2]
        dist = Counter(objects)
        for obj in dist:
            dist[obj] /= len(objects)
        rel_obj_dist_scaled[rel] = {k: v for k, v in dist.items()}

    return obj_dist_scaled, rel_obj_dist_scaled



def calculate_obj_distribution_timeaware(learn_data, edges, num_rels, lmbda, cur_ts):
    """
    Calculate the overall object distribution and the object distribution for each relation in the data.
    take into account the delta function. 
    BUT: this is currently to slow without performance benefits

    Parameters:
        learn_data (np.ndarray): data on which the rules should be learned
        edges (dict): edges from the data on which the rules should be learned

    Returns:
        obj_dist (dict): overall object distribution
        rel_obj_dist (dict): object distribution for each relation
    """


    objects = learn_data[:, 2]
    timesteps_o = learn_data[:,3]
    ts_series = np.ones(len(timesteps_o ))*cur_ts
    denom =  np.sum(score_delta(timesteps_o, ts_series, lmbda))
    obj_dist_scaled = {}

    rel_obj_dist = dict()
    rel_obj_dist_scaled = dict()
    for rel in range(num_rels):
        rel_obj_dist[rel] = {}
        rel_obj_dist_scaled[rel] = {}
    
    for rel in edges:
        objects = edges[rel][:, 2]
        rel_edges = edges[rel]
        rel_edges_ts = rel_edges[:,3]
        ts_series = np.ones(len(rel_edges_ts ))*cur_ts 
        denom =  np.sum(score_delta(rel_edges_ts, ts_series, lmbda))
        dist = Counter(objects)
        for obj in objects: #dist:
            ts_rel_ob = rel_edges[rel_edges[:,2]==obj][:,3]
            ts_series_rel_ob = np.ones(len(ts_rel_ob ))*cur_ts
            nom = np.sum(score_delta(ts_rel_ob, ts_series_rel_ob, lmbda))
            rel_obj_dist_scaled[rel][obj] = nom/denom  
    return obj_dist_scaled, rel_obj_dist_scaled
