import json
from collections import deque

def handler(input: dict, context: object) -> dict:
    """
    Serverless function handler.
    Computes metrics and returns a JSON-serializable dictionary.
    """
    # Load previous state for moving averages
    if 'cpu_averages' not in context.env:
        context.env['cpu_averages'] = {}
    if 'cpu_data' not in context.env:
        context.env['cpu_data'] = {f"cpu_{i}": deque(maxlen=12) for i in range(len(input) if 'cpu_percent-0' in input else 1)}

    # Calculate outgoing network percentage
    net_out_total = input["net_io_counters_eth0-bytes_sent1"]
    net_total = net_out_total + input["net_io_counters_eth0-bytes_recv1"]
    percent_network_egress = (net_out_total / net_total) * 100 if net_total else 0

    # Calculate memory caching percentage
    percent_memory_cached = ((input["virtual_memory-cached"] + input["virtual_memory-buffers"]) /
                              input["virtual_memory-total"]) * 100

    # Compute moving average for each CPU
    cpu_utilization = {}
    for i in range(len(context.env['cpu_data'])):
        key = f"cpu_percent-{i}"
        if key in input:
            context.env['cpu_data'][f"cpu_{i}"].append(input[key])
            avg_util = sum(context.env['cpu_data'][f"cpu_{i}"]) / len(context.env['cpu_data'][f"cpu_{i}"])
            cpu_utilization[f"avg-util-cpu{i}-60sec"] = avg_util

    # Prepare result
    result = {
        "percent-network-egress": percent_network_egress,
        "percent-memory-cached": percent_memory_cached,
    }
    result.update(cpu_utilization)

    return result
