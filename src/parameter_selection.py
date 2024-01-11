'''
Parameter Selection; optional
For given dataset, for each relation, find the values of parameters lambda and alpha that give the best validation mrr 
Log the values and some additional information to ./configs/datasetnameconfigs.json; 
Grid-search over a fixed, predefined set of lambdas and alphas.
These parameter values can be used during testing.
'''

## imports
import json
import time
import argparse
import numpy as np
from joblib import Parallel, delayed
import pathlib
import os
from copy import copy

import utils.utils as utils
from data import data_handler
from utils.apply_baselines import apply_baselines
from utils.baselinepsi import score_psi

start_o = time.time()

## args
parser = argparse.ArgumentParser()
parser.add_argument("--dataset", "-d", default="YAGO", type=str)
parser.add_argument("--rules", "-r", default="1_r.json", type=str)
parser.add_argument("--window", "-w", default=0, type=int)
parser.add_argument("--num_processes", "-p", default=13, type=int)
parser.add_argument("--includebaselinexi", "-b",  default='y', type=str) 
parser.add_argument("--includebaselinepsi", "-psi",  default='y', type=str) 
parser.add_argument("--learnlmbdapsi", "-ld",  default='y', type=str) 
parser.add_argument("--learnalpha", "-alpha",  default='y', type=str) 


parsed = vars(parser.parse_args())

dataset_name = parsed["dataset"]
rules_file = parsed["rules"]
window = parsed["window"]
num_processes = parsed["num_processes"]
includexi = parsed["includebaselinexi"]
includepsi = parsed["includebaselinepsi"]
learn_lmbdapsi = parsed['learnlmbdapsi']
learn_alpha = parsed['learnalpha']
if learn_alpha == 'y':    
    learn_alpha = True
else:
    learn_alpha = False
if learn_lmbdapsi == 'y':
    learn_lmbdapsi = True
else:
    learn_lmbdapsi = False

method_name = ''
baselinepsi_flag = False
baselinexi_flag = False
if includepsi == 'y':
    method_name += 'baselinepsi'
    baselinepsi_flag = True
if includexi == 'y':
    method_name += 'baselinexi'
    baselinexi_flag = True
print("method: ", method_name)

## parameters to choose from
params_dict = {}
params_dict['lmbda_psi'] = [0, 0.0001, 0.0005, 0.001, 0.005, 0.01, 0.02, 0.04, 0.06, 0.08, 0.1, 0.5, 0.9, 1.0001] 
params_dict['alpha'] = [0, 0.00001, 0.0001, 0.001, 0.01, 0.1, 0.5, 0.9, 0.99, 0.999, 0.9999, 0.99999, 1]
append_alpha = False

## load dataset 
dataset = (dataset_name, 3) # identifier, timestamp_column_idx
train_data, valid_data, test_data, stat = data_handler.load(dataset[0])
num_nodes, num_rels = int(stat[0]), int(stat[1])
train_data = data_handler.add_inverse_quadruples(train_data, num_rels)
valid_data = data_handler.add_inverse_quadruples(valid_data, num_rels)
train_valid_data = np.concatenate((train_data, valid_data))

rels = np.arange(0,2*num_rels)

# group per relation. dict with key: relation id, values: quadruples
train_data_prel = data_handler.group_by(train_data, 1, rels)
valid_data_prel = data_handler.group_by(valid_data, 1, rels)
trainvalid_data_prel = data_handler.group_by(train_valid_data, 1, rels)

## load rules
dir_path =  os.path.join(pathlib.Path().resolve(), 'rules', dataset_name, rules_file)  #"./rules/" + dataset_name + "/"
basis_dict = json.load(open(dir_path)) # + rules_file))
basis_dict = {int(k): v for k, v in basis_dict.items()}

score_func_psi = score_psi
default_lmbdapsi = params_dict['lmbda_psi'][-1] 
default_alpha = params_dict['alpha'][-2] 

best_alpha = 0
if learn_alpha == False or learn_lmbdapsi == False:
    dir_path =  os.path.join(pathlib.Path().resolve(), 'configs', dataset_name+'configs.json')  
    if window < 0:
        dir_path =  os.path.join(pathlib.Path().resolve(), 'configs', dataset_name+'configs_multistep.json')  
    best_config = json.load(open(dir_path)) # + rules_file))
else:
    best_config = {}


for rel in rels: # loop through relations. for each relation, apply rules with selected params, compute valid mrr
    start = time.time()
    rel_key = int(copy(rel))
    if learn_lmbdapsi and learn_alpha:
        best_config[str(rel_key)] = {}
    best_config[str(rel_key)]['not_trained'] = 'True'    
    if learn_lmbdapsi:
        best_config[str(rel_key)]['lmbda_psi'] = copy([default_lmbdapsi,0] ) #default
        best_config[str(rel_key)]['other_lmbda_mrrs'] = list(np.zeros(len(params_dict['lmbda_psi'])))
    if learn_alpha:
        if append_alpha == False:
            best_config[str(rel_key)]['alpha'] = copy([default_alpha,0] ) #default    
            best_config[str(rel_key)]['other_alpha_mrrs'] = list(np.zeros(len(params_dict['alpha'])))
    
    if rel in valid_data_prel.keys():      
        # valid data for this relation  
        valid_data_c_rel = copy(valid_data_prel[rel])
        timesteps_valid = list(set(valid_data_c_rel[:,3]))
        timesteps_valid.sort()
        trainvalid_data_c_rel = trainvalid_data_prel[rel]
        
        # queries per process if multiple processes
        num_queries = len(valid_data_c_rel) // num_processes
        if num_queries < num_processes: # if we do not have enough queries for all the processes
            num_processes_tmp = copy(1)
            num_queries = copy(len(valid_data_c_rel))
        else:
            num_processes_tmp = copy(num_processes)

        ######  1) tune lmbda_psi ###############        
        baselinepsi_flag = True
        baselinexi_flag = False
        lmbdas_psi = params_dict['lmbda_psi']        

        alpha = 1
        method_name = 'baselinepsi'
        best_lmbda_psi = 0
        best_mrr_psi = 0
        lmbda_mrrs = []

        best_config[str(rel_key)]['num_app_valid'] = copy(len(valid_data_c_rel))
        best_config[str(rel_key)]['num_app_train_valid'] = copy(len(trainvalid_data_c_rel))            

        if learn_lmbdapsi:
            best_config[str(rel_key)]['not_trained'] = 'False'       

            print(rel)
            for lmbda_psi in lmbdas_psi:             
                output = Parallel(n_jobs=num_processes_tmp)(
                    delayed(apply_baselines)(i, copy(num_queries), copy(valid_data_c_rel), copy(trainvalid_data_c_rel), window, 
                                        copy(basis_dict), score_func_psi, 
                                        num_nodes, 2*num_rels, 
                                        baselinexi_flag, baselinepsi_flag,
                                        lmbda_psi, alpha) for i in range(num_processes_tmp))
                scores_dict_for_eval = {}
                for proc_loop in range(num_processes_tmp):
                    scores_dict_for_eval.update(output[proc_loop][1])

                # compute mrr
                mrr_and_friends = utils.compute_mrr(scores_dict_for_eval, valid_data_c_rel, timesteps_valid)
                mrr = mrr_and_friends[1]

                # is new mrr better than previous best? if yes: store lmbda
                if mrr > best_mrr_psi:
                    best_mrr_psi = mrr
                    best_lmbda_psi = lmbda_psi
                print('lmbda_psi: ', lmbda_psi)
                lmbda_mrrs.append(mrr)
            best_config[str(rel_key)]['lmbda_psi'] = copy([best_lmbda_psi, best_mrr_psi])
            best_config[str(rel_key)]['other_lmbda_mrrs'] = copy(lmbda_mrrs)

        ##### 2) tune alphas: ###############
        if learn_alpha == True or append_alpha ==True:
            if append_alpha:
                best_mrr_alpha = best_config[str(rel_key)]['alpha'][1]
                best_alpha = best_config[str(rel_key)]['alpha'][0]
            else:
                best_alpha = 0
                best_mrr_alpha = 0
            best_config[str(rel_key)]['not_trained'] = 'False'    
            alphas = params_dict['alpha'] 
            lmbda_psi = best_config[str(rel_key)]['lmbda_psi'][0] # use the best lmbda psi
            baselinepsi_flag = True
            baselinexi_flag = True
            method_name = 'baselinepsibaselinexi'

            alpha_mrrs = []
            for alpha in alphas:
                ## apply baselines for this relation and this 
                output_alpha = Parallel(n_jobs=num_processes_tmp)(
                    delayed(apply_baselines)(i, num_queries, valid_data_c_rel, trainvalid_data_c_rel, window, 
                                        basis_dict, score_func_psi, 
                                        num_nodes, 2*num_rels, 
                                        baselinexi_flag, baselinepsi_flag,
                                        lmbda_psi, alpha) for i in range(num_processes_tmp))
                scores_dict_for_eval_alpha = {}
                for proc_loop in range(num_processes_tmp):
                    scores_dict_for_eval_alpha.update(output_alpha[proc_loop][1])

                # compute mrr
                mrr_and_friends = utils.compute_mrr(scores_dict_for_eval_alpha, valid_data_c_rel, timesteps_valid)
                mrr_alpha = mrr_and_friends[1]

                # is new mrr better than previous best? if yes: store alpha
                if mrr_alpha > best_mrr_alpha:
                    best_mrr_alpha = mrr_alpha
                    best_alpha = alpha
                print('alpha: ', alpha)
                alpha_mrrs.append(mrr_alpha)

            best_config[str(rel_key)]['alpha'] = copy([best_alpha, best_mrr_alpha])
            if append_alpha:
                best_config[str(rel_key)]['other_alpha_mrrs'].append(copy(alpha_mrrs))
            else:
                best_config[str(rel_key)]['other_alpha_mrrs'] = copy(alpha_mrrs)

    end = time.time()
    total_time = round(end - start, 6)  
    print("Relation {} finished in {} seconds.".format(rel, total_time))

if append_alpha:
    with open('./configs/'+dataset_name+'appened_configs.json', 'w') as fp:
        json.dump(best_config, fp)
else:
    if window < 0:

        filename = dataset_name+ str(0.0)+'configs_multistep.json'
        with open('./configs/'+filename, 'w') as fp:
            json.dump(best_config, fp)       
    else:
        filename = dataset_name+ str(0.0)+'configs.json'
        with open('./configs/'+filename, 'w') as fp:
            json.dump(best_config, fp)

end_o = time.time()
total_time_o = round(end_o- start_o, 6)  
print("Finding the best configs finished in {} seconds.".format(total_time_o))
with open('learning_time.txt', 'a') as f:
    f.write(dataset_name+str(window)+str(learn_lmbdapsi)+str(learn_alpha)+':\t')
    f.write(str(total_time_o))
    f.write('\n')






