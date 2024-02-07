import os
import time
import uuid
from fastapi import FastAPI, HTTPException, Body, Request, Cookie
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from enum import Enum
from typing import List, Annotated, Union
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


class Language(str, Enum):
    cpp = "cpp"
    py = "py"

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
    avg_time: float


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

    for test_case in request.test_cases:
        input_data = test_case.get("input", "")
        expected_output = test_case.get("expected_output", "")
        session_id = str(uuid.uuid4())  # Menggunakan uuid sebagai session_id

        try:
            # Menjalankan source code dengan input tertentu
            result, execution_time = run_code(request.source_code, request.language_id, input_data, session_id)

            if result.returncode == 0:
                if result.stdout.strip() == expected_output.strip():
                    status = "Accepted"
                else:
                    status = "Wrong Answer"
            else:
                print(result.stdout)
                status = result.stderr

            results.append({
                "input": input_data,
                "expected_output": expected_output,
                "actual_output": result.stdout,
                "status": status,
                "time": execution_time
            })

        except Exception as e:
            execution_time = 0
            avg_time = 0
            results.append({
                "input": input_data,
                "expected_output": expected_output,
                "actual_output": f"Error: {str(e)}",
                "status": "Err",
                "time": execution_time
            })
            response_model = CodeExecutionResponse(identifier=request.identifier, source_code=request.source_code , language_id=request.language_id, results=results, avg_time=avg_time)
            return response_model
    
    total_time = 0
    for result in results:
        total_time += result["time"]
    avg_time = total_time/len(results)

    # Membuat instansiasi dari model CodeExecutionResponse
    response_model = CodeExecutionResponse(identifier=request.identifier, source_code=request.source_code , language_id=request.language_id, results=results, avg_time=avg_time)
    return response_model

def run_code(source_code, language_id, input_data, session_id):
    execution_time = 0

    # Menyimpan source code ke file sementara
    file_name = f"temp_{session_id}.{languages[language_id]}"
    with open(file_name, "w") as file:
        file.write(source_code)


    if languages[language_id] == "cpp" or languages[language_id] == "c":
        # Menjalankan kompilasi hanya jika belum pernah dikompilasi sebelumnya
        if not os.path.exists(f"temp_{session_id}"):
            compile_result = subprocess.run(["g++", file_name, "-o", f"temp_{session_id}"], capture_output=True)
            if compile_result.returncode != 0:
                # Jika gagal kompilasi
                # result = subprocess.CompletedProcess(args=[], returncode=-1, stderr=compile_result.stderr.decode("utf-8"))
                result = subprocess.CompletedProcess(args=[], returncode=-1, stderr="Compile Error")

                # Menghapus file sementara jika sudah selesai digunakan
                os.remove(file_name)

                # Mengembalikan hasil eksekusi
                return result, execution_time

    start_time = time.time()  # Waktu mulai eksekusi

    # Menjalankan source code dengan input tertentu menggunakan subprocess
    
    if languages[language_id] == "cpp" or languages[language_id] == "c":
        try:
            result = subprocess.run([f"./temp_{session_id}"], input=input_data, text=True, capture_output=True, timeout=5)  # Ganti 5 dengan batas waktu yang diinginkan (dalam detik)
            if result.stderr:
                result.stderr="Runtime Exception"
            # Menghapus file compiled jika sudah selesai digunakan
            os.remove(f"temp_{session_id}")
        except subprocess.TimeoutExpired:
            os.remove(f"temp_{session_id}")
            result = subprocess.CompletedProcess(args=[], returncode=-1, stderr="Time Limit Exceeded")
        except subprocess.CalledProcessError as e:
            # Tangani kesalahan saat menjalankan program C++ yang dikompilasi
            result = subprocess.CompletedProcess(args=e.cmd, returncode=e.returncode, stderr=e.stderr)
    elif languages[language_id] == "py":
        try:
            result = subprocess.run(["python", file_name], input=input_data, text=True, capture_output=True, timeout=5)  # Ganti 5 dengan batas waktu yang diinginkan (dalam detik)
            
            if result.stderr:
                result.stderr="Runtime Exception"
        except subprocess.TimeoutExpired:
            result = subprocess.CompletedProcess(args=[], returncode=-1, stderr="Time Limit Exceeded")
        except subprocess.CalledProcessError as e:
            # Tangani kesalahan saat menjalankan program Python
            result = subprocess.CompletedProcess(args=e.cmd, returncode=e.returncode, stderr=e.stderr)

    # Tambahkan kondisi untuk bahasa lainnya sesuai kebutuhan
    
    execution_time = time.time() - start_time  # Waktu eksekusi dalam detik

    # Menghapus file sementara jika sudah selesai digunakan
    os.remove(file_name)

    # Mengembalikan hasil eksekusi
    return result, execution_time




    

