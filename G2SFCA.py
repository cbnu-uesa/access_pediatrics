
import numpy as np

# gaussian distribution
def gauss_w (dij, beta):
      #' Gaussian distance decay function
      #' W = e^(-d^2/a)
      weight = np.exp(-dij**2 / beta)
      return weight

# generalized 2sfca
def Generalized2SFCA(data, demand_id, demand_col, supply_id, supply_col, cost_col, catchment, impedance_beta):
    
    print("Procedure started for", demand_id)
    print("\n")

    tmp = data.copy()
    tmp[cost_col] = tmp[cost_col] # cost_id는 분(min)으로 측정되어야 함
    tmp = tmp.loc[tmp[cost_col] <= catchment]

    tmp['weight'] = gauss_w(tmp[[cost_col]], beta = impedance_beta)
    tmp['w_demand'] = tmp[demand_col] * tmp['weight']
    w_demand = tmp.groupby(supply_id, as_index = False)\
        .agg(sum_w_demand = ('w_demand', 'sum'))
    
    rj = tmp[[supply_id, supply_col]].drop_duplicates()
    rj = rj.merge(w_demand, how = 'left', on = supply_id)
    rj['rj'] = rj[supply_col] / rj['sum_w_demand']
    rj['rj'][np.isinf(rj['rj'])] = 0
    rj = rj[[supply_id, 'rj']]   

    tmp = tmp.merge(rj, how = 'left', on = supply_id)
    tmp['w_rj'] = tmp['rj'] * tmp['weight']
    ai_result = tmp.groupby(demand_id, as_index = False)\
        .agg(accessibility = ('w_rj', 'sum'))
    ai_result[demand_id] = ai_result[demand_id].astype(str)
    ai_result['accessibility'] = ai_result['accessibility']*1000

    avg_access = ai_result['accessibility'].mean()
    ai_result['spar'] = ai_result['accessibility']/avg_access -1

    print('Procedure finished for', demand_id, '\n')

    
    return ai_result    

########### 실행코드
import pandas as pd
network_data = pd.read_csv('data/network_data.csv')
demand_data = pd.read_csv('data/demand_df.csv')
supply_data = pd.read_csv('data/supply_df.csv')

network_data = pd.merge(network_data, demand_data, on='demand_id', how='left')
network_data = pd.merge(network_data, supply_data, on='supply_id', how='left')

demand_id = 'demand_id'
demand_col = 'demand_col'
supply_id = 'supply_id'
supply_col = 'supply_col'
cost_col = 'cost_col'
catchment = 30
impedance_beta = 200

result = Generalized2SFCA(network_data, demand_id, demand_col, supply_id, supply_col, cost_col, catchment, impedance_beta)

result.to_csv('data/accessibility.csv', index=False, encoding = 'utf-8')
