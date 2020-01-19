from Initialization import *
import random
import time
import os


class Evaluation:
    def __init__(self, graph_dict, prod_list, wallet_dict):
        ### graph_dict: (dict) the graph
        ### prod_list: (list) the set to record products [kk's profit, kk's cost, kk's price]
        ### num_product: (int) the kinds of products
        self.graph_dict = graph_dict
        self.product_list = prod_list
        self.num_product = len(prod_list)
        self.wallet_dict = wallet_dict
        self.eva_monte_carlo = 100

    def getSeedSetProfit(self, s_set):
        pnn_k_list = [0.0 for _ in range(self.num_product)]
        seed_diffusion_dict = {(k, s): 0 for k in range(self.num_product) for s in s_set[k]}

        for _ in range(self.eva_monte_carlo):
            s_total_set = set(s for k in range(self.num_product) for s in s_set[k])
            seed_diffusion_dict = {(k, s): 0 for k in range(self.num_product) for s in s_set[k]}
            wallet_dict = self.wallet_dict.copy()

            reverse_graph_dict = [{i: {} for i in self.graph_dict} for _ in range(self.num_product)]
            for k in range(self.num_product):
                for i in self.graph_dict:
                    for j in self.graph_dict[i]:
                        if random.random() <= self.graph_dict[i][j]:
                            reverse_graph_dict[k][i][j] = self.graph_dict[i][j]
                    if not reverse_graph_dict[k][i]:
                        del reverse_graph_dict[k][i]

            a_n_set = [s_total_set.copy() for _ in range(self.num_product)]
            a_n_sequence = [(k, i, (k, s)) for k in range(self.num_product) for s in s_set[k] if s in reverse_graph_dict[k]
                            for i in reverse_graph_dict[k][s] if i not in s_total_set and wallet_dict[i] >= self.product_list[k][2]]
            a_n_sequence2 = []

            while a_n_sequence:
                for k_prod, i_node, seed_diffusion_flag in a_n_sequence:
                    # -- purchasing --
                    a_n_set[k_prod].add(i_node)
                    wallet_dict[i_node] -= self.product_list[k_prod][2]
                    seed_diffusion_dict[seed_diffusion_flag] += 1

                    # -- passing the information --
                    if i_node in reverse_graph_dict[k_prod]:
                        for ii_node in reverse_graph_dict[k_prod][i_node]:
                            if wallet_dict[ii_node] >= self.product_list[k_prod][2]:
                                a_n_sequence2.append((k_prod, ii_node, seed_diffusion_flag))

                a_n_sequence, a_n_sequence2 = a_n_sequence2, []

            pnn_k_list = [pnn_k_list[k] + len(a_n_set[k]) - len(s_total_set) for k in range(self.num_product)]

        pnn_k_list = [safe_div(pnn, self.eva_monte_carlo) for pnn in pnn_k_list]
        seed_diffusion_dict = {seed_diffusion_flag: safe_div(seed_diffusion_dict[seed_diffusion_flag], self.eva_monte_carlo) for seed_diffusion_flag in seed_diffusion_dict}

        return pnn_k_list, seed_diffusion_dict


class EvaluationM:
    def __init__(self, model_name, dataset_name, product_name, cascade_model):
        self.model_name = model_name
        self.dataset_name = dataset_name
        self.new_dataset_name = 'email' * (dataset_name == 'email') + 'dnc' * (dataset_name == 'dnc_email') + \
                                'Eu' * (dataset_name == 'email_Eu_core') + 'Net' * (dataset_name == 'NetHEPT')
        self.product_name = product_name
        self.new_product_name = 'lphc' * (product_name == 'item_lphc') + 'hplc' * (product_name == 'item_hplc')
        self.cascade_model = cascade_model

    def evaluate(self, bi, wallet_distribution_type, sample_seed_set, ss_time):
        eva_start_time = time.time()
        ini = Initialization(self.dataset_name, self.product_name, wallet_distribution_type)

        seed_cost_dict = ini.constructSeedCostDict()
        graph_dict = ini.constructGraphDict(self.cascade_model)
        product_list = ini.constructProductList()[0]
        num_product = len(product_list)
        wallet_dict = ini.constructWalletDict()
        total_cost = sum(seed_cost_dict[i] for i in seed_cost_dict)
        total_budget = round(total_cost / 2 ** bi, 4)

        eva = Evaluation(graph_dict, product_list, wallet_dict)
        print('@ evaluation @ ' + self.new_dataset_name + '_' + self.cascade_model +
              '\t' + self.model_name +
              '\t' + wallet_distribution_type + '_' + self.new_product_name + '_bi' + str(bi))

        sample_pnn_k, seed_diffusion_dict_k = eva.getSeedSetProfit(sample_seed_set)
        sample_pro_k = [round(sample_pnn_k[k] * product_list[k][0], 4) for k in range(num_product)]
        sample_sn_k = [len(sample_sn_k) for sample_sn_k in sample_seed_set]
        sample_bud_k = [round(sum(seed_cost_dict[i] for i in sample_seed_set[k]), 4) for k in range(num_product)]
        sample_bud = round(sum(sample_bud_k), 4)
        sample_pro = round(sum(sample_pro_k), 4)
        seed_diffusion_list = [(seed_diffusion_flag, seed_diffusion_dict_k[seed_diffusion_flag]) for seed_diffusion_flag in seed_diffusion_dict_k]
        seed_diffusion_list = [(round(sd_item[1] * product_list[sd_item[0][0]][0], 4), sd_item[0], sd_item[1]) for sd_item in seed_diffusion_list]
        seed_diffusion_list = sorted(seed_diffusion_list, reverse=True)

        result = [sample_pro, sample_bud, sample_sn_k, sample_pnn_k, sample_pro_k, sample_bud_k, sample_seed_set]
        print('eva_time = ' + str(round(time.time() - eva_start_time, 2)) + 'sec')
        print(result)
        print('------------------------------------------')

        path0 = 'result/' + self.new_dataset_name + '_' + self.cascade_model
        if not os.path.isdir(path0):
            os.mkdir(path0)
        path = path0 + '/' + wallet_distribution_type + '_' + self.new_product_name + '_bi' + str(bi)
        if not os.path.isdir(path):
            os.mkdir(path)
        result_name = path + '/' + self.model_name + '.txt'

        fw = open(result_name, 'w')
        fw.write(self.new_dataset_name + '_' + self.cascade_model + '\t' +
                 self.model_name + '\t' +
                 wallet_distribution_type + '_' + self.new_product_name + '_bi' + str(bi) + '\n' +
                 'budget_limit = ' + str(total_budget) + '\n' +
                 'time = ' + str(ss_time) + '\n\n' +
                 'profit = ' + str(sample_pro) + '\n' +
                 'budget = ' + str(sample_bud) + '\n')
        fw.write('\nprofit_ratio = ')
        for kk in range(num_product):
            fw.write(str(sample_pro_k[kk]) + '\t')
        fw.write('\nbudget_ratio = ')
        for kk in range(num_product):
            fw.write(str(sample_bud_k[kk]) + '\t')
        fw.write('\nseed_number = ')
        for kk in range(num_product):
            fw.write(str(sample_sn_k[kk]) + '\t')
        fw.write('\ncustomer_number = ')
        for kk in range(num_product):
            fw.write(str(sample_pnn_k[kk]) + '\t')
        fw.write('\n\n')

        fw.write(str(sample_seed_set))
        for sd_item in seed_diffusion_list:
            fw.write('\n' + str(sd_item[1]) + '\t' + str(sd_item[0]) + '\t' + str(sd_item[2]))
        fw.close()