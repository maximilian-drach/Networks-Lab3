from matplotlib import pyplot as plt

#f.write(f"{occupancy},{quality/(client_message.quality_levels-1)},{client_message.quality_bitrates[quality]}\n")

with open("bba.log", "r") as f:
    points = f.read().split('\n')
    data = [x.split(',') for x in points[:-1]]
    f.close()
    occupancy = [float(x[0]) for x in data]
    quality = [float(x[1]) for x in data]
    bitrate = [float(x[2]) for x in data]

    fig, ax = plt.subplots(2)
    ax[0].plot(occupancy, color="orange")
    ax[0].set_ylabel("Occupancy")
    ax02 = ax[0].twinx()
    ax02.plot(quality, color="blue")
    ax02.set_ylabel("Quality")

    ax[1].plot(occupancy, color="orange")
    ax[1].set_ylabel("Occupancy")
    ax12 = ax[1].twinx()
    ax12.plot(bitrate, color="blue")
    ax12.set_ylabel("Real Bitrate")

    plt.show()