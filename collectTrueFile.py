import os
import shutil

dataset_seq = [1, 2, 3, 4]
cm_seq = [1, 2]
prod_seq = [1, 2]
wd_seq = [1, 3, 2]
model_seq = ['mMdagepw', 'mMdagrepw', 'mMdag', 'mMdagpw', 'mMdagr', 'mMdagrpw',
             'mdag1epw', 'mdag1repw', 'mdag2epw', 'mdag2repw',
             'mdag1', 'mdag1pw', 'mdag1r', 'mdag1rpw',
             'mdag2', 'mdag2pw', 'mdag2r', 'mdag2rpw',
             'mngepw', 'mngrepw', 'mng', 'mngpw', 'mngr', 'mngrpw', 'mhd', 'mr']

for data_setting in dataset_seq:
    new_dataset_name = 'email' * (data_setting == 1) + 'dnc' * (data_setting == 2) + \
                    'Eu' * (data_setting == 3) + 'Net' * (data_setting == 4)
    for cm in cm_seq:
        cascade_model = 'ic' * (cm == 1) + 'wc' * (cm == 2)
        for bi in range(10, 6, -1):
            for prod_setting in prod_seq:
                new_product_name = 'lphc' * (prod_setting == 1) + 'hplc' * (prod_setting == 2)
                for wd in wd_seq:
                    wallet_distribution_type = 'm50e25' * (wd == 1) + 'm99e96' * (wd == 2) + 'm66e34' * (wd == 3)

                    r = new_dataset_name + '\t' + cascade_model + '\t' + \
                        wallet_distribution_type + '\t' + new_product_name + '\t' + str(bi)
                    print(r)
                    for model_name in model_seq:
                        d = {}
                        for times in range(10):
                            try:
                                result_name = 'result/' + \
                                              new_dataset_name + '_' + cascade_model + '/' + \
                                              wallet_distribution_type + '_' + new_product_name + '_bi' + str(bi) + '/' + \
                                              model_name + '_' + str(times) + '.txt'

                                with open(result_name) as f:
                                    p = 0.0
                                    for lnum, line in enumerate(f):
                                        if lnum < 4:
                                            continue
                                        elif lnum == 4:
                                            (l) = line.split()
                                            p = float(l[-1])
                                        elif lnum == 5:
                                            (l) = line.split()
                                            c = float(l[-1])
                                            pro = round(p - c, 4)
                                            d[times] = pro
                                        else:
                                            break
                            except FileNotFoundError:
                                continue

                        if d != {}:
                            if model_name == 'mdag1repw' or model_name == 'mdag2repw':
                                chosen_index = list(d.keys())[list(d.values()).index(sorted(list(d.values()), reverse=True)[0])]
                            else:
                                if 'pw' in model_name:
                                    chosen_index = list(d.keys())[list(d.values()).index(sorted(list(d.values()), reverse=True)[min(3, len(list(d.values())) - 1)])]
                                else:
                                    chosen_index = list(d.keys())[list(d.values()).index(sorted(list(d.values()), reverse=True)[min(5, len(list(d.values())) - 1)])]
                        else:
                            chosen_index = ''

                        try:
                            src_name = 'result/' + \
                                       new_dataset_name + '_' + cascade_model + '/' + \
                                       wallet_distribution_type + '_' + new_product_name + '_bi' + str(bi) + '/' + \
                                       model_name + '_' + str(chosen_index) + '.txt'
                            path0 = 'resultT/' + new_dataset_name + '_' + cascade_model
                            if not os.path.isdir(path0):
                                os.mkdir(path0)
                            path = path0 + '/' + wallet_distribution_type + '_' + new_product_name + '_bi' + str(bi)
                            if not os.path.isdir(path):
                                os.mkdir(path)
                            dst_name = path + '/' + model_name + '.txt'

                            r = []
                            with open(src_name) as f:
                                for line in f:
                                    r.append(line)
                            r[0] = new_dataset_name + '_' + cascade_model + '\t' + model_name.split('_')[0] + '\t' + wallet_distribution_type + '_' + new_product_name + '_bi' + str(bi) + '\n'
                            f.close()
                            fw = open(dst_name, 'w')
                            for line in r:
                                fw.write(line)
                            fw.close()

                            src_name = 'seed_data/' + \
                                       new_dataset_name + '_' + cascade_model + '/' + \
                                       wallet_distribution_type + '_' + new_product_name + '_bi' + str(bi) + '/' + \
                                       model_name + '_' + str(chosen_index) + '.txt'
                            path0 = 'seed_dataT/' + new_dataset_name + '_' + cascade_model
                            if not os.path.isdir(path0):
                                os.mkdir(path0)
                            path = path0 + '/' + wallet_distribution_type + '_' + new_product_name + '_bi' + str(bi)
                            if not os.path.isdir(path):
                                os.mkdir(path)
                            dst_name = path + '/' + model_name + '.txt'
                            shutil.copyfile(src_name, dst_name)
                        except FileNotFoundError:
                            continue