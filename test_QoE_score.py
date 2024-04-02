import itertools
A = 2
B = 8
C = 1
MDP_K = 5

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

def QoE_Score(video_quality_Rk, video_quality_Rk_1, C_estimate, buffer_time):
    # print(sum(video_quality_Rk))
    QoE = A*sum(video_quality_Rk) 
    - B*sum([abs(video_quality_Rk_1[i] - video_quality_Rk[i]) for i in range(len(video_quality_Rk))])
    - C*sum([((video_quality_Rk[i] / C_estimate) - (buffer_time + i)) for i in range(len(video_quality_Rk))])
    return QoE

video_quality_Rk = [[1.0, 2.0, 4.0]]
print(video_quality_Rk)
video_quality_Rk_1 = [[1.0, 2.0, 4.0], [0.8, 1.6, 3.2], [0.8, 1.6, 3.2], [0.6, 1.2, 2.4], [0.6, 1.2, 2.4]]
video_quality_Rk.extend(video_quality_Rk_1[0:MDP_K-1])

print(video_quality_Rk)
print(video_quality_Rk_1)
index_list = index_list_creator(len(video_quality_Rk[0]), MDP_K)
print(index_list)
video_quality_Rk_MDP_list = MDP_bitrate_chuck_list(index_list, video_quality_Rk)
video_quality_Rk_1_MDP_list = MDP_bitrate_chuck_list(index_list, video_quality_Rk_1)
print(len(video_quality_Rk_MDP_list))


buffer_time = 1.0
best_QoE = 0
best_QoE_list = []
for i in range(len(video_quality_Rk_MDP_list)):
    temp_QoE = QoE_Score(video_quality_Rk_MDP_list[i], video_quality_Rk_1_MDP_list[i], C_estimate=2.0, buffer_time=buffer_time)
    if temp_QoE > best_QoE:
        best_QoE = temp_QoE
        best_QoE_list = video_quality_Rk_MDP_list[i]

print(QoE_Score(video_quality_Rk_MDP_list[0], video_quality_Rk_1_MDP_list[0], C_estimate=2.0, buffer_time=buffer_time))
print("**")
print(f"best Qoe {best_QoE}, best QoE buffer: {best_QoE_list}")
print(video_quality_Rk[0].index(best_QoE_list[0]))