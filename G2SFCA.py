
import numpy as np

# gaussian distribution
def gauss_w (dij, beta):
      #' Gaussian distance decay function
      #' W = e^(-d^2/a)
      weight = np.exp(-dij**2 / beta)
      return weight


# generalized 2sfca
def Generalized2SFCA(data, demand_id, demand_col, supply_id, supply_col, cost_id, catchment, impedance_beta):
    
    print("Procedure started for", demand_id)
    print("\n")

    tmp = data.copy()
    tmp[cost_id] = tmp[cost_id]/60
    tmp = tmp.loc[tmp[cost_id] <= catchment]

    tmp['weight'] = gauss_w(tmp[[cost_id]], beta = impedance_beta)
    tmp['w_demand'] = tmp[demand_col] * tmp['weight']
    w_demand = tmp.groupby(supply_id, as_index = False)\
        .agg(sum_w_demand = ('w_demand', 'sum'))
    tmp = tmp.merge(w_demand, how = 'left', on = supply_id)

    if supply_col == 1:
        tmp['rj'] = 1 / tmp['sum_w_demand']
        tmp['rj'][np.isinf(tmp['rj'])] = 0   
    else: 
        tmp['rj'] = tmp[supply_col] / tmp['sum_w_demand']
        tmp['rj'][np.isinf(tmp['rj'])] = 0
    
    tmp['w_rj'] = tmp['rj'] * tmp['weight']
    ai_result = tmp.groupby(demand_id, as_index = False)\
        .agg(accessibility = ('w_rj', 'sum'))
    ai_result[demand_id] = ai_result[demand_id].astype(str)
    ai_result['accessibility'] = ai_result['accessibility']*1000
    
    print('Procedure finished for', demand_id, '\n')

    
    return ai_result    


