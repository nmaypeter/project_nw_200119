from Model import *

if __name__ == '__main__':
    dataset_seq = [1, 2, 3, 4]
    cm_seq = [1, 2]
    prod_seq = [1, 2]
    wd_seq = [1, 2, 3]

    for data_setting in dataset_seq:
        dataset_name = 'email' * (data_setting == 1) + 'dnc_email' * (data_setting == 2) + \
                       'email_Eu_core' * (data_setting == 3) + 'NetHEPT' * (data_setting == 4)
        for cm in cm_seq:
            cascade_model = 'ic' * (cm == 1) + 'wc' * (cm == 2)
            for prod_setting in prod_seq:
                product_name = 'item_lphc' * (prod_setting == 1) + 'item_hplc' * (prod_setting == 2)
                for times in range(10):

                    Model('mMdag1_' + str(times), dataset_name, product_name, cascade_model).model_dag(1, r_flag=False, M_flag=True)
                    Model('mMdag1r_' + str(times), dataset_name, product_name, cascade_model).model_dag(1, r_flag=True, M_flag=True)
                    Model('mdag1_' + str(times), dataset_name, product_name, cascade_model).model_dag(1, r_flag=False)
                    Model('mdag1r_' + str(times), dataset_name, product_name, cascade_model).model_dag(1, r_flag=True)
                    Model('mdag2_' + str(times), dataset_name, product_name, cascade_model).model_dag(2, r_flag=False)
                    Model('mdag2r_' + str(times), dataset_name, product_name, cascade_model).model_dag(2, r_flag=True)
                    Model('mng_' + str(times), dataset_name, product_name, cascade_model).model_ng(r_flag=False)
                    Model('mngr_' + str(times), dataset_name, product_name, cascade_model).model_ng(r_flag=True)
                    Model('mhd_' + str(times), dataset_name, product_name, cascade_model).model_hd()
                    Model('mr_' + str(times), dataset_name, product_name, cascade_model).model_r()

                    for wd in wd_seq:
                        wallet_distribution_type = 'm50e25' * (wd == 1) + 'm99e96' * (wd == 2) + 'm66e34' * (wd == 3)

                        Model('mMdag1epw_' + str(times), dataset_name, product_name, cascade_model, wallet_distribution_type).model_dag(1, r_flag=False, epw_flag=True, M_flag=True)
                        Model('mMdag1repw_' + str(times), dataset_name, product_name, cascade_model, wallet_distribution_type).model_dag(1, r_flag=True, epw_flag=True, M_flag=True)
                        Model('mMdag1pw_' + str(times), dataset_name, product_name, cascade_model, wallet_distribution_type).model_dag(1, r_flag=False, M_flag=True)
                        Model('mMdag1rpw_' + str(times), dataset_name, product_name, cascade_model, wallet_distribution_type).model_dag(1, r_flag=True, M_flag=True)
                        Model('mdag1epw_' + str(times), dataset_name, product_name, cascade_model, wallet_distribution_type).model_dag(1, r_flag=False, epw_flag=True)
                        Model('mdag1repw_' + str(times), dataset_name, product_name, cascade_model, wallet_distribution_type).model_dag(1, r_flag=True, epw_flag=True)
                        Model('mdag2epw_' + str(times), dataset_name, product_name, cascade_model, wallet_distribution_type).model_dag(2, r_flag=False, epw_flag=True)
                        Model('mdag2repw_' + str(times), dataset_name, product_name, cascade_model, wallet_distribution_type).model_dag(2, r_flag=True, epw_flag=True)
                        Model('mdag1pw_' + str(times), dataset_name, product_name, cascade_model, wallet_distribution_type).model_dag(1, r_flag=False)
                        Model('mdag1rpw_' + str(times), dataset_name, product_name, cascade_model, wallet_distribution_type).model_dag(1, r_flag=True)
                        Model('mdag2pw_' + str(times), dataset_name, product_name, cascade_model, wallet_distribution_type).model_dag(2, r_flag=False)
                        Model('mdag2rpw_' + str(times), dataset_name, product_name, cascade_model, wallet_distribution_type).model_dag(2, r_flag=True)
                        Model('mngepw_' + str(times), dataset_name, product_name, cascade_model, wallet_distribution_type).model_ng(r_flag=False, epw_flag=True)
                        Model('mngrepw_' + str(times), dataset_name, product_name, cascade_model, wallet_distribution_type).model_ng(r_flag=True, epw_flag=True)
                        Model('mngpw_' + str(times), dataset_name, product_name, cascade_model, wallet_distribution_type).model_ng(r_flag=False)
                        Model('mngrpw_' + str(times), dataset_name, product_name, cascade_model, wallet_distribution_type).model_ng(r_flag=True)