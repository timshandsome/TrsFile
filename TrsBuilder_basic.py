from trsfile import trs_open, Trace, SampleCoding, TracePadding, Header
from trsfile.parametermap import TraceParameterMap, TraceSetParameterMap, TraceParameterDefinitionMap
from trsfile.traceparameter import ShortArrayParameter, StringParameter, ByteArrayParameter, ParameterType, \
     TraceParameterDefinition
import numpy as np
import sys, os
import matplotlib.pyplot as plt
import time
import math

# --------------------------------------------------------------------------------------------
file_type = 0         # 0: npy / 1: npz

Ptrace = 10
if Ptrace <= 0:
    sys.exit("Error! Ptrace must be >= 0")

# ---------------------------------------------------------------------------------------------
read_filename = {"traceset": list(), "dataset": list(), "key": list(), "parameter": list()}  # .np
write_filename = {"traceset": list(), "dataset": list(), "key": list()}  # .trs

r_path = "D:/SCA_data" + "/"
r_file = "III_M2351_20220829-1629" + "/"
npy_tracename = "M2351_traceset_20220829-1629.npy"
npy_dataname = "M2351_dataset_20220829-1629.npy"
npy_keyname = "M2351_key_20220829-1629.npy"
npz_filename = ""

if file_type == 0:
    read_filename["traceset"] = r_path + r_file + npy_tracename
    read_filename["dataset"] = r_path + r_file + npy_dataname
    read_filename["key"] = r_path + r_file + npy_keyname
    read_filename["parameter"] = r_path + r_file + "parameters.txt"
    traceset = np.load(read_filename["traceset"])
    dataset = np.load(read_filename["dataset"])
    key = np.load(read_filename["key"])
    samples = traceset.shape[1]
elif file_type == 1:
    npz_traceset_path = r_path + r_file + npz_filename
    npz_file = np.load(npz_traceset_path)
    traceset = npz_file["trace"]
    dataset = npz_file["data"]
    key = npz_file["key"]
    parameters = npz_file["parameter"]

sub_filename = {"filename": read_filename["traceset"].split(".")[0].rsplit("/")[-1],
                "format": read_filename["traceset"].split(".")[1]}

# ---------------------------------------------------------------------------------------------
start = time.time()
traceset = np.load(read_filename["traceset"])
dataset = np.load(read_filename["dataset"])
key = np.load(read_filename["key"])[0]

if file_type == 0:
    file = open(read_filename["parameter"], "r")
    parameters = {}
    for line in file.readlines():
        line = line.strip()
        k = line.split(": ")[0]
        v = line.split(": ")[1]
        parameters[k] = v
    file.close()

# ----------------------------------------------------
trace_size = {"Ntraces": int(parameters["traces"]), "samples": int(parameters["samples"])}
interval = math.ceil(1e-6 / int(parameters["sampling rate (MHz)"]) * 1e9) / 1e9
vrange = float(parameters["vrange (V)"])

# ----------------------------------------------------
dut_name = r_file.split("_")[1]
time_str = r_file.split("_")[-1].split("/")[0]
write_filename["traceset"] = r_path + r_file + dut_name + "_" + time_str + ".trs"
w_path = write_filename["traceset"]
print("Traceset: (Ntraces, Samples) = (" + str(trace_size["Ntraces"]) + ", " + str(trace_size["samples"]) + ")")
print("---------------------------------------------------------------------------------------------")
print("Waiting for file conversion...")

# --------------------------------------------------------------------------------------------
Ntraces = trace_size["Ntraces"]
data_size = {"Ndata": dataset.shape[0]}

# --------------------------------------------------------------------------------------------
with trs_open(
    w_path,  # File name of the trace set
    "w",  # Mode: r, w, x, a (default to x)
          # Zero or more options can be passed (supported options depend on the storage engine)
    engine="TrsEngine",  # Optional: how the trace set is stored (defaults to TrsEngine)
    headers={  # Optional: headers (see Header class)
        Header.TRS_VERSION: 2,
        Header.SCALE_X: interval,
        Header.SCALE_Y: 1,
        Header.LABEL_X: "s",
        Header.LABEL_Y: "V",
            Header.DESCRIPTION: "trsfile creation",
            Header.TRACE_PARAMETER_DEFINITIONS: TraceParameterDefinitionMap({
                "INPUT": TraceParameterDefinition(ParameterType.BYTE, 16, 0),
                "KEY": TraceParameterDefinition(ParameterType.BYTE, 16, 0),
                "TVLA:SET_INDEX": TraceParameterDefinition(ParameterType.SHORT, 1, 16)}),
            Header.TRACE_SET_PARAMETERS: TraceSetParameterMap({
                "TVLA:SET0": StringParameter("Random"),
                "TVLA:SET1": StringParameter("Fixed"),
                "TVLA:CIPHER": StringParameter("Fixed vs Random")})},
        padding_mode=TracePadding.AUTO,  # Optional: padding mode (defaults to TracePadding.AUTO)
        live_update=True  # Optional: updates the TRS file for live preview (small performance hit)
                          #   0 (False): Disabled (default)
                          #   1 (True) : TRS file updated after every trace
                          #   N        : TRS file is updated after N
    ) as traces:

    # Extend the trace file with n traces with each n samples
    for n_trace in range(trace_size["Ntraces"]):
        if n_trace % 2 == 0:
            set_No = [0]
            input_type = "Random"
        else:
            set_No = [1]
            input_type = "Fixed"

        traces.extend([
            Trace(
                SampleCoding.FLOAT,
                traceset[n_trace],
                TraceParameterMap({
                    "INPUT": ByteArrayParameter(bytes.fromhex(dataset[n_trace])),
                    "KEY": ByteArrayParameter(bytes.fromhex(key)),
                    "TVLA:SET_INDEX": ShortArrayParameter(set_No)}),
                title="Trace No." + str(n_trace) + " - " + str(input_type)
            )
        ])

# --------------------------------------------------------------------------------------------
np.set_printoptions(linewidth=200)  # a line print n char
print("\nTraceset:\n", traceset)
print("\nDataset:\n", dataset)

plt.figure(1)
figure = plt.gcf()
figure.patch.set_facecolor("white")
figure.set_size_inches(9, 6)
for p_trace in range(Ptrace):
    plt.plot(traceset[p_trace])
plt.title(sub_filename["filename"]); plt.xlabel("Samples")
plt.axis([0, trace_size["samples"] - 1, -vrange, vrange])
plt.show()
end = time.time()
print("\nExecution time (s): ", end - start); print("")
