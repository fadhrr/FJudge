import os
import re
import signal
import subprocess

file_name = "temp/temp_c399d47b-1c4a-4752-b560-f0e8b6749687.py"
input_data = "2\n 5\n"

import signal, psutil
def kill_child_processes(parent_pid, sig=signal.SIGTERM):
    try:
      parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
      return
    children = parent.children(recursive=True)
    for process in children:
      process.send_signal(sig)

try:
    # Membuka subprocess
    process = subprocess.Popen(["memusage", "python", file_name], 
                                stdin=subprocess.PIPE, 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE, 
                                text=True)

    # Here you can get the PID
    child_pid = process.pid

    # Berinteraksi dengan subprocess dan menunggu hingga selesai atau timeout (5 detik)
    stdout, stderr = process.communicate(input=input_data, timeout=5)

    # Proses output jika subprocess selesai dengan sukses
    if process.returncode == 0:
        print("Output:", stdout)
        match = re.search(r'heap total:\s+(\d+)', stderr)
        if match:
            heap_total = int(match.group(1))
            print("Heap : ", int(heap_total / 1024))
        else:
            print("Heap total not found in the memusage output.")
    else:
        print("Error:", stderr)
        print("Status:", "RTE")
except subprocess.TimeoutExpired:
    print("Timeout terjadi, menghentikan proses...")
    kill_child_processes(child_pid)
    print("Killed?")
    # stdout, stderr = process.communicate()  # Ambil output terakhir jika diperlukan
    print("Proses telah dihentikan.")
except subprocess.CalledProcessError as e:
    # Tangani kesalahan saat menjalankan program Python
    print(str(e))
