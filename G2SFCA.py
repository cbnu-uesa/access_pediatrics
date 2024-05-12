
import numpy as np
import datetime

# gaussian distribution
def gauss_w (dij, beta):
      #' Gaussian distance decay function
      #' W = e^(-d^2/a)
      weight = np.exp(-dij**2 / beta)
      return weight

# generalized 2sfca
def Generalized_2SFCA(demand_data, supply_data, cost_data, threshold):
    
    start_time = datetime.datetime.now()

    print("Procedure started")
    print("\n")

    # 컬럼 정리
    demand_data.columns = ['demand_id', 'demand_val']
    supply_data.columns = ['supply_id', 'supply_val']
    cost_data.columns = ['demand_id', 'supply_id', 'cost_val']

    # 분석용 데이터 생성
    data = cost_data.merge(demand_data, how = 'left', on = 'demand_id')\
          .merge(supply_data, how = 'left', on = 'supply_id')
    
    # threshold에 따른 impedence beta 산정
    impedance_beta = -(threshold**2)/np.log(0.001)
    
    # threshold를 기반으로 불필요한 OD pairs 삭제
    data = data.loc[data['cost_val'] <= threshold]

    # cost를 distance decay function을 활용하여 weight로 변경
    data['fij'] = gauss_w(data['cost_val'], beta = impedance_beta) 

    # 1단계: 공급지별 수요(w_demand)를 고려한 Rj 산정
    data['w_demand'] = data['demand_val'] * data['fij']
    w_demand = data.groupby(supply_id, as_index = False)\
        .agg(sum_w_demand = ('w_demand', 'sum'))
    
    rj = supply_data.merge(w_demand, how = 'left', on = supply_id)
    rj['rj'] = rj['supply_val'] / rj['sum_w_demand']
    rj.loc[np.isinf(rj['rj']), ['rj']] = 0
    rj = rj[[supply_id, 'rj']]   

    # 2단계: 수요지별로 Rj 합산
    data = data.merge(rj, how = 'left', on = supply_id)
    data['w_rj'] = data['rj'] * data['weight']
    access = data.groupby(demand_id, as_index = False)\
        .agg(accessibility = ('w_rj', 'sum'))
    
    avg_access = access['accessibility'].mean()
    access['spar'] = access['accessibility']/avg_access - 1

    result = demand_data.merge(access, how = 'left', on = 'demand_id')
    result = result[['demand_id', 'accessibility', 'spar']]

    end_time = datetime.datetime.now()
    duration = end_time - start_time

    print(f'Procedure has finished. It takes {duration} seconds')
    
    return result    

# inverted 2sfca
def inverted_2SFCA(demand_data, supply_data, cost_data, threshold):
    
    start_time = datetime.datetime.now()

    print("Procedure started")
    print("\n")

    # 컬럼 정리
    demand_data.columns = ['demand_id', 'demand_val']
    supply_data.columns = ['supply_id', 'supply_val']
    cost_data.columns = ['demand_id', 'supply_id', 'cost_val']

    # 분석용 데이터 생성
    data = cost_data.merge(demand_data, how = 'left', on = 'demand_id')\
          .merge(supply_data, how = 'left', on = 'supply_id')
    
    # threshold에 따른 impedence beta 산정
    impedance_beta = -(threshold**2)/np.log(0.001)
    
    # threshold를 기반으로 불필요한 OD pairs 삭제
    data = data.loc[data['cost_val'] <= threshold]

    # cost를 distance decay function을 활용하여 weight로 변경
    data['fij'] = gauss_w(data['cost_val'], beta = impedance_beta) 

    # 1단계: 수요지별 공급(w_supply)를 고려한 Rj 산정
    data['w_demand'] = data['demand_val'] * data['fij']
    w_demand = data.groupby(supply_id, as_index = False)\
        .agg(sum_w_demand = ('w_demand', 'sum'))
    
    rj = supply_data.merge(w_demand, how = 'left', on = supply_id)
    rj['rj'] = rj['supply_val'] / rj['sum_w_demand']
    rj.loc[np.isinf(rj['rj']), ['rj']] = 0
    rj = rj[[supply_id, 'rj']]   

    # 2단계: 수요지별로 Rj 합산
    data = data.merge(rj, how = 'left', on = supply_id)
    data['w_rj'] = data['rj'] * data['weight']
    access = data.groupby(demand_id, as_index = False)\
        .agg(accessibility = ('w_rj', 'sum'))
    
    avg_access = access['accessibility'].mean()
    access['spar'] = access['accessibility']/avg_access - 1

    result = demand_data.merge(access, how = 'left', on = 'demand_id')
    result = result[['demand_id', 'accessibility', 'spar']]

    end_time = datetime.datetime.now()
    duration = end_time - start_time

    print(f'Procedure has finished. It takes {duration} seconds')
    
    return result    

# Adjusted Balanced FCA
def ABFCA(demand_data, supply_data, cost_data, threshold):
    
    start_time = datetime.datetime.now()

    print("Procedure started")
    print("\n")

    # 컬럼 정리
    demand_data.columns = ['demand_id', 'demand_val']
    supply_data.columns = ['supply_id', 'supply_val']
    cost_data.columns = ['demand_id', 'supply_id', 'cost_val']

    # 분석용 데이터 생성
    data = cost_data.merge(demand_data, how = 'left', on = 'demand_id')\
          .merge(supply_data, how = 'left', on = 'supply_id')
    
    # threshold에 따른 impedence beta 산정
    impedance_beta = -(threshold**2)/np.log(0.001)
    
    # threshold를 기반으로 불필요한 OD pairs 삭제
    data = data.loc[data['cost_val'] <= threshold]

    # cost를 distance decay function을 활용하여 weight로 변경
    data['fij'] = gauss_w(data['cost_val'], beta = impedance_beta) 

    # 0단계: 공급지 매력도를 고려한 수요 배분 확률(Huff 확률) qij 산정
    data['w_supply'] = data['supply_col'] * data['fij']
    w_supply = data.groupby(supply_id, as_index = False)\
        .agg(sum_w_supply = ('w_supply', 'sum'))
    data = data.merge(w_supply, how = 'left', on = 'supply_id')
    data['qij'] = data['w_supply'] / data['sum_w_supply']

    # 1단계: 공급지별 수요(w_demand)를 고려한 Rj 산정 
    data['w_demand'] = data['demand_val'] * data['qij']
    w_demand = w_demand.groupby(supply_id, as_index = False)\
        .agg(sum_w_demand = ('w_demand', 'sum'))
    
    rj = supply_data.merge(w_demand, how = 'left', on = supply_id)
    rj['rj'] = rj['supply_val'] / rj['sum_w_demand']
    rj.loc[np.isinf(rj['rj']), ['rj']] = 0
    rj = rj[[supply_id, 'rj']]   

    # 2단계: 수요지별로 Rj 합산
    data = data.merge(rj, how = 'left', on = supply_id)
    data['w_rj'] = data['rj'] * data['qij']
    access = data.groupby(demand_id, as_index = False)\
        .agg(accessibility = ('w_rj', 'sum'))
    
    avg_access = access['accessibility'].mean()
    access['spar'] = access['accessibility']/avg_access - 1

    result = demand_data.merge(access, how = 'left', on = 'demand_id')
    result = result[['demand_id', 'accessibility', 'spar']]

    end_time = datetime.datetime.now()
    duration = end_time - start_time

    print(f'Procedure has finished. It takes {duration} seconds')
    
    return result 

# Congested Supply Accessibility
def CongestedFCA(demand_data, supply_data, cost_data, threshold):
    
    start_time = datetime.datetime.now()

    print("Congested Supply Accessibility Procedure started")
    print("\n")

    # 컬럼 정리
    demand_data.columns = ['demand_id', 'demand_val']
    supply_data.columns = ['supply_id', 'supply_val']
    cost_data.columns = ['demand_id', 'supply_id', 'cost_val']

    # 분석용 데이터 생성
    data = cost_data.merge(demand_data, how = 'left', on = 'demand_id')\
          .merge(supply_data, how = 'left', on = 'supply_id')
    
    # threshold에 따른 impedence beta 산정
    impedance_beta = -(threshold**2)/np.log(0.001)
    
    # threshold를 기반으로 불필요한 OD pairs 삭제
    data = data.loc[data['cost_val'] <= threshold]

    # cost를 distance decay function을 활용하여 weight로 변경
    data['fij'] = gauss_w(data['cost_val'], beta = impedance_beta) 

    # -1단계: 정체(congestion) 수준을 고려한 Sj' 산정
    mj = mj['demand_id', 'accessibility']
    mj.columns = ['supply_id', 'mj']

    data = data.merge(sj, how = 'left', on = supply_id)
    
    # 0단계: 공급지 매력도를 고려한 수요 배분 확률(Huff 확률) qij 산정
    data['w_supply'] = data['sj'] * data['fij']
    w_supply = data.groupby(supply_id, as_index = False)\
        .agg(sum_w_supply = ('w_supply', 'sum'))
    data = data.merge(w_supply, how = 'left', on = 'supply_id')
    data['qij'] = data['w_supply'] / data['sum_w_supply']

    # 1단계: 공급지별 수요(w_demand)를 고려한 Rj 산정 
    data['w_demand'] = data['demand_val'] * data['qij']
    w_demand = w_demand.groupby(supply_id, as_index = False)\
        .agg(sum_w_demand = ('w_demand', 'sum'))
    
    rj = supply_data.merge(w_demand, how = 'left', on = supply_id)
    rj['rj'] = rj['supply_val'] / rj['sum_w_demand']
    rj.loc[np.isinf(rj['rj']), ['rj']] = 0
    rj = rj[[supply_id, 'rj']]   

    # 2단계: 수요지별로 Rj 합산
    data = data.merge(rj, how = 'left', on = supply_id)
    data['w_rj'] = data['rj'] * data['qij']
    access = data.groupby(demand_id, as_index = False)\
        .agg(accessibility = ('w_rj', 'sum'))
    
    avg_access = access['accessibility'].mean()
    access['spar'] = access['accessibility']/avg_access - 1

    result = demand_data.merge(access, how = 'left', on = 'demand_id')
    result = result[['demand_id', 'accessibility', 'spar']]

    end_time = datetime.datetime.now()
    duration = end_time - start_time

    print(f'Procedure has finished. It takes {duration} seconds')
    
    return result 

# Load and prepare data
network_data = pd.read_csv('c:/p/g2sfca/new_network_data.csv')
demand_data = pd.read_csv('c:/p/g2sfca/new_demand_data.csv')
supply_data = pd.read_csv('c:/p/g2sfca/new_supply_data.csv')

network_data = pd.merge(network_data, demand_data, on='demand_id', how='left')
network_data = pd.merge(network_data, supply_data, on='supply_id', how='left')

demand_id = 'demand_id'
demand_col = 'demand_col'
supply_id = 'supply_id'
supply_col = 'supply_col'
cost_col = 'cost_col'
catchment = 30
impedance_beta = 130.283

# Execute the modified 2SFCA with ABFC adjustment
result = Generalized2SFCA_ABFCAdjustment(network_data, demand_id, demand_col, supply_id, supply_col, cost_col, catchment, impedance_beta)

result.to_csv('data/re_accessibility_30.csv', index=False, encoding = 'utf-8-sig')
