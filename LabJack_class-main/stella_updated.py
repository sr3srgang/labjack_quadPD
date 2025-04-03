from labjack_device import *
import time
import pandas as pd

import pandas as pd
import os
from pprint import pprint
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import traceback
import concurrent.futures

def find_valley_averages(time_array, signal_array, threshold):
    below = np.abs(signal_array) > threshold
    indices = np.flatnonzero(below)

    if len(indices) == 0:
        return []

    chunks = []
    chunk = [indices[0]]
    for i in range(1, len(indices)):
        if indices[i] == indices[i - 1] + 1:
            chunk.append(indices[i])
        else:
            chunks.append(chunk)
            chunk = [indices[i]]
    chunks.append(chunk)

    results = []
    for ch in chunks:
        avg_time = np.mean(time_array[ch])
        avg_val = np.mean(signal_array[ch])
        results.append((avg_time, avg_val))

    return results

def upload_to_influx(
    value,
    measurement,
    field,
    tag_key,
    tag_value,
    timestamp=None,
    influx_url="http://yesnuffleupagus.colorado.edu:8086",
    influx_token="yelabtoken",
    influx_org="yelab",
    influx_bucket="sr3"
):
    """Upload a value to InfluxDB as a single point."""
    # Create client and write API
    client = InfluxDBClient(url=influx_url, token=influx_token, org=influx_org)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    # Use current UTC time if not provided
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()

    # Create and write the point
    point = Point(measurement).tag(tag_key, tag_value).field(field, value).time(timestamp)
    write_api.write(bucket=influx_bucket, record=point)
    #print('sent')
    # Clean up
    write_api.close()
    client.close()


# lj_device = LabJackDevice(
#         device_type=LabJackDeviceTypeEnum.T7,
#         connection_type=LabJackConnectionTypeEnum.ETHERNET,
#         device_identifier='192.168.1.92',
#         #ch_names=["AIN10", "AIN13"],
#         #a_scan_list_names=["AIN10", "AIN12","AIN13","AIN11"],
#         a_scan_list_names=["AIN10", "AIN12"],
#         scan_rate=50e3,
#         scan_duration=.0065, # seconds
#         #num_reads=1,
#         do_trigger=True,
#         # trigger_mode=None,
#         # trigger_edge=None,
#         #trigger_ch_name="DIO0",
#         trigger_name="DIO0",
#     )
a_scan_list_names=["AIN1","AIN3","AIN12"]
#x is 1 sum is 12
lj_device = LabJackDevice(
    device_type=LabJackDeviceTypeEnum.T7,
    connection_type=LabJackConnectionTypeEnum.ETHERNET,
    device_identifier='192.168.1.92',
    #a_scan_list_names=a_scan_list_names,
    # scan_rate=30e3,
    # scan_duration=.6,
    # do_trigger=True,
    # trigger_mode=LabJackTriggerModeEnum.ConditionalReset,
    # trigger_edge=LabJackTriggerEdgeEnum.Rising,
    # trigger_name="DIO0",
)
#device = LabJackDevice(device_identifier='192.168.1.92')
device = lj_device
reference_times = {name: None for name in a_scan_list_names}
voltage_columns = {name: [] for name in a_scan_list_names}

save_interval = 1  # Save every 100 loops
output_csv = r"C:\Users\srgang\Desktop\LabJack_class\raw_profile.csv"
stream_in = lj_device.stream_in(["AIN1", "AIN3", "AIN12"], duration_s=1, sampling_rate_Hz=30e3, do_trigger=True)
for loop_index in range(2000):  # number of total triggers
    print(f"Loop {loop_index}")
    import time

    start_time = time.perf_counter()
    #data = device.stream_in(scan_channels= ["AIN1", "AIN3","AIN12"],duration_s = .002,sampling_rate_Hz=30e3,do_trigger=True)
    stream_in._stream_in()
    data = stream_in
    #print("StreamIn object:", type(data))
    #print("dir(data):", dir(data))
    #print('data')
    #data = data.to_dict()
    #print(data)
    end_time = time.perf_counter()

    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.4f} seconds")
    for chan_name in a_scan_list_names:
        V_raw = np.array(data.records[chan_name]['V'])  
        t_raw = np.array(data.records[chan_name]['t'])
        if chan_name in ["AIN1", "AIN3"]:
        # Subtract mean before valley detection
            V_centered = V_raw - np.mean(V_raw)

            # Find valleys below threshold (absolute value)
            threshold = 0.002  # adjust this value as needed
            valleys = find_valley_averages(t_raw, V_centered, threshold=.005)

            # Labels to use for left-to-right valleys
            labels = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"]

            for i, (avg_time, avg_val) in enumerate(valleys):
                if i >= len(labels):
                    label = f"extra{i+1}"
                else:
                    label = labels[i]

                tag_str = f"{chan_name}_{label}"
                print(f"Uploading: {tag_str} with avg_val = {avg_val:.6f} at avg_time = {avg_time:.6f}")

                try:
                    upload_to_influx(
                        value=avg_val,
                        measurement="valley_measurement",
                        field="avg_voltage",
                        tag_key="channel",
                        tag_value=tag_str,
                        timestamp=datetime.utcnow().isoformat()
                    )
                except Exception as e:
                    print(f"Failed to upload {chan_name} ({tag_str}): {e}")
                    traceback.print_exc()

    # for chan_name in a_scan_list_names:
    #     V_raw = np.array(data.records[chan_name]['V'])  
    #     t_raw = np.array(data.records[chan_name]['t'])
    #     #print('t_raw')
    #     #print(t_raw)
    #     if chan_name in ["AIN1", "AIN3"]:
    #         intervals = [
    #                         (180, 286, "first"),
    #                         (857, 908, "second"),
    #                         (4458, 4563, "third"),
    #                         (7992, 8045, "fourth"),
    #                         (11198, 11250, "fifth"),
    #                         (17683, 17788, "sixth"),
    #                         (24415, 24520, "seventh"),
    #                     ]
            
    #         # intervals = [
    #         #                 (60, 95, "first"),
    #         #                 (276, 292, "second"),
    #         #                 (1474, 1510, "third"),
    #         #                 (5633, 5669, "fourth"),
    #         #                 (7875,7910, "fifth")
                            
    #         #             ]

    #                     #Loop over intervals and upload
    #         for start, end, label in intervals:
    #             avg_val = np.mean(V_raw[start:end])
    #             tag_str = f"{chan_name}_{label}"
    #             print(f"Uploading: {tag_str} with avg_val = {avg_val:.6f}")

    #             try:
    #                 upload_to_influx(
    #                     value=avg_val,
    #                     measurement="valley_measurement",
    #                     field="avg_voltage",
    #                     tag_key="channel",
    #                     tag_value=tag_str,
    #                     timestamp=datetime.utcnow().isoformat()
    #                 )
    #             except Exception as e:
    #                 print(f"Failed to upload {chan_name} ({tag_str}): {e}")
    #                 traceback.print_exc()

        if reference_times[chan_name] is None:
                    reference_times[chan_name] = t_raw
        else:
            if not np.allclose(t_raw, reference_times[chan_name], rtol=1e-6, atol=1e-9):
                raise ValueError(f"Time for {chan_name} at loop {loop_index} does not match first sweep.")

        voltage_columns[chan_name].append(V_raw)

    
        if (loop_index + 1) % save_interval == 0:
            print(f"Saving to CSV at loop {loop_index + 1}")
            data_dict = {}

            # Add time columns
            for chan_name in a_scan_list_names:
                data_dict[f"{chan_name}_t"] = reference_times[chan_name]

            # Use shortest length across all channels
            min_len = min(len(voltage_columns[chan]) for chan in a_scan_list_names)

            # Add voltage columns
            for i in range(min_len):
                for chan_name in a_scan_list_names:
                    data_dict[f"{chan_name}_V_{i}"] = voltage_columns[chan_name][i]

            raw_df = pd.DataFrame(data_dict)
            raw_df.to_csv(output_csv, index=False)
            print(f"Saved")
del device 
# num_loops = 5  
# pause_time = 1  
# data = lj_device.stream(num_loops=num_loops, pause_between_loops=pause_time)

# def safe_stream_call(device, timeout=10):
#     """Runs lj_device.stream() with a timeout. Returns None on timeout."""
#     with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
#         future = executor.submit(device.stream)
#         try:
#             return future.result(timeout=timeout)
#         except concurrent.futures.TimeoutError:
#             print(f"stream() timed out after {timeout} seconds.")
#             return None
        


# channel_data = {}  # Will hold arrays like "AIN10_V", "AIN10_t", etc.
# end_time = np.array([])

# # Initialize arrays for all channels
# for ch in lj_device.a_scan_list_names:
#     channel_data[f"{ch}_V"] = np.array([])
#     channel_data[f"{ch}_t"] = np.array([])

# for i in range(500):
#     print(i)

#     data = lj_device.stream()
#     print(data)

#     # Process each channel dynamically
#     for ch in lj_device.a_scan_list_names:
#         V_avg = np.average(data["records"][ch]["V"])
#         t_avg = np.average(data["records"][ch]["t"])

#         # Append values
#         channel_data[f"{ch}_V"] = np.append(channel_data[f"{ch}_V"], V_avg)
#         channel_data[f"{ch}_t"] = np.append(channel_data[f"{ch}_t"], t_avg)

#         # Upload to Influx
#         upload_to_influx(
#             value=V_avg,
#             measurement="PDLog",
#             field="Volts",
#             tag_key="Channel",
#             tag_value=ch
#         )

#     # Append end_time once per iteration
#     end_time = np.append(end_time, data["end_time"])

#     # Add end_time to column data
#     all_columns = channel_data.copy()
#     all_columns["end_time"] = end_time

#     # Pad each array with NaNs to align columns
#     max_len = max(len(arr) for arr in all_columns.values())
#     for key in all_columns:
#         pad = max_len - len(all_columns[key])
#         if pad > 0:
#             all_columns[key] = np.pad(all_columns[key], (0, pad), constant_values=np.nan)

#     # Convert to DataFrame
#     df = pd.DataFrame(all_columns)
#     df["end_time"] = pd.to_datetime(df["end_time"])
#     df["end_time_offset_sec"] = (df["end_time"] - df["end_time"].iloc[0]).dt.total_seconds()

#     df.to_csv("data_output_new2.csv", index=False)
#     time.sleep(1)

# #pprint(AIN10_t)







# equivalent to:
# with LabJackDevice(
#         device_type=LabJackDeviceTypeEnum.T7,
#         connection_type=LabJackConnectionTypeEnum.ETHERNET,
#         device_identifier='192.168.1.92',
#         a_scan_list_names=["AIN10", "AIN13"],
#         # scan_rate=None,
#         scan_duration=1.5, # seconds
#         # num_reads=1,
#         do_trigger=True,
#         # trigger_mode=None,
#         # trigger_edge=None,
#         trigger_name="DIO0",
#     ) as lj_device:
#     lj_device.connect()
#     data = lj_device.stream()
        
# code to deal with `data`...
