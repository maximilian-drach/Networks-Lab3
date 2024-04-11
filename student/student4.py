from typing import List
import itertools
import time

# Adapted from code by Zach Peats

# ======================================================================================================================
# Do not touch the client message class!
# ======================================================================================================================
MDP_K = 5
THROUGHPUT_CHUNKS = 5
LOG_FILE = "mpc.log"
ALPHA = .875
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
    # ======================================================================================================================

# Your helper functions, variables, classes here. You may also write initialization routines to be called
# when this script is first imported and anything else you wish.
throughput_estimate_list = []

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

def QoE_Score_Static_Chunk(client_message, video_quality_Rk_int, video_quality_Rk_chunck, video_quality_Rk_1, C_estimate, buffer_occupancy):
    # print(client_message.rebuffering_coefficient*sum([((video_quality_Rk_chunck[i] / C_estimate) - (buffer_occupancy)) for i in range(len(video_quality_Rk_chunck))]))
    #change max to -12 
    # QoE = ((client_message.quality_coefficient*sum(video_quality_Rk_chunck)/len(video_quality_Rk_int))
    QoE = ((client_message.quality_coefficient*sum(video_quality_Rk_int)/len(video_quality_Rk_int))
    - (client_message.variation_coefficient*sum([abs(video_quality_Rk_1[i] - video_quality_Rk_int[i]) for i in range(len(video_quality_Rk_int))]) / len(video_quality_Rk_int))
    - client_message.rebuffering_coefficient*sum([max((video_quality_Rk_chunck[i] / C_estimate) - (buffer_occupancy), 0) for i in range(len(video_quality_Rk_chunck))]))
    return QoE

        

def Robust_MPC(client_message, C_estimate):

    buffer_occupancy = client_message.buffer_seconds_until_empty
    video_quality_Rk = [client_message.quality_bitrates]
    # print(video_quality_Rk)
    if len(client_message.upcoming_quality_bitrates) >= MDP_K:
        video_quality_Rk1 = client_message.upcoming_quality_bitrates[0:(MDP_K)]
        #extends the video quaility list to the next MDP amount
        video_quality_Rk.extend(video_quality_Rk1[0:(MDP_K-1)])
        # print(len(video_quality_Rk[0]))
        index_list = index_list_creator(len(video_quality_Rk[0]), MDP_K)
        video_quality_Rk_MDP_list = MDP_bitrate_chuck_list(index_list, video_quality_Rk)
        video_quality_Rk1_MDP_list = MDP_bitrate_chuck_list(index_list, video_quality_Rk1)
    else:
        video_quality_Rk1 = client_message.upcoming_quality_bitrates[0:len(client_message.upcoming_quality_bitrates)]
        video_quality_Rk.extend(video_quality_Rk1[0:(len(client_message.upcoming_quality_bitrates)-1)])
        # print(video_quality_Rk)
        # print(len(video_quality_Rk[0]))
        index_list = index_list_creator(len(video_quality_Rk[0]), len(client_message.upcoming_quality_bitrates))
        # if len(index_list[0]) == 0:
        # 	print("**\n\n**")
        # 	print(len(client_message.upcoming_quality_bitrates))
        # 	index_list = index_list_creator(3, len(client_message.upcoming_quality_bitrates)+1)
        # 	print(index_list)
        video_quality_Rk_MDP_list = MDP_bitrate_chuck_list(index_list, video_quality_Rk)
        video_quality_Rk1_MDP_list = MDP_bitrate_chuck_list(index_list, video_quality_Rk1)
    Best_QoE = float("-inf")
    Best_QoE_List = []
    for i in range(len(video_quality_Rk_MDP_list)):
        # if (client_message.rebuffering_coefficient*sum([((video_quality_Rk_MDP_list[i] / C_estimate) - (buffer_occupancy+i)) for i in range(len(video_quality_Rk_MDP_list[i]))])) >= 0:
        # temp_QoE = QoE_Score_Dynamic_Chunk(client_message, video_quality_Rk_MDP_list[i], video_quality_Rk1_MDP_list[i], C_estimate, buffer_occupancy)
        temp_QoE = QoE_Score_Static_Chunk(client_message, index_list[i], video_quality_Rk_MDP_list[i], index_list[i], C_estimate, buffer_occupancy)
        # print(temp_QoE)
        if temp_QoE > Best_QoE:
            # print(f"new best! {temp_QoE} > {Best_QoE} - {video_quality_Rk_MDP_list[i]}")
            Best_QoE = temp_QoE
            Best_QoE_List = video_quality_Rk_MDP_list[i]
            # print(video_quality_Rk_MDP_list[i])

    return Best_QoE, Best_QoE_List
   
             
    

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

    
    
global bitrate_choice
bitrate_choice = 0
global new_file
new_file = True
global c_tot_esti
c_tot_esti = 0
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
    global c_tot_esti
    if client_message.total_seconds_elapsed > 0:
        throughput_estimate_list.append(client_message.previous_throughput)
        if(len(throughput_estimate_list) > THROUGHPUT_CHUNKS):
            del throughput_estimate_list[0]
        c_esti, c_esti_err = harmonic_mean(throughput_estimate_list)
        # print(f" c esti {c_esti}, err {c_esti_err}")
        C_Estimate = c_esti / (1 + c_esti_err)
        c_tot_esti = ALPHA * c_tot_esti + (1-ALPHA)*C_Estimate
        # print(f" prev th {client_message.previous_throughput}, c esti {c_esti}, err {c_esti_err}, C EST {C_Estimate}")
        # print(f"buffer level: {client_message.buffer_seconds_until_empty}, prev_c {client_message.previous_throughput}")
        if len(client_message.upcoming_quality_bitrates) > 0:
            Best_QoE, Best_QoE_List = Robust_MPC(client_message, c_tot_esti)
            # print(f"Best QoE {Best_QoE}, QoE List {Best_QoE_List}")
            bitrate_choice = [client_message.quality_bitrates[i]*(2**i) for i in range(len(client_message.quality_bitrates))].index(Best_QoE_List[0])
            # print(Best_QoE_List[0], client_message.quality_bitrates, prev_bitrate)s
            # print(f"Best QoE {Best_QoE}, QoE List {Best_QoE_List}, Bitrate Choise {prev_bitrate}")
            logger(client_message, bitrate_choice, throughput_estimate_list, C_Estimate, c_esti_err, new_file)
            new_file = False
            # print(f"buffer level: {round(client_message.buffer_seconds_until_empty,3)}, prev_c {round(client_message.previous_throughput,3)}, esti_c {round(C_Estimate, 3)}, avg c {c_tot_esti}, bitrate options {client_message.quality_bitrates} bitrate selected {bitrate_choice}, chunk {238-len(client_message.upcoming_quality_bitrates)}")
            return bitrate_choice
        else:
            return bitrate_choice

    else:
        bitrate_choice = 0
        return bitrate_choice # Let's see what happens if we select the lowest bitrate every time
    # print(client_message.quality_bitrates)
    # return 0
