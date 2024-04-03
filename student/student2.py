from typing import List
import math

# Adapted from code by Zach Peats

# ======================================================================================================================
# Do not touch the client message class!
# ======================================================================================================================

UPPER_RESERVOIR = 1/6
SMOOTHING_PARAMETER = 1/8
LOG_FILE = "bba.log"

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

class BBA:
	def __init__(self, log=True):
		self.mu_vbr = 0.0
		self.num_chunks = 0
		self.log = log

		self.startup = True
		self.last_chunk = 0.0
		self.last_quality = 0

		if(self.log):
			f = open(LOG_FILE, 'w')
			f.close()


	def __call__(self, message: ClientMessage):
		self.mu_vbr = (self.mu_vbr*self.num_chunks + message.quality_bitrates[0])  / (self.num_chunks+1)
		self.num_chunks += 1

		num_upcoming = min(len(message.upcoming_quality_bitrates), int(2*message.buffer_max_size))
		delta_buf = sum([r[0] - self.mu_vbr for r in message.upcoming_quality_bitrates[0:num_upcoming]]) / self.mu_vbr
		reservoir = min(max(delta_buf, 8.0), message.buffer_max_size * .6)
		
		upper_reservoir = message.buffer_max_size*UPPER_RESERVOIR

		occupancy = message.buffer_seconds_until_empty
		quality = 0
		if(occupancy < reservoir): quality = 0
		elif(occupancy > (message.buffer_max_size - upper_reservoir)): quality = message.quality_levels-1
		else: quality = int(math.floor((message.quality_levels) * ((occupancy - reservoir) / (message.buffer_max_size - reservoir - upper_reservoir))))

		if self.startup and self.num_chunks > 1:
			delta_time = message.total_seconds_elapsed - self.last_chunk
			if delta_time > message.buffer_seconds_per_chunk or quality > self.last_quality: 
				print(f"leaving startup @ t={self.num_chunks}")
				self.startup=False
			elif occupancy >= reservoir and delta_time < message.buffer_seconds_per_chunk * 0.5:
				quality = min(self.last_quality+1, message.quality_levels-1)
			elif occupancy < reservoir and delta_time < message.buffer_seconds_per_chunk * 0.125:
				quality = min(self.last_quality+1, message.quality_levels-1)
			else: quality = self.last_quality
			
		# farther smoothing: implement a schmitt trigger
		if delta_buf > (SMOOTHING_PARAMETER*message.buffer_max_size) and quality > self.last_quality: quality = self.last_quality

		self.last_quality = quality
		self.last_chunk = message.total_seconds_elapsed
		return quality
	
	def logger(self, message: ClientMessage, quality: int):
		if(self.log):
			with open(LOG_FILE, 'a') as f:
				occupancy = message.buffer_seconds_until_empty / message.buffer_max_size
				f.write(f"{occupancy},{quality/(message.quality_levels-1)},{message.quality_bitrates[quality]}\n")
				f.close()

global bba
bba = None

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
	global bba
	if bba is None: 
		print("initalizing bba")
		bba = BBA()

	quality = bba(client_message)
	bba.logger(client_message, quality)
	return quality
