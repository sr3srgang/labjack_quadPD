
from labjack_device import LabJackDevice
from _ljm_aux import *

lj_device = LabJackDevice(
        device_type=LabJackDeviceTypeEnum.T7,
        connection_type=LabJackConnectionTypeEnum.ETHERNET,
        device_identifier='192.168.1.92',
    )

# # working
# stream_in = lj_device.stream_in(["AIN0", "AIN1"], 10, sampling_rate_Hz=50e3, scans_per_read=50000)
# working
stream_in = lj_device.stream_in(["AIN0", "AIN1"], 1, sampling_rate_Hz=50e3,do_trigger=True)
data = stream_in
print(data)
# # too high sampling rate
# stream_in = lj_device.stream_in(["AIN0", "AIN1"], 10, sampling_rate_Hz=100e3, scans_per_read=50000)