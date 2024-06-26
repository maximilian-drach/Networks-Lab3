from typing import List
import itertools
import time
import numpy as np
import math
# Adapted from code by Zach Peats

# ======================================================================================================================
# Do not touch the client message class!
# ======================================================================================================================
MDP_K = 3
THROUGHPUT_CHUNKS = 10
LOG_FILE = "mpc.log"
# BUFFER_GROWTH_SEC = 5
class ClientMessage:
    """
    This class will be filled out and passed to student_entrypoint for your algorithm.
    """
    total_seconds_elapsed: float	  # The number of simulated seconds elapsed in this test
    previous_throughput: float		  # The measured throughput for the previous chunk in kB/s

    buffer_current_fill: float		    # The number of kB currently in the client buffer
    buffer_seconds_per_chunk: float     # Number of seconds that it takes the client to watch a chunk. Every
                                        # buffer_seconds_per_chunk, a chunk is consumed from the client buffer.
    buffer_seconds_until_empty: float   # The number of seconds of video left in the client buffer. A chunk must
                                        # be finished downloading before this time to avoid a rebuffer event.
    buffer_max_size: float              # The maximum size of the client buffer. If the client buffer is filled beyond
                                        # maximum, then download will be throttled until the buffer is no longer full

    # The quality bitrates are formatted as follows:
    #
    #   quality_levels is an integer reflecting the # of quality levels you may choose from.
    #
    #   quality_bitrates is a list of floats specifying the number of kilobytes the upcoming chunk is at each quality
    #   level. Quality level 2 always costs twice as much as quality level 1, quality level 3 is twice as big as 2, and
    #   so on.
    #       quality_bitrates[0] = kB cost for quality level 1
    #       quality_bitrates[1] = kB cost for quality level 2
    #       ...
    #
    #   upcoming_quality_bitrates is a list of quality_bitrates for future chunks. Each entry is a list of
    #   quality_bitrates that will be used for an upcoming chunk. Use this for algorithms that look forward multiple
    #   chunks in the future. Will shrink and eventually become empty as streaming approaches the end of the video.
    #       upcoming_quality_bitrates[0]: Will be used for quality_bitrates in the next student_entrypoint call
    #       upcoming_quality_bitrates[1]: Will be used for quality_bitrates in the student_entrypoint call after that
    #       ...
    #
    quality_levels: int
    quality_bitrates: List[float]
    upcoming_quality_bitrates: List[List[float]]

    # You may use these to tune your algorithm to each user case! Remember, you can and should change these in the
    # config files to simulate different clients!
    #
    #   User Quality of Experience =    (Average chunk quality) * (Quality Coefficient) +
    #                                   -(Number of changes in chunk quality) * (Variation Coefficient)
    #                                   -(Amount of time spent rebuffering) * (Rebuffering Coefficient)
    #
    #   *QoE is then divided by total number of chunks
    #
    quality_coefficient: float
    variation_coefficient: float
    rebuffering_coefficient: float
    audio_coefficient: float 
    # ======================================================================================================================

# Your helper functions, variables, classes here. You may also write initialization routines to be called
# when this script is first imported and anything else you wish.
throughput_estimate_list = []
throughput_estimate_list_longterm = []
prev_bitrate_list = []
def harmonic_mean(num_list):
    tot = 0
    for num in num_list:
        tot += (1/num)
    hmean = len(num_list) / tot
    max_abs_error = 0
    for num in num_list:
        abs_error = abs(hmean - num) / abs(num)
        if abs_error > max_abs_error:
            max_abs_error = abs_error
    return hmean, max_abs_error
def harmonic_mean_std(num_list):
    tot = 0
    # for num in num_list:
    #     tot += (1/num)
    # mean = len(num_list) / tot
    # tot = 1
    # for num in num_list:
    #     tot *= (num)
    # mean = tot**(1/len(num_list))
    
    for num in num_list:
        tot += num
    mean = tot/len(num_list)
    # for num in num_list:
    #     tot += (num**2)
    # mean = (tot/len(num_list))**(1/2)
    
    # abs_error = 0
    # for num in num_list:
    #     abs_error += (mean - num) / abs(num)
    #     # if abs_error > max_abs_error:
    #         # max_abs_error = abs_error
    # abs_error = abs_error / len(num_list)
    error = 0
    for num in num_list:
        error += ((mean - num)**2) 
        # if abs_error > max_abs_error:
            # max_abs_error = abs_error
    error = (error/len(num_list))**(1/2)
    return mean, error

def index_list_creator(number_bitrate_levels, mdp_k):
    list_MDP_K_vals = []
    for i in range(number_bitrate_levels):
        list_MDP_K_vals.append(i)
    # print(list_MDP_K_vals)
    combinations_MDP_addr = itertools.product(list_MDP_K_vals, repeat=mdp_k)
    combinations_MDP = []
    for i in combinations_MDP_addr:
        combinations_MDP.append(list(i))

    return combinations_MDP

def MDP_bitrate_chuck_list(index_combination_list, MDP_bitrate_list):
    # print(index_combination_list, MDP_bitrate_list)
    # print(len(index_combination_list[0]), len(MDP_bitrate_list))
    assert(len(index_combination_list[0]) == len(MDP_bitrate_list))
    bitrate_level_list = []
    for indexes in index_combination_list:
        temp_list = []
        for i in range(len(indexes)):
            temp_list.append(MDP_bitrate_list[i][indexes[i]]*(2**indexes[i]))
        bitrate_level_list.append(temp_list)
    return bitrate_level_list


def test(client_message: ClientMessage):
    print(vars(client_message))


# def QoE_Score_Dynamic_Chunk(client_message, video_quality_Rk, video_quality_Rk_1, C_estimate, buffer_occupancy):
# 	QoE = (client_message.quality_coefficient*sum(video_quality_Rk) 
# 	- client_message.variation_coefficient*sum([abs(video_quality_Rk_1[i] - video_quality_Rk[i]) for i in range(len(video_quality_Rk))])
# 	- client_message.rebuffering_coefficient*sum([max(((video_quality_Rk[i] / C_estimate) - (buffer_occupancy)),0) for i in range(len(video_quality_Rk))]))
# 	# _QoE = client_message.quality_coefficient*sum(video_quality_Rk) 
# 	# print(_QoE == QoE)
# 	return QoE

def QoE_Score_Dynamic_Chunk(client_message, video_quality_Rk, video_quality_Rk_1, C_estimate, buffer_occupancy):
    #max -10
    QoE = ((client_message.quality_coefficient*sum(video_quality_Rk) / len(video_quality_Rk))
    - (client_message.variation_coefficient*sum([abs(video_quality_Rk_1[i] - video_quality_Rk[i]) for i in range(len(video_quality_Rk))]) / len(video_quality_Rk))
    - client_message.rebuffering_coefficient*sum([max(((video_quality_Rk[i] / C_estimate) - (buffer_occupancy)), -10) for i in range(len(video_quality_Rk))]))
    # _QoE = client_message.quality_coefficient*sum(video_quality_Rk) 
    # print(_QoE == QoE)
    return QoE#, [(client_message.quality_coefficient*sum(video_quality_Rk) / len(video_quality_Rk)),- (client_message.variation_coefficient*sum([abs(video_quality_Rk_1[i] - video_quality_Rk[i]) for i in range(len(video_quality_Rk))]) / len(video_quality_Rk)), - client_message.rebuffering_coefficient*sum([max(((video_quality_Rk[i] / C_estimate) - (buffer_occupancy)),0) for i in range(len(video_quality_Rk))])]

# def QoE_Score_Static_Chunk(client_message, video_quality_Rk_int, video_quality_Rk_chunck, video_quality_Rk_1, C_estimate, buffer_occupancy):
#     # print(client_message.rebuffering_coefficient*sum([((video_quality_Rk_chunck[i] / C_estimate) - (buffer_occupancy)) for i in range(len(video_quality_Rk_chunck))]))
#     #change max to -12 
#     # QoE = ((client_message.quality_coefficient*sum(video_quality_Rk_chunck)/len(video_quality_Rk_int))
#     QoE = ((client_message.quality_coefficient*sum(video_quality_Rk_int)/len(video_quality_Rk_int))
#     - (client_message.variation_coefficient*sum([abs(video_quality_Rk_1[i] - video_quality_Rk_int[i]) for i in range(len(video_quality_Rk_int))]) / len(video_quality_Rk_int))
#     - client_message.rebuffering_coefficient*max(sum([max((video_quality_Rk_chunck[i] / C_estimate) - (buffer_occupancy+i), -BUFFER_GROWTH_SEC) for i in range(len(video_quality_Rk_chunck))]), -MDP_K*BUFFER_GROWTH_SEC))
#     #  - client_message.rebuffering_coefficient*sum([max((video_quality_Rk_chunck[i] / C_estimate) - (buffer_occupancy+i), -BUFFER_GROWTH_SEC) for i in range(len(video_quality_Rk_chunck))]))
#     return QoE


def QoE_Score_Static_Chunk(client_message, video_quality_Rk_int, video_quality_Rk_chunck, C_estimate, buffer_occupancy):
    # print(client_message.rebuffering_coefficient*sum([((video_quality_Rk_chunck[i] / C_estimate) - (buffer_occupancy)) for i in range(len(video_quality_Rk_chunck))]))
    #change max to -12 
    # QoE = ((client_message.quality_coefficient*sum(video_quality_Rk_chunck)/len(video_quality_Rk_int))
    QoE = ((client_message.quality_coefficient*sum(video_quality_Rk_int)/len(video_quality_Rk_int))
    - client_message.rebuffering_coefficient*sum([max((video_quality_Rk_chunck[i] / C_estimate) - (buffer_occupancy+ (i*.1)), 0) for i in range(len(video_quality_Rk_chunck))])
    )
    
    #  - client_message.rebuffering_coefficient*sum([max((video_quality_Rk_chunck[i] / C_estimate) - (buffer_occupancy+i), -BUFFER_GROWTH_SEC) for i in range(len(video_quality_Rk_chunck))]))
    return QoE


# def QoE_Score_Static_Chunk(client_message, video_quality_Rk_int, video_quality_Rk_chunck, video_quality_Rk_1, C_estimate, C_longterm, past_bitrate_level_1, buffer_occupancy, buffer_growth_per_chunk_limit):
#     # print(client_message.rebuffering_coefficient*sum([((video_quality_Rk_chunck[i] / C_estimate) - (buffer_occupancy)) for i in range(len(video_quality_Rk_chunck))]))
#     #change max to -12 
#     # QoE = ((client_message.quality_coefficient*sum(video_quality_Rk_chunck)/len(video_quality_Rk_int))
#     QoE = ((client_message.quality_coefficient*sum(video_quality_Rk_int)/len(video_quality_Rk_int))
#     - (client_message.variation_coefficient*sum([abs(video_quality_Rk_1[i] - video_quality_Rk_int[i]) for i in range(len(video_quality_Rk_int))]) / len(video_quality_Rk_int))
#     - (sum([max(((video_quality_Rk_chunck[i]/C_estimate) - buffer_occupancy),0) + max(((past_bitrate_level_1[i] / C_longterm) - buffer_occupancy), 0) for i in range(len(video_quality_Rk_chunck))]))
#     )
    # return QoE
             
    

def logger(message: ClientMessage, quality: int, throughput_list, C_esti, C_err, nfile):
    # if(self.log):
    if nfile == False:
        with open(LOG_FILE, 'a') as f:
            occupancy = message.buffer_seconds_until_empty / message.buffer_max_size
            f.write(f"{occupancy},{quality/(message.quality_levels-1)},{message.quality_bitrates[quality]},{throughput_list[len(throughput_list)-1]},{C_esti},{C_err}\n")
            f.close()
    else:
        with open(LOG_FILE, 'w') as f:
            occupancy = message.buffer_seconds_until_empty / message.buffer_max_size
            f.write(f"{occupancy},{quality/(message.quality_levels-1)},{message.quality_bitrates[quality]},{throughput_list[len(throughput_list)-1]},{C_esti},{C_err}\n")
            f.close()

def bitrate_averages(prev_bitrate_list):
    prev_bitrate_list_avrgs = []
    for i in range(len(prev_bitrate_list[0])):
        prev_bitrate_list_avrgs.append(0)  
    for i in range(len(prev_bitrate_list)):
        for j in range(len(prev_bitrate_list[i])):
            prev_bitrate_list_avrgs[j] += prev_bitrate_list[i][j]
    for i in range(len(prev_bitrate_list_avrgs)):
        prev_bitrate_list_avrgs[i] = prev_bitrate_list_avrgs[i] / len(prev_bitrate_list)
    return prev_bitrate_list_avrgs 

def voice_bitrate_algorithm(client_message, C_esti, C_esti_long, prev_bitrates_vals):
    prev_avg_bitrate_vals = bitrate_averages(prev_bitrates_vals)
    buffer_level = client_message.buffer_seconds_until_empty
    Best_QoE = float("-inf")
    Best_Bitrate_level = 0
    for i in range(len(prev_avg_bitrate_vals)):
        QoE = client_message.quality_coefficient*i - client_message.rebuffering_coefficient*(max((prev_avg_bitrate_vals[i]/C_esti - buffer_level),0)) - client_message.audio_coefficient*max((prev_avg_bitrate_vals[i]/C_esti - buffer_level),0)
        if QoE > Best_QoE:
            Best_Bitrate_level = i
            Best_QoE = QoE
    return Best_Bitrate_level

# def MPC_voice_bitrate_algorithm(client_message, C_esti, C_esti_long, prev_bitrates_vals):
#     index_list = index_list_creator(len(prev_bitrates_vals[0]),  len(prev_bitrates_vals))
#     video_quality_Rk_MDP_list = MDP_bitrate_chuck_list(index_list, prev_avg_bitrate_vals)
#     prev_avg_bitrate_vals = bitrate_averages(prev_bitrates_vals)
#     buffer_level = client_message.buffer_seconds_until_empty
#     Best_QoE = float("-inf")
#     Best_QoE_List = []
#     for i in range(len(video_quality_Rk_MDP_list)):
#         temp_QoE = QoE_Score_Static_Chunk(client_message, index_list[i], video_quality_Rk_MDP_list[i], C_esti, client_message.buffer_seconds_until_empty)
#         if temp_QoE > Best_QoE:
#             Best_QoE = temp_QoE
#             Best_QoE_List = video_quality_Rk_MDP_list[i]
#     return Best_QoE, Best_QoE_List

global bitrate_choice
bitrate_choice = 0
global new_file
new_file = True
global buffer_deficit
buffer_deficit = 0
# global c_tot_esti
# c_tot_esti = 0
def student_entrypoint(client_message: ClientMessage):
    """
    Your mission, if you choose to accept it, is to build an algorithm for chunk bitrate selection that provides
    the best possible experience for users streaming from your service.

    Construct an algorithm below that selects a quality for a new chunk given the parameters in ClientMessage. Feel
    free to create any helper function, variables, or classes as you wish.

    Simulation does ~NOT~ run in real time. The code you write can be as slow and complicated as you wish without
    penalizing your results. Focus on picking good qualities!

    Also remember the config files are built for one particular client. You can (and should!) adjust the QoE metrics to
    see how it impacts the final user score. How do algorithms work with a client that really hates rebuffering? What
    about when the client doesn't care about variation? For what QoE coefficients does your algorithm work best, and
    for what coefficients does it fail?

    Args:
        client_message : ClientMessage holding the parameters for this chunk and current client state.

    :return: float Your quality choice. Must be one in the range [0 ... quality_levels - 1] inclusive.
    """
    # new_file = True
    global bitrate_choice
    global new_file
    global buffer_deficit
    # global c_tot_esti
    if client_message.total_seconds_elapsed > 0:
        bitrate_choice = 0
        throughput_estimate_list.append(client_message.previous_throughput)
        throughput_estimate_list_longterm.append(client_message.previous_throughput)
        if(len(throughput_estimate_list) > THROUGHPUT_CHUNKS):
            del throughput_estimate_list[0]
        c_esti, c_esti_err = harmonic_mean(throughput_estimate_list)
        C_Estimate_err = c_esti / (1 + c_esti_err)
        C_Estimate = c_esti
        C_Estimate_voice = C_Estimate - client_message.quality_bitrates[0]*.1
        # print(throughput_estimate_list)
        # print(C_Estimate_voice)
        # print(client_message.quality_bitrates[0])
        # print(client_message.buffer_seconds_until_empty)
        # print(client_message.upcoming_quality_bitrates)
        
        if (len(throughput_estimate_list_longterm) > 2*client_message.buffer_max_size):
            del throughput_estimate_list_longterm[0]
        c_esti, c_esti_err = harmonic_mean(throughput_estimate_list_longterm)
        # Longterm = np.array(throughput_estimate_list)
        # # C_Estimate_Longterm = np.mean(Longterm)
        # # C_Estimate_Longterm = C_Estimate_Longterm - 3*np.std(Longterm)
        C_Estimate_Longterm = c_esti / (1 + c_esti_err)
        C_Estimate_Longterm_voice = C_Estimate_Longterm - client_message.quality_bitrates[0]*.1
        prev_bitrate_list.append(client_message.quality_bitrates)
        if len(prev_bitrate_list) > MDP_K:
            del prev_bitrate_list[0]
        
        bitrate_choice = voice_bitrate_algorithm(client_message, C_Estimate_voice, C_Estimate_Longterm_voice,prev_bitrate_list)
        # Robust_MPC(client_message, prev_bitrates, C_Estimate_voice, C_Estimate_Longterm)
        
        # num_upcoming = min(len(client_message.upcoming_quality_bitrates), int(2*client_message.buffer_max_size))
        # # c_tot_esti = ALPHA * c_tot_esti + (1-ALPHA)*C_Estimate
        # # print(f" prev th {client_message.previous_throughput}, c esti {c_esti}, err {c_esti_err}, C EST {C_Estimate}")
        # # print(f"buffer level: {client_message.buffer_seconds_until_empty}, prev_c {client_message.previous_throughput}")
        # if len(client_message.upcoming_quality_bitrates) > 0:
        #     longterm_bitrate_mean,longterm_bitrate_mean_error = harmonic_mean_std([(client_message.upcoming_quality_bitrates[j][0]) for j in range(num_upcoming)])
        #     # longterm_bitrate_mean = sorted([(client_message.upcoming_quality_bitrates[0][bitrate_choice]) for j in range(num_upcoming)])[int(num_upcoming/2)]
        #     Best_QoE, Best_QoE_List = Robust_MPC(client_message, C_Estimate, C_Estimate_Longterm, longterm_bitrate_mean, 6)
        #     bitrate_choice = [client_message.quality_bitrates[i]*(2**i) for i in range(len(client_message.quality_bitrates))].index(Best_QoE_List[0])
        #     logger(client_message, bitrate_choice, throughput_estimate_list, C_Estimate, c_esti_err, new_file)
        #     new_file = False
        #     # print(f"buffer level: {round(client_message.buffer_seconds_until_empty,3)}, prev_c {round(client_message.previous_throughput,3)}, esti_c {round(C_Estimate, 3)}, esti_c_long {round(C_Estimate_Longterm, 3)}, bitrate options {client_message.quality_bitrates} bitrate selected {bitrate_choice}, avrg_upcoming_rate {round(sum([(client_message.upcoming_quality_bitrates[j][0]) for j in range(num_upcoming)])/num_upcoming,3)},{round(sum([(client_message.upcoming_quality_bitrates[j][1]) for j in range(num_upcoming)])/num_upcoming,3)},{round(sum([(client_message.upcoming_quality_bitrates[j][2]) for j in range(num_upcoming)])/num_upcoming,3)}, chunk {238-len(client_message.upcoming_quality_bitrates)}")
        return bitrate_choice
        # else:
            # return bitrate_choice

    else:
        bitrate_choice = 0
        return bitrate_choice # Let's see what happens if we select the lowest bitrate every time
    # print(client_message.quality_bitrates)
    # return 0
