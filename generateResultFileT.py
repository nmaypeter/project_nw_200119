import xlwings as xw

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
        profit_list, time_list = [], []
        for bi in range(10, 6, -1):
            for prod_setting in prod_seq:
                new_product_name = 'lphc' * (prod_setting == 1) + 'hplc' * (prod_setting == 2)
                for wd in wd_seq:
                    wallet_distribution_type = 'm50e25' * (wd == 1) + 'm99e96' * (wd == 2) + 'm66e34' * (wd == 3)

                    profit, time = [], []
                    r = new_dataset_name + '\t' + cascade_model + '\t' + \
                        wallet_distribution_type + '\t' + new_product_name + '\t' + str(bi)
                    print(r)
                    for model_name in model_seq:
                        try:
                            result_name = 'resultT/' + \
                                          new_dataset_name + '_' + cascade_model + '/' + \
                                          wallet_distribution_type + '_' + new_product_name + '_bi' + str(bi) + '/' + \
                                          model_name + '.txt'

                            with open(result_name) as f:
                                p = 0.0
                                for lnum, line in enumerate(f):
                                    if lnum < 2 or lnum == 3:
                                        continue
                                    elif lnum == 2:
                                        (l) = line.split()
                                        t = l[-1]
                                        time.append(t)
                                    elif lnum == 4:
                                        (l) = line.split()
                                        p = float(l[-1])
                                    elif lnum == 5:
                                        (l) = line.split()
                                        c = float(l[-1])
                                        profit.append(str(round(p - c, 4)))
                                    else:
                                        break
                        except FileNotFoundError:
                            profit.append('')
                            time.append('')
                    profit_list.append(profit)
                    time_list.append(time)
            profit_list.append(['' for _ in range(len(model_seq))])
            time_list.append(['' for _ in range(len(model_seq))])

        result_path = 'resultT/profit.xlsx'
        wb = xw.Book(result_path)
        sheet_name = new_dataset_name + '_' + cascade_model
        sheet = wb.sheets[sheet_name]
        sheet.cells(7, "C").value = profit_list

        result_path = 'resultT/time.xlsx'
        wb = xw.Book(result_path)
        sheet_name = new_dataset_name + '_' + cascade_model
        sheet = wb.sheets[sheet_name]
        sheet.cells(7, "C").value = time_list