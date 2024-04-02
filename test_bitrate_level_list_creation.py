import itertools

def index_list_creator(number_bitrate_levels, mdp_k):
    list_MDP_K_vals = []
    for i in range(number_bitrate_levels):
        list_MDP_K_vals.append(i)
    print(list_MDP_K_vals)
    combinations_MDP_addr = itertools.product(list_MDP_K_vals, repeat=mdp_k)
    combinations_MDP = []
    for i in combinations_MDP_addr:
        combinations_MDP.append(list(i))
    
    return combinations_MDP
def MDP_bitrate_chuck_list(index_combination_list, MDP_bitrate_list):
    assert(len(index_combination_list[0]) == len(MDP_bitrate_list))
    bitrate_level_list = []
    for indexes in index_combination_list:
        temp_list = []
        for i in range(len(indexes)):
            temp_list.append(MDP_bitrate_list[i][indexes[i]])
        bitrate_level_list.append(temp_list)
    return bitrate_level_list
        
# bitrate_options = [[1.0, 2.0, 4.0], [0.8, 1.6, 3.2], [0.8, 1.6, 3.2], [0.6, 1.2, 2.4], [0.6, 1.2, 2.4]]
bitrate_options = [[1.0, 2.0, 4.0], [0.8, 1.6, 3.2]]
index_options = index_list_creator(3, 2)
print(MDP_bitrate_chuck_list(index_options, bitrate_options))

def QoE_Score(client_message, video_quality_Rk, video_quality_Rk_1, C_estimate):
    
    QoE = client_message.quality_coefficient*sum(video_quality_Rk) 
    - client_message.variation_coefficient*sum([abs(video_quality_Rk_1[i] - video_quality_Rk[i]) for i in range(len(video_quality_Rk))])
    - client_message.rebuffering_coefficient*sum([((video_quality_Rk[i] / C_estimate) - (client_message.buffer_seconds_until_empty + i)) for i in range(len(video_quality_Rk))])
    return QoE