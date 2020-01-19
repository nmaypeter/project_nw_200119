import shutil

dataset_seq = [1, 2, 3, 4]
cm_seq = [1, 2]

for data_setting in dataset_seq:
    dataset_name = 'email' * (data_setting == 1) + 'dnc_email' * (data_setting == 2) + \
                   'email_Eu_core' * (data_setting == 3) + 'NetHEPT' * (data_setting == 4)
    new_dataset_name = 'email' * (data_setting == 1) + 'dnc' * (data_setting == 2) + \
                       'Eu' * (data_setting == 3) + 'Net' * (data_setting == 4)
    for bi in [i for i in range(10, 6, -1)]:
        for cm in cm_seq:
            cascade_model = 'ic' * (cm == 1) + 'wc' * (cm == 2)
            for dag_class in [1, 2]:
                if data_setting == 1 and cm == 1 and dag_class == 1 and bi == 8:
                    continue
                src = 'analysis/email_ic_1_bi8.xlsx'
                dst = 'analysis/' + new_dataset_name + '_' + cascade_model + '_' + str(dag_class) + '_bi' + str(bi) + '.xlsx'
                shutil.copyfile(src, dst)