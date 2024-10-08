import os
import re
import signal
import time
import uuid
from fastapi import FastAPI, HTTPException, Body, Request, Cookie
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import psutil
from pydantic import BaseModel
from enum import Enum
from typing import List, Annotated, Optional, Union
import subprocess
from fastapi.staticfiles import StaticFiles
import uvicorn
from dotenv import load_dotenv

load_dotenv()


app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory='templates')
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get('/', response_class=HTMLResponse)
def main(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "base_url": str(request.base_url)})


languages = ["java", "cpp", "c", "py"]

class CodeExecutionRequest(BaseModel):
    identifier: Union[int, str]
    source_code: str
    language_id: int
    test_cases: List[dict]


class CodeExecutionResponse(BaseModel):
    identifier: Union[int, str]
    source_code: str
    language_id: int
    results: List[dict]
    avg_time: Optional[float] = None
    avg_memory: Optional[int] = None
    verdict: str


@app.post("/api/judge", response_model=CodeExecutionResponse)
async def judge(
    request: Annotated[
        CodeExecutionRequest,
        Body(
            openapi_examples={
                "py": {
                    "summary": "Python",
                    "description": "",
                    "value": {
                        "identifier": 0,
                        "source_code": "def add(a, b):\n    return a + b\n\na = int(input())\nb = int(input())\nprint(add(a,b))",
                        "language_id": 3,
                        "test_cases": [
                            {
                            "input": "2\n3\n",
                            "expected_output": "5\n"
                            },
                            {
                            "input": "5\n3\n",
                            "expected_output": "12\n"
                            }
                        ],
                    },
                },
                "cpp": {
                    "summary": "C/C++",
                    "description": "",
                    "value": {
                        "identifier": 0,
                        "source_code": "#include <iostream>\nusing namespace std;\nint main() {\n    int a, b;\n    cin >> a >> b;\n    cout << a + b << endl;\n    return 0;\n}",
                        "language_id": 2,
                        "test_cases": [
                            {
                            "input": "2 3\n",
                            "expected_output": "5\n"
                            },
                            {
                            "input": "5 7\n",
                            "expected_output": "12\n"
                            }
                        ],
                    },
                },
            },
        ),
    ],
):
    results = []
    verdict = ""

    session_id = str(uuid.uuid4())  # Menggunakan uuid sebagai session_id

    try:
        # Menjalankan source code dengan input tertentu
        result_test_cases = run_code(request.source_code, request.language_id, request.test_cases, session_id)

        results = result_test_cases

        # menghitung rata-rata time 
        total_time = 0
        total_memory = 0
        for result in results:
            total_time += result["time"]

            # temp solution
            if result["memory"] == None:
                continue
            total_memory += result["memory"]
            
        avg_time = total_time/len(results)
        avg_memory = total_memory/len(results)


        # test_num = 0
        for result in results:
            if "CTE" == result["status"]:
                verdict = f"CTE"
                break
            elif "RTE" == result["status"]:
                verdict = f"RTE"
                break
            elif "TLE" == result["status"]:
                verdict = f"TLE"
                break
            elif "WA" == result["status"]:
                verdict = f"WA"
                break
            elif "AC" == result["status"]:
                verdict = f"AC"
            
        # Membuat instansiasi dari model CodeExecutionResponse
        response_model = CodeExecutionResponse(identifier=request.identifier, source_code=request.source_code , language_id=request.language_id, results=results, avg_time=avg_time, avg_memory=avg_memory, verdict=verdict)
        return response_model

    except Exception as e:
        response_model = CodeExecutionResponse(identifier=request.identifier, source_code=request.source_code , language_id=request.language_id, results=results, avg_time=None, avg_memory=None , verdict=str(e))
        return response_model

def kill_child_processes(parent_pid, sig=signal.SIGTERM):
    try:
      parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
      return
    children = parent.children(recursive=True)
    for process in children:
      process.send_signal(sig)
      
def run_code(source_code, language_id, test_cases, session_id):
    results = []
    

    for test_case in test_cases:
        
        input_data = test_case.get("input", "")
        expected_output = test_case.get("expected_output", "")

        result_dict = {
            "input": input_data,
            "expected_output": expected_output,
            "actual_output": None,
            "status": None,
            # "err_msg": None,
            "time": None,
            "memory": None
        }

        # Menyimpan source code ke file sementara
        file_name = f"temp_{session_id}.{languages[language_id]}"
        with open(file_name, "w") as file:
            file.write(source_code)


        if languages[language_id] == "cpp" or languages[language_id] == "c":
            # Menjalankan kompilasi hanya jika belum pernah dikompilasi sebelumnya
            if not os.path.exists(f"temp_{session_id}"):
                compile_result = subprocess.run(["g++", "-g", file_name, "-o", f"temp_{session_id}"], capture_output=True)
                
                # untuk menampilkan warning error saat kompilasi
                # result_dict["err_msg"] = compile_result.stderr
                # print(compile_result)
                if compile_result.returncode != 0:
                    # Jika gagal kompilasi
                    result_dict["status"] = "CTE"
                    result_dict["time"] = 0
                    # result_dict["err_msg"] = compile_result.stderr
                    results.append(result_dict)

                    # Menghapus file sementara jika sudah selesai digunakan
                    os.remove(file_name)

                    # Mengembalikan hasil eksekusi
                    return results

        start_time = time.time()  # Waktu mulai eksekusi

        # Menjalankan source code dengan input tertentu menggunakan subprocess
        
        if languages[language_id] == "cpp" or languages[language_id] == "c":
            try:
                # result = subprocess.run(["memusage", f"./temp_{session_id}"], input=input_data, text=True, capture_output=True, timeout=5)  # Ganti 5 dengan batas waktu yang diinginkan (dalam detik)
                process = subprocess.Popen(["memusage", f"./temp_{session_id}"], 
                                stdin=subprocess.PIPE, 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE, 
                                text=True)
                
                # Here you can get the PID
                parent_pid = process.pid
                # print(result)

                # Berinteraksi dengan subprocess dan menunggu hingga selesai atau timeout (5 detik)
                stdout, stderr = process.communicate(input=input_data, timeout=2)
                result_dict["actual_output"] = stdout
                match = re.search(r'heap total:\s+(\d+)', stderr)

                if match:
                    heap_total = int(match.group(1))
                    # print("Heap total:", heap_total)
                    result_dict["memory"] = int(heap_total / 1024)
                else:
                    print("Heap total not found in the memusage output.")
                
                if process.returncode != 0:
                    result_dict["status"] = "RTE"

                # Menghapus file compiled jika sudah selesai digunakan
                os.remove(f"temp_{session_id}")
            except subprocess.TimeoutExpired:
                os.remove(f"temp_{session_id}")
                kill_child_processes(parent_pid)
                result_dict["status"] = "TLE"
            except subprocess.CalledProcessError as e:
                # Tangani kesalahan saat menjalankan program C++ yang dikompilasi
                result_dict["status"] = str(e)
        elif languages[language_id] == "py":
            try:
                # result = subprocess.run(["memusage", "python", file_name], input=input_data, text=True, capture_output=True, timeout=5)  # Ganti 5 dengan batas waktu yang diinginkan (dalam detik)
                # print(result)
                process = subprocess.Popen(["memusage", "python", file_name], 
                                stdin=subprocess.PIPE, 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE, 
                                text=True)
                
                # Here you can get the PID
                parent_pid = process.pid
                # print(result)

                # Berinteraksi dengan subprocess dan menunggu hingga selesai atau timeout (5 detik)
                stdout, stderr = process.communicate(input=input_data, timeout=2)
                result_dict["actual_output"] = stdout
                match = re.search(r'heap total:\s+(\d+)', stderr)

                if match:
                    heap_total = int(match.group(1))
                    # print("Heap total:", heap_total)
                    result_dict["memory"] = int(heap_total / 1024)
                else:
                    print("Heap total not found in the memusage output.")

                # result_dict["err_msg"] = result.stderr
                if process.returncode != 0:
                    result_dict["status"] = "RTE"
            except subprocess.TimeoutExpired:
                kill_child_processes(parent_pid)
                result_dict["status"] = "TLE"
            except subprocess.CalledProcessError as e:
                # Tangani kesalahan saat menjalankan program Python
                result_dict["status"] = str(e)

        # Tambahkan kondisi untuk bahasa lainnya sesuai kebutuhan
        
        execution_time = time.time() - start_time  # Waktu eksekusi dalam detik

        # Menghapus file sementara jika sudah selesai digunakan
        os.remove(file_name)

        result_dict["time"] = execution_time

        if process.returncode == 0:
            if result_dict["actual_output"].strip() == expected_output.strip():
                result_dict["status"] = "AC"
            else:
                result_dict["status"] = "WA"

        results.append(result_dict)

    # Mengembalikan hasil eksekusi
    return results

if __name__ == "__main__":
   uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


    

