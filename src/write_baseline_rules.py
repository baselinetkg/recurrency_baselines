"""*
 *     Reccurency Baselines 
 *
 *        File: write_baseline_rules.py
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
"""
log the "rules", i.e. principles of strict recurrency, that are used for baseline psi. 
log the file to ./rules/datasetname/1_r.json
for each dataset: find the relation ids in train and valid set. for each of these relations create a rule,
where the head rel =  body rel, and the confidence is artificially set to 1.
this is used as input to baseline psi
"""

import json
import numpy as np
import os
from data import data_handler


names = ['ICEWS14', 'ICEWS18', 'YAGO', 'WIKI', 'GDELT'] #add new datasets here.
for dataset_name in names:
    dataset = (dataset_name, 3) # identifier, timestamp_column_idx

    train_data, valid_data, _, stat = data_handler.load(dataset[0]) #only needed to extract relation ids
    num_rels = int(stat[1])
    train_data = data_handler.add_inverse_quadruples(train_data, num_rels)
    valid_data = data_handler.add_inverse_quadruples(valid_data, num_rels)

    train_valid_data = np.concatenate((train_data, valid_data))
    rels = list(set(train_valid_data[:,1]))
    new_rules = {}

    for rel in rels:
        rules_id_new = []
        rule_dict = {}
        rule_dict["head_rel"] = int(rel)
        rule_dict["body_rels"] = [int(rel)] #same body and head relation -> what happened before happens again
        rule_dict["conf"] = 1 #same confidence for every rule
        rule_new = rule_dict
        rules_id_new.append(rule_new)
        new_rules[str(rel)] = rules_id_new

    if not os.path.exists('./rules/'+dataset_name):
        os.makedirs('./rules/'+dataset_name)
    with open('./rules/'+dataset_name+'/1_r.json', 'w') as fp: #store rules in directory
        json.dump(new_rules, fp)

