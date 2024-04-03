from matplotlib import pyplot as plt

#f.write(f"{occupancy},{quality/(client_message.quality_levels-1)},{client_message.quality_bitrates[quality]}\n")

with open("mpc.log", "r") as f:
    points = f.read().split('\n')
    data = [x.split(',') for x in points[:-1]]
    f.close()
    occupancy = [float(x[0]) for x in data]
    quality = [float(x[1]) for x in data]
    bitrate = [float(x[2]) for x in data]
    C_curr = [float(x[3]) for x in data]
    C_esti = [float(x[4]) for x in data]
    C_err = [float(x[5]) for x in data]
    
    fig, ax = plt.subplots(3)
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
    
    ax[2].plot(C_curr, color="orange")
    ax[2].set_ylabel("Throughput Real")
    ax22 = ax[2].twinx()
    ax[2].plot(C_esti, color="blue")
    ax22.plot(C_err, color="red")
    ax22.set_ylabel("Throughput Estimate")

    plt.savefig("mpc_plot.jpg")