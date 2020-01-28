from SeedSelection import *
from Evaluation import *
import time
import copy
import math


class Model:
    def __init__(self, model_name, dataset_name, product_name, cascade_model, wallet_distribution_type=''):
        self.model_name = model_name
        self.dataset_name = dataset_name
        self.new_dataset_name = 'email' * (dataset_name == 'email') + 'dnc' * (dataset_name == 'dnc_email') + \
                                'Eu' * (dataset_name == 'email_Eu_core') + 'Net' * (dataset_name == 'NetHEPT')
        self.product_name = product_name
        self.new_product_name = 'lphc' * (product_name == 'item_lphc') + 'hplc' * (product_name == 'item_hplc')
        self.cascade_model = cascade_model
        self.wallet_distribution_type = wallet_distribution_type
        self.wd_seq = ['m50e25', 'm99e96', 'm66e34']
        self.budget_iteration = [i for i in range(10, 6, -1)]
        self.monte_carlo = 100

    def model_dag(self, dag_class, r_flag, epw_flag=False, M_flag=False):
        ini = Initialization(self.dataset_name, self.product_name, self.wallet_distribution_type)
        seed_cost_dict = ini.constructSeedCostDict()
        graph_dict = ini.constructGraphDict(self.cascade_model)
        product_list, product_weight_list = ini.constructProductList()
        num_product = len(product_list)
        total_cost = sum(seed_cost_dict[i] for i in seed_cost_dict)

        seed_set_sequence = [-1 for _ in range(len(self.budget_iteration))]
        ss_time_sequence = [-1 for _ in range(len(self.budget_iteration))]
        seed_data_sequence = [-1 for _ in range(len(self.budget_iteration))]
        ssmioa_model = SeedSelectionMIOA(graph_dict, seed_cost_dict, product_list, product_weight_list, dag_class, r_flag, epw_flag, M_flag)

        ss_start_time = time.time()
        bud_iteration = self.budget_iteration.copy()
        now_b_iter = bud_iteration.pop(0)
        now_budget, now_profit = 0.0, 0.0
        seed_set = [set() for _ in range(num_product)]

        wd_seq = [self.wallet_distribution_type] if self.wallet_distribution_type else self.wd_seq
        mioa_dict = ssmioa_model.generateMIOA()
        celf_heap = ssmioa_model.generateCelfHeap(mioa_dict)

        ss_acc_time = round(time.time() - ss_start_time, 4)
        temp_sequence = [[ss_acc_time, now_budget, now_profit, seed_set, celf_heap]]
        temp_seed_data = [['time\tk_prod\ti_node\tnow_budget\tnow_profit\tseed_num\n']]
        while temp_sequence:
            ss_start_time = time.time()
            now_bi_index = self.budget_iteration.index(now_b_iter)
            total_budget = safe_div(total_cost, 2 ** now_b_iter)
            [ss_acc_time, now_budget, now_profit, seed_set, celf_heap] = temp_sequence.pop()
            seed_data = temp_seed_data.pop()
            print('@ selection\t' + self.model_name + ' @ ' + self.new_dataset_name + '_' + self.cascade_model +
                  '\t' + self.wallet_distribution_type + '_' + self.new_product_name + '_bi' + str(now_b_iter) + ', budget = ' + str(total_budget))

            celf_heap_c = []
            while now_budget < total_budget and celf_heap:
                if round(now_budget + seed_cost_dict[celf_heap[0][2]], 4) >= total_budget and bud_iteration and not temp_sequence:
                    celf_heap_c = copy.deepcopy(celf_heap)
                mep_item = heap.heappop_max(celf_heap)
                mep_mg, mep_k_prod, mep_i_node, mep_flag = mep_item
                sc = seed_cost_dict[mep_i_node]
                seed_set_length = sum(len(seed_set[k]) for k in range(num_product))

                if round(now_budget + sc, 4) >= total_budget and bud_iteration and not temp_sequence:
                    ss_time = round(time.time() - ss_start_time + ss_acc_time, 4)
                    now_b_iter = bud_iteration.pop(0)
                    temp_sequence.append([ss_time, now_budget, now_profit, copy.deepcopy(seed_set), celf_heap_c])
                    temp_seed_data.append(seed_data.copy())

                if round(now_budget + sc, 4) > total_budget:
                    continue

                if mep_flag == seed_set_length:
                    seed_set[mep_k_prod].add(mep_i_node)
                    now_budget = round(now_budget + sc, 4)
                    now_profit = round(now_profit + (mep_mg * (sc if r_flag else 1.0)), 4)
                    seed_data.append(str(round(time.time() - ss_start_time + ss_acc_time, 4)) + '\t' + str(mep_k_prod) + '\t' + str(mep_i_node) + '\t' +
                                     str(now_budget) + '\t' + str(now_profit) + '\t' + str([len(seed_set[k]) for k in range(num_product)]) + '\n')
                else:
                    seed_set_t = copy.deepcopy(seed_set)
                    seed_set_t[mep_k_prod].add(mep_i_node)
                    dag_dict = [{} for _ in range(num_product)]
                    if dag_class == 1:
                        dag_dict = ssmioa_model.generateDAG1(mioa_dict, seed_set_t)
                    elif dag_class == 2:
                        dag_dict = ssmioa_model.generateDAG2(mioa_dict, seed_set_t)
                    ep_t = ssmioa_model.calculateExpectedProfit(dag_dict, seed_set_t)
                    mg_t = safe_div(round(ep_t - now_profit, 4), sc if r_flag else 1.0)
                    flag_t = seed_set_length

                    if mg_t > 0:
                        celf_item_t = (mg_t, mep_k_prod, mep_i_node, flag_t)
                        heap.heappush_max(celf_heap, celf_item_t)

            ss_time = round(time.time() - ss_start_time + ss_acc_time, 4)
            print('ss_time = ' + str(ss_time) + 'sec, cost = ' + str(now_budget) + ', seed_set_length = ' + str([len(s_set_k) for s_set_k in seed_set]))
            seed_set_sequence[now_bi_index] = seed_set
            ss_time_sequence[now_bi_index] = ss_time
            seed_data_sequence[now_bi_index] = seed_data

            for wd in wd_seq:
                seed_data_path = 'seed_data/' + self.new_dataset_name + '_' + self.cascade_model
                if not os.path.isdir(seed_data_path):
                    os.mkdir(seed_data_path)
                seed_data_path0 = seed_data_path + '/' + wd + '_' + self.new_product_name + '_bi' + str(self.budget_iteration[now_bi_index])
                if not os.path.isdir(seed_data_path0):
                    os.mkdir(seed_data_path0)
                seed_data_file = open(seed_data_path0 + '/' + self.model_name + '.txt', 'w')
                for sd in seed_data:
                    seed_data_file.write(sd)
                seed_data_file.close()

        while -1 in seed_data_sequence:
            no_data_index = seed_data_sequence.index(-1)
            seed_set_sequence[no_data_index] = seed_set_sequence[no_data_index - 1]
            ss_time_sequence[no_data_index] = ss_time_sequence[no_data_index - 1]
            seed_data_sequence[no_data_index] = seed_data_sequence[no_data_index - 1]

        eva_model = EvaluationM(self.model_name, self.dataset_name, self.product_name, self.cascade_model)
        for bi in self.budget_iteration:
            now_bi_index = self.budget_iteration.index(bi)
            if self.wallet_distribution_type:
                eva_model.evaluate(bi, self.wallet_distribution_type, seed_set_sequence[now_bi_index], ss_time_sequence[now_bi_index])
            else:
                for wallet_distribution_type in self.wd_seq:
                    eva_model.evaluate(bi, wallet_distribution_type, seed_set_sequence[now_bi_index], ss_time_sequence[now_bi_index])

    def model_ng(self, r_flag, epw_flag=False):
        ini = Initialization(self.dataset_name, self.product_name, self.wallet_distribution_type)
        seed_cost_dict = ini.constructSeedCostDict()
        graph_dict = ini.constructGraphDict(self.cascade_model)
        product_list, product_weight_list = ini.constructProductList()
        num_product = len(product_list)
        total_cost = sum(seed_cost_dict[i] for i in seed_cost_dict)

        seed_set_sequence = [-1 for _ in range(len(self.budget_iteration))]
        ss_time_sequence = [-1 for _ in range(len(self.budget_iteration))]
        seed_data_sequence = [-1 for _ in range(len(self.budget_iteration))]
        ssng_model = SeedSelectionNG(graph_dict, seed_cost_dict, product_list, product_weight_list, r_flag, epw_flag)

        ss_start_time = time.time()
        bud_iteration = self.budget_iteration.copy()
        now_b_iter = bud_iteration.pop(0)
        now_budget, now_profit = 0.0, 0.0
        seed_set = [set() for _ in range(num_product)]

        wd_seq = [self.wallet_distribution_type] if self.wallet_distribution_type else self.wd_seq
        celf_heap = ssng_model.generateCelfHeap()

        ss_acc_time = round(time.time() - ss_start_time, 4)
        temp_sequence = [[ss_acc_time, now_budget, now_profit, seed_set, celf_heap]]
        temp_seed_data = [['time\tk_prod\ti_node\tnow_budget\tnow_profit\tseed_num\n']]
        while temp_sequence:
            ss_start_time = time.time()
            now_bi_index = self.budget_iteration.index(now_b_iter)
            total_budget = safe_div(total_cost, 2 ** now_b_iter)
            [ss_acc_time, now_budget, now_profit, seed_set, celf_heap] = temp_sequence.pop()
            seed_data = temp_seed_data.pop()
            print('@ selection\t' + self.model_name + ' @ ' + self.new_dataset_name + '_' + self.cascade_model +
                  '\t' + self.wallet_distribution_type + '_' + self.new_product_name + '_bi' + str(now_b_iter) + ', budget = ' + str(total_budget))

            celf_heap_c = []
            while now_budget < total_budget and celf_heap:
                if round(now_budget + seed_cost_dict[celf_heap[0][2]], 4) >= total_budget and bud_iteration and not temp_sequence:
                    celf_heap_c = copy.deepcopy(celf_heap)
                mep_item = heap.heappop_max(celf_heap)
                mep_mg, mep_k_prod, mep_i_node, mep_flag = mep_item
                sc = seed_cost_dict[mep_i_node]
                seed_set_length = sum(len(seed_set[k]) for k in range(num_product))

                if round(now_budget + sc, 4) >= total_budget and bud_iteration and not temp_sequence:
                    ss_time = round(time.time() - ss_start_time + ss_acc_time, 4)
                    now_b_iter = bud_iteration.pop(0)
                    temp_sequence.append([ss_time, now_budget, now_profit, copy.deepcopy(seed_set), celf_heap_c])
                    temp_seed_data.append(seed_data.copy())

                if round(now_budget + sc, 4) > total_budget:
                    continue

                if mep_flag == seed_set_length:
                    seed_set[mep_k_prod].add(mep_i_node)
                    now_budget = round(now_budget + sc, 4)
                    now_profit = ssng_model.getSeedSetProfit(seed_set)
                    seed_data.append(str(round(time.time() - ss_start_time + ss_acc_time, 4)) + '\t' + str(mep_k_prod) + '\t' + str(mep_i_node) + '\t' +
                                     str(now_budget) + '\t' + str(now_profit) + '\t' + str([len(seed_set[k]) for k in range(num_product)]) + '\n')
                else:
                    seed_set_t = copy.deepcopy(seed_set)
                    seed_set_t[mep_k_prod].add(mep_i_node)
                    ep_t = ssng_model.getSeedSetProfit(seed_set_t)
                    mg_t = round(ep_t - now_profit, 4)
                    if r_flag:
                        mg_t = safe_div(mg_t, sc)
                    flag_t = seed_set_length

                    if mg_t > 0:
                        celf_item_t = (mg_t, mep_k_prod, mep_i_node, flag_t)
                        heap.heappush_max(celf_heap, celf_item_t)

            ss_time = round(time.time() - ss_start_time + ss_acc_time, 4)
            print('ss_time = ' + str(ss_time) + 'sec, cost = ' + str(now_budget) + ', seed_set_length = ' + str([len(s_set_k) for s_set_k in seed_set]))
            seed_set_sequence[now_bi_index] = seed_set
            ss_time_sequence[now_bi_index] = ss_time
            seed_data_sequence[now_bi_index] = seed_data

            for wd in wd_seq:
                seed_data_path = 'seed_data/' + self.new_dataset_name + '_' + self.cascade_model
                if not os.path.isdir(seed_data_path):
                    os.mkdir(seed_data_path)
                seed_data_path0 = seed_data_path + '/' + wd + '_' + self.new_product_name + '_bi' + str(self.budget_iteration[now_bi_index])
                if not os.path.isdir(seed_data_path0):
                    os.mkdir(seed_data_path0)
                seed_data_file = open(seed_data_path0 + '/' + self.model_name + '.txt', 'w')
                for sd in seed_data:
                    seed_data_file.write(sd)
                seed_data_file.close()

        while -1 in seed_data_sequence:
            no_data_index = seed_data_sequence.index(-1)
            seed_set_sequence[no_data_index] = seed_set_sequence[no_data_index - 1]
            ss_time_sequence[no_data_index] = ss_time_sequence[no_data_index - 1]
            seed_data_sequence[no_data_index] = seed_data_sequence[no_data_index - 1]

        eva_model = EvaluationM(self.model_name, self.dataset_name, self.product_name, self.cascade_model)
        for bi in self.budget_iteration:
            now_bi_index = self.budget_iteration.index(bi)
            if self.wallet_distribution_type:
                eva_model.evaluate(bi, self.wallet_distribution_type, seed_set_sequence[now_bi_index], ss_time_sequence[now_bi_index])
            else:
                for wallet_distribution_type in self.wd_seq:
                    eva_model.evaluate(bi, wallet_distribution_type, seed_set_sequence[now_bi_index], ss_time_sequence[now_bi_index])

    def model_hd(self):
        ini = Initialization(self.dataset_name, self.product_name, self.wallet_distribution_type)
        seed_cost_dict = ini.constructSeedCostDict()
        graph_dict = ini.constructGraphDict(self.cascade_model)
        product_list, product_weight_list = ini.constructProductList()
        num_product = len(product_list)
        total_cost = sum(seed_cost_dict[i] for i in seed_cost_dict)

        seed_set_sequence = [-1 for _ in range(len(self.budget_iteration))]
        ss_time_sequence = [-1 for _ in range(len(self.budget_iteration))]
        seed_data_sequence = [-1 for _ in range(len(self.budget_iteration))]
        sshd_model = SeedSelectionHD(graph_dict, product_list)

        ss_start_time = time.time()
        bud_iteration = self.budget_iteration.copy()
        now_b_iter = bud_iteration.pop(0)
        now_budget = 0.0
        seed_set = [set() for _ in range(num_product)]

        wd_seq = [self.wallet_distribution_type] if self.wallet_distribution_type else self.wd_seq
        degree_heap = sshd_model.generateDegreeHeap()

        ss_acc_time = round(time.time() - ss_start_time, 4)
        temp_sequence = [[ss_acc_time, now_budget, seed_set, degree_heap]]
        temp_seed_data = [['time\tk_prod\ti_node\tnow_budget\tnow_profit\tseed_num\n']]
        while temp_sequence:
            ss_start_time = time.time()
            now_bi_index = self.budget_iteration.index(now_b_iter)
            total_budget = safe_div(total_cost, 2 ** now_b_iter)
            [ss_acc_time, now_budget, seed_set, degree_heap] = temp_sequence.pop()
            seed_data = temp_seed_data.pop()
            print('@ selection\t' + self.model_name + '@ ' + self.new_dataset_name + '_' + self.cascade_model +
                  '\t' + self.wallet_distribution_type + '_' + self.new_product_name + '_bi' + str(now_b_iter) + ', budget = ' + str(total_budget))

            degree_heap_c = []
            while now_budget < total_budget and degree_heap:
                if round(now_budget + seed_cost_dict[degree_heap[0][2]], 4) >= total_budget and bud_iteration and not temp_sequence:
                    degree_heap_c = copy.deepcopy(degree_heap)
                mep_item = heap.heappop_max(degree_heap)
                mep_deg, mep_k_prod, mep_i_node = mep_item
                sc = seed_cost_dict[mep_i_node]

                if round(now_budget + sc, 4) >= total_budget and bud_iteration and not temp_sequence:
                    ss_time = round(time.time() - ss_start_time + ss_acc_time, 4)
                    now_b_iter = bud_iteration.pop(0)
                    temp_sequence.append([ss_time, now_budget, copy.deepcopy(seed_set), degree_heap_c])
                    temp_seed_data.append(seed_data.copy())

                if round(now_budget + sc, 4) > total_budget:
                    continue

                seed_set[mep_k_prod].add(mep_i_node)
                now_budget = round(now_budget + sc, 4)
                seed_data.append(str(round(time.time() - ss_start_time + ss_acc_time, 4)) + '\t' + str(mep_k_prod) + '\t' + str(mep_i_node) + '\t' +
                                 str(now_budget) + '\t' + str([len(seed_set[k]) for k in range(num_product)]) + '\n')

            ss_time = round(time.time() - ss_start_time + ss_acc_time, 4)
            print('ss_time = ' + str(ss_time) + 'sec, cost = ' + str(now_budget) + ', seed_set_length = ' + str([len(s_set_k) for s_set_k in seed_set]))
            seed_set_sequence[now_bi_index] = seed_set
            ss_time_sequence[now_bi_index] = ss_time
            seed_data_sequence[now_bi_index] = seed_data

            for wd in wd_seq:
                seed_data_path = 'seed_data/' + self.new_dataset_name + '_' + self.cascade_model
                if not os.path.isdir(seed_data_path):
                    os.mkdir(seed_data_path)
                seed_data_path0 = seed_data_path + '/' + wd + '_' + self.new_product_name + '_bi' + str(self.budget_iteration[now_bi_index])
                if not os.path.isdir(seed_data_path0):
                    os.mkdir(seed_data_path0)
                seed_data_file = open(seed_data_path0 + '/' + self.model_name + '.txt', 'w')
                for sd in seed_data:
                    seed_data_file.write(sd)
                seed_data_file.close()

        while -1 in seed_data_sequence:
            no_data_index = seed_data_sequence.index(-1)
            seed_set_sequence[no_data_index] = seed_set_sequence[no_data_index - 1]
            ss_time_sequence[no_data_index] = ss_time_sequence[no_data_index - 1]
            seed_data_sequence[no_data_index] = seed_data_sequence[no_data_index - 1]

        eva_model = EvaluationM(self.model_name, self.dataset_name, self.product_name, self.cascade_model)
        for bi in self.budget_iteration:
            now_bi_index = self.budget_iteration.index(bi)
            if self.wallet_distribution_type:
                eva_model.evaluate(bi, self.wallet_distribution_type, seed_set_sequence[now_bi_index], ss_time_sequence[now_bi_index])
            else:
                for wallet_distribution_type in self.wd_seq:
                    eva_model.evaluate(bi, wallet_distribution_type, seed_set_sequence[now_bi_index], ss_time_sequence[now_bi_index])

    def model_r(self):
        ini = Initialization(self.dataset_name, self.product_name, self.wallet_distribution_type)
        seed_cost_dict = ini.constructSeedCostDict()
        graph_dict = ini.constructGraphDict(self.cascade_model)
        product_list, product_weight_list = ini.constructProductList()
        num_product = len(product_list)
        total_cost = sum(seed_cost_dict[i] for i in seed_cost_dict)

        seed_set_sequence = [-1 for _ in range(len(self.budget_iteration))]
        ss_time_sequence = [-1 for _ in range(len(self.budget_iteration))]
        seed_data_sequence = [-1 for _ in range(len(self.budget_iteration))]

        ss_start_time = time.time()
        bud_iteration = self.budget_iteration.copy()
        now_b_iter = bud_iteration.pop(0)
        now_budget = 0.0
        seed_set = [set() for _ in range(num_product)]

        wd_seq = [self.wallet_distribution_type] if self.wallet_distribution_type else self.wd_seq
        random_node_list = [(k, i) for i in graph_dict for k in range(num_product)]
        random.shuffle(random_node_list)

        ss_acc_time = round(time.time() - ss_start_time, 4)
        temp_sequence = [[ss_acc_time, now_budget, seed_set, random_node_list]]
        temp_seed_data = [['time\tk_prod\ti_node\tnow_budget\tnow_profit\tseed_num\n']]
        while temp_sequence:
            ss_start_time = time.time()
            now_bi_index = self.budget_iteration.index(now_b_iter)
            total_budget = safe_div(total_cost, 2 ** now_b_iter)
            [ss_acc_time, now_budget, seed_set, random_node_list] = temp_sequence.pop()
            seed_data = temp_seed_data.pop()
            print('@ selection\t' + self.model_name + '@ ' + self.new_dataset_name + '_' + self.cascade_model +
                  '\t' + self.wallet_distribution_type + '_' + self.new_product_name + '_bi' + str(now_b_iter) + ', budget = ' + str(total_budget))

            random_node_list_c = []
            while now_budget < total_budget and random_node_list:
                if round(now_budget + seed_cost_dict[random_node_list[0][1]], 4) >= total_budget and bud_iteration and not temp_sequence:
                    random_node_list_c = copy.deepcopy(random_node_list)
                mep_item = random_node_list.pop(0)
                mep_k_prod, mep_i_node = mep_item
                sc = seed_cost_dict[mep_i_node]

                if round(now_budget + sc, 4) >= total_budget and bud_iteration and not temp_sequence:
                    ss_time = round(time.time() - ss_start_time + ss_acc_time, 4)
                    now_b_iter = bud_iteration.pop(0)
                    temp_sequence.append([ss_time, now_budget, copy.deepcopy(seed_set), random_node_list_c])
                    temp_seed_data.append(seed_data.copy())

                if round(now_budget + sc, 4) > total_budget:
                    continue

                seed_set[mep_k_prod].add(mep_i_node)
                now_budget = round(now_budget + sc, 4)
                seed_data.append(str(round(time.time() - ss_start_time + ss_acc_time, 4)) + '\t' + str(mep_k_prod) + '\t' + str(mep_i_node) + '\t' +
                                 str(now_budget) + '\t' + str([len(seed_set[k]) for k in range(num_product)]) + '\n')

            ss_time = round(time.time() - ss_start_time + ss_acc_time, 4)
            print('ss_time = ' + str(ss_time) + 'sec, cost = ' + str(now_budget) + ', seed_set_length = ' + str([len(s_set_k) for s_set_k in seed_set]))
            seed_set_sequence[now_bi_index] = seed_set
            ss_time_sequence[now_bi_index] = ss_time
            seed_data_sequence[now_bi_index] = seed_data

            for wd in wd_seq:
                seed_data_path = 'seed_data/' + self.new_dataset_name + '_' + self.cascade_model
                if not os.path.isdir(seed_data_path):
                    os.mkdir(seed_data_path)
                seed_data_path0 = seed_data_path + '/' + wd + '_' + self.new_product_name + '_bi' + str(self.budget_iteration[now_bi_index])
                if not os.path.isdir(seed_data_path0):
                    os.mkdir(seed_data_path0)
                seed_data_file = open(seed_data_path0 + '/' + self.model_name + '.txt', 'w')
                for sd in seed_data:
                    seed_data_file.write(sd)
                seed_data_file.close()

        while -1 in seed_data_sequence:
            no_data_index = seed_data_sequence.index(-1)
            seed_set_sequence[no_data_index] = seed_set_sequence[no_data_index - 1]
            ss_time_sequence[no_data_index] = ss_time_sequence[no_data_index - 1]
            seed_data_sequence[no_data_index] = seed_data_sequence[no_data_index - 1]

        eva_model = EvaluationM(self.model_name, self.dataset_name, self.product_name, self.cascade_model)
        for bi in self.budget_iteration:
            now_bi_index = self.budget_iteration.index(bi)
            if self.wallet_distribution_type:
                eva_model.evaluate(bi, self.wallet_distribution_type, seed_set_sequence[now_bi_index], ss_time_sequence[now_bi_index])
            else:
                for wallet_distribution_type in self.wd_seq:
                    eva_model.evaluate(bi, wallet_distribution_type, seed_set_sequence[now_bi_index], ss_time_sequence[now_bi_index])

    def model_pmis(self, epw_flag=False):
        ini = Initialization(self.dataset_name, self.product_name, self.wallet_distribution_type)
        seed_cost_dict = ini.constructSeedCostDict()
        graph_dict = ini.constructGraphDict(self.cascade_model)
        product_list, product_weight_list = ini.constructProductList()
        num_product = len(product_list)
        total_cost = sum(seed_cost_dict[i] for i in seed_cost_dict)

        seed_set_sequence = [-1 for _ in range(len(self.budget_iteration))]
        ss_time_sequence = [-1 for _ in range(len(self.budget_iteration))]
        seed_data_sequence = [-1 for _ in range(len(self.budget_iteration))]
        ssng_model = SeedSelectionNG(graph_dict, seed_cost_dict, product_list, product_weight_list, True, epw_flag)
        sspmis_model = SeedSelectionPMIS(graph_dict, seed_cost_dict, product_list, product_weight_list, epw_flag)

        ss_start_time = time.time()
        celf_heap_o = sspmis_model.generateCelfHeap()

        ss_acc_time = round(time.time() - ss_start_time, 4)
        for now_b_iter in self.budget_iteration:
            ss_start_time = time.time()
            now_bi_index = self.budget_iteration.index(now_b_iter)
            total_budget = safe_div(total_cost, 2 ** now_b_iter)
            celf_heap = copy.deepcopy(celf_heap_o)
            print('@ selection\t' + self.model_name + ' @ ' + self.new_dataset_name + '_' + self.cascade_model +
                  '\t' + self.wallet_distribution_type + '_' + self.new_product_name + '_bi' + str(now_b_iter) + ', budget = ' + str(total_budget))

            # -- initialization for each sample --
            now_budget, now_profit = 0.0, 0.0
            seed_set = [set() for _ in range(num_product)]
            s_matrix, c_matrix = [[set() for _ in range(num_product)]], [0.0]

            while now_budget < total_budget and celf_heap:
                mep_item = heap.heappop_max(celf_heap)
                mep_mg, mep_k_prod, mep_i_node, mep_flag = mep_item
                sc = seed_cost_dict[mep_i_node]
                seed_set_length = sum(len(seed_set[k]) for k in range(num_product))

                if round(now_budget + sc, 4) > total_budget:
                    continue

                if mep_flag == seed_set_length:
                    seed_set[mep_k_prod].add(mep_i_node)
                    now_budget = round(now_budget + sc, 4)
                    now_profit = ssng_model.getSeedSetProfit(seed_set)
                    s_matrix.append(copy.deepcopy(seed_set))
                    c_matrix.append(now_budget)
                else:
                    seed_set_t = copy.deepcopy(seed_set)
                    seed_set_t[mep_k_prod].add(mep_i_node)
                    ep_t = ssng_model.getSeedSetProfit(seed_set_t)
                    mg_t = round(ep_t - now_profit, 4)
                    flag_t = seed_set_length

                    if mg_t > 0:
                        celf_item_t = (mg_t, mep_k_prod, mep_i_node, flag_t)
                        heap.heappush_max(celf_heap, celf_item_t)

            seed_set = sspmis_model.solveMCPK(total_budget, [s_matrix] * num_product, [c_matrix] * num_product)
            now_budget = sum(seed_cost_dict[i] for k in range(num_product) for i in seed_set[k])

            ss_time = round(time.time() - ss_start_time + ss_acc_time, 4)
            print('ss_time = ' + str(ss_time) + 'sec, cost = ' + str(now_budget) + ', seed_set_length = ' + str([len(s_set_k) for s_set_k in seed_set]))
            seed_set_sequence[now_bi_index] = seed_set
            ss_time_sequence[now_bi_index] = ss_time
            seed_data_sequence[now_bi_index] = seed_set

        while -1 in seed_data_sequence:
            no_data_index = seed_data_sequence.index(-1)
            seed_set_sequence[no_data_index] = seed_set_sequence[no_data_index - 1]
            ss_time_sequence[no_data_index] = ss_time_sequence[no_data_index - 1]
            seed_data_sequence[no_data_index] = seed_data_sequence[no_data_index - 1]

        eva_model = EvaluationM(self.model_name, self.dataset_name, self.product_name, self.cascade_model)
        for bi in self.budget_iteration:
            now_bi_index = self.budget_iteration.index(bi)
            if self.wallet_distribution_type:
                eva_model.evaluate(bi, self.wallet_distribution_type, seed_set_sequence[now_bi_index], ss_time_sequence[now_bi_index])
            else:
                for wallet_distribution_type in self.wd_seq:
                    eva_model.evaluate(bi, wallet_distribution_type, seed_set_sequence[now_bi_index], ss_time_sequence[now_bi_index])

    def model_bcs(self, epw_flag=False):
        ini = Initialization(self.dataset_name, self.product_name, self.wallet_distribution_type)
        seed_cost_dict = ini.constructSeedCostDict()
        graph_dict = ini.constructGraphDict(self.cascade_model)
        product_list, product_weight_list = ini.constructProductList()
        num_product = len(product_list)
        total_cost = sum(seed_cost_dict[i] for i in seed_cost_dict)

        seed_set_sequence = [-1 for _ in range(len(self.budget_iteration))]
        ss_time_sequence = [-1 for _ in range(len(self.budget_iteration))]
        seed_data_sequence = [-1 for _ in range(len(self.budget_iteration))]
        ssbcs_model = SeedSelectionBCS(graph_dict, seed_cost_dict, product_list, product_weight_list, epw_flag)

        ss_start_time = time.time()
        celf_heap_list_o = ssbcs_model.generateCelfHeap()

        ss_acc_time = round(time.time() - ss_start_time, 4)
        for now_b_iter in self.budget_iteration:
            ss_start_time = time.time()
            now_bi_index = self.budget_iteration.index(now_b_iter)
            total_budget = safe_div(total_cost, 2 ** now_b_iter)
            celf_heap_list = copy.deepcopy(celf_heap_list_o)
            print('@ selection\t' + self.model_name + ' @ ' + self.new_dataset_name + '_' + self.cascade_model +
                  '\t' + self.wallet_distribution_type + '_' + self.new_product_name + '_bi' + str(now_b_iter) + ', budget = ' + str(total_budget))

            seed_set_list = []
            while celf_heap_list:
                celf_heap = celf_heap_list.pop()
                now_budget, now_profit = 0.0, 0.0
                seed_set = [set() for _ in range(num_product)]

                while now_budget < total_budget and celf_heap:
                    mep_item = heap.heappop_max(celf_heap)
                    mep_mg, mep_k_prod, mep_i_node, mep_flag = mep_item
                    sc = seed_cost_dict[mep_i_node]
                    seed_set_length = sum(len(seed_set[k]) for k in range(num_product))

                    if round(now_budget + sc, 4) > total_budget:
                        continue

                    if mep_flag == seed_set_length:
                        seed_set[mep_k_prod].add(mep_i_node)
                        now_budget = round(now_budget + sc, 4)
                        now_profit = round(now_profit + mep_mg * (sc if len(celf_heap_list) else 1.0), 4)
                    else:
                        seed_set_t = copy.deepcopy(seed_set)
                        seed_set_t[mep_k_prod].add(mep_i_node)
                        ep_t = ssbcs_model.getSeedSetProfit(seed_set_t)
                        mg_t = round(ep_t - now_profit, 4)
                        if len(celf_heap_list):
                            mg_t = safe_div(mg_t, sc)
                        flag_t = seed_set_length

                        if mg_t > 0:
                            celf_item_t = (mg_t, mep_k_prod, mep_i_node, flag_t)
                            heap.heappush_max(celf_heap, celf_item_t)

                seed_set_list.insert(0, seed_set)

            final_seed_set = copy.deepcopy(seed_set_list[0])
            final_bud = sum(seed_cost_dict[i] for k in range(num_product) for i in final_seed_set[k])
            final_ep = ssbcs_model.getSeedSetProfit(seed_set_list[0])
            for k in range(num_product):
                Handbill_counter = 0
                AnnealingScheduleT, detT = 1000000, 1000
                for s in seed_set_list[0][k]:
                    # -- first level: replace billboard seed by handbill seed --
                    final_seed_set_t = copy.deepcopy(final_seed_set)
                    final_seed_set_t[k].remove(s)
                    final_bud_t = final_bud - seed_cost_dict[s]
                    Handbill_seed_set = set((k, i) for k in range(num_product) for i in seed_set_list[1][k] if i not in final_seed_set_t[k])
                    if Handbill_seed_set:
                        min_Handbill_cost = min(seed_cost_dict[Handbill_item[1]] for Handbill_item in Handbill_seed_set)
                        while total_budget - final_bud_t >= min_Handbill_cost and Handbill_seed_set:
                            k_prod, i_node = Handbill_seed_set.pop()
                            if seed_cost_dict[i_node] <= total_budget - final_bud_t:
                                final_seed_set_t[k_prod].add(i_node)
                                final_bud_t += seed_cost_dict[i_node]
                                Handbill_counter += 1
                        final_ep_t = ssbcs_model.getSeedSetProfit(final_seed_set_t)
                        final_mg_t = final_ep_t - final_ep
                        # -- second level: replace handbill seed by handbill seed --
                        if final_mg_t >= 0 or math.exp(safe_div(final_mg_t, AnnealingScheduleT)) > random.random():
                            final_seed_set = final_seed_set_t
                            final_bud = final_bud_t
                            final_ep = final_ep_t
                            for q in range(min(Handbill_counter, 10)):
                                final_seed_set_t = copy.deepcopy(final_seed_set)
                                final_Handbill_seed_set = set((k, i) for k in range(num_product) for i in final_seed_set_t[k] if i in seed_set_list[1][k])
                                if final_Handbill_seed_set:
                                    k_prod, i_node = final_Handbill_seed_set.pop()
                                    final_seed_set_t[k_prod].remove(i_node)
                                    final_bud_t = final_bud - seed_cost_dict[i_node]
                                    Handbill_seed_set = set((k, i) for k in range(num_product) for i in seed_set_list[1][k] if i not in final_seed_set_t[k])
                                    min_Handbill_cost = min(seed_cost_dict[Handbill_item[1]] for Handbill_item in Handbill_seed_set)
                                    while total_budget - final_bud_t >= min_Handbill_cost and Handbill_seed_set:
                                        k_prod, i_node = Handbill_seed_set.pop()
                                        if seed_cost_dict[i_node] <= total_budget - final_bud_t:
                                            final_seed_set_t[k_prod].add(i_node)
                                            final_bud_t += seed_cost_dict[i_node]
                                    final_ep_t = ssbcs_model.getSeedSetProfit(final_seed_set_t)
                                    final_mg_t = final_ep_t - final_ep
                                    if final_mg_t >= 0 or math.exp(safe_div(final_mg_t, AnnealingScheduleT)) > random.random():
                                        final_seed_set = final_seed_set_t
                                        final_bud = final_bud_t
                                        final_ep = final_ep_t

                    AnnealingScheduleT -= detT
            seed_set = copy.deepcopy(final_seed_set)

            ss_time = round(time.time() - ss_start_time + ss_acc_time, 4)
            print('ss_time = ' + str(ss_time) + 'sec, cost = ' + str(final_bud) + ', seed_set_length = ' + str([len(s_set_k) for s_set_k in seed_set]))
            seed_set_sequence[now_bi_index] = seed_set
            ss_time_sequence[now_bi_index] = ss_time
            seed_data_sequence[now_bi_index] = final_seed_set

        while -1 in seed_data_sequence:
            no_data_index = seed_data_sequence.index(-1)
            seed_set_sequence[no_data_index] = seed_set_sequence[no_data_index - 1]
            ss_time_sequence[no_data_index] = ss_time_sequence[no_data_index - 1]
            seed_data_sequence[no_data_index] = seed_data_sequence[no_data_index - 1]

        eva_model = EvaluationM(self.model_name, self.dataset_name, self.product_name, self.cascade_model)
        for bi in self.budget_iteration:
            now_bi_index = self.budget_iteration.index(bi)
            if self.wallet_distribution_type:
                eva_model.evaluate(bi, self.wallet_distribution_type, seed_set_sequence[now_bi_index], ss_time_sequence[now_bi_index])
            else:
                for wallet_distribution_type in self.wd_seq:
                    eva_model.evaluate(bi, wallet_distribution_type, seed_set_sequence[now_bi_index], ss_time_sequence[now_bi_index])