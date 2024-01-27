from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from enum import Enum
from typing import List, Annotated
import subprocess
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/editor", StaticFiles(directory="static",html = True), name="static")

class Language(str, Enum):
    cpp = "cpp"
    py = "py"

class CodeExecutionRequest(BaseModel):
    source_code: str
    language: str
    test_cases: List[dict]


class CodeExecutionResponse(BaseModel):
    results: List[dict]


@app.post("/api/submission")
async def execute_code(
    request: Annotated[
        CodeExecutionRequest,
        Body(
            openapi_examples={
                "py": {
                    "summary": "Python",
                    "description": "",
                    "value": {
                        "source_code": "def add(a, b):\n    return a + b\n\na = int(input())\nb = int(input())\nprint(add(a,b))",
                        "language": "py",
                        "test_cases": [
                            {
                            "input": "2\n3\n",
                            "output": "5\n"
                            },
                            {
                            "input": "5\n3\n",
                            "output": "12\n"
                            }
                        ],
                    },
                },
                "cpp": {
                    "summary": "C/C++",
                    "description": "",
                    "value": {
                        "source_code": "#include <iostream>\nusing namespace std;\nint main() {\n    int a, b;\n    cin >> a >> b;\n    cout << a + b << endl;\n    return 0;\n}",
                        "language": "cpp",
                        "test_cases": [
                            {
                            "input": "2 3\n",
                            "output": "5\n"
                            },
                            {
                            "input": "5 7\n",
                            "output": "12\n"
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
        expected_output = test_case.get("output", "")
        
        try:
            # Menjalankan source code dengan input tertentu
            result = run_code(request.source_code, request.language, input_data)
            
            # Membandingkan hasil dengan output yang diharapkan
            is_passed = result.strip() == expected_output.strip()
            
            results.append({
                "input": input_data,
                "expected_output": expected_output,
                "actual_output": result,
                "is_passed": is_passed
            })
            
        except Exception as e:
            results.append({
                "input": input_data,
                "expected_output": expected_output,
                "actual_output": f"Error: {str(e)}",
                "is_passed": False
            })

    return results

def run_code(source_code, language, input_data):
    # Menyimpan source code ke file sementara
    file_name = "temp_code_executable." +  language
    with open(file_name, "w") as file:
        file.write(source_code)

    # Menjalankan source code dengan input tertentu menggunakan subprocess
    if language == "cpp":
        result = subprocess.run(["g++", file_name, "-o", "temp_code_executable"], capture_output=True)
        if result.returncode == 0:
            result = subprocess.run(["./temp_code_executable"], input=input_data, text=True, capture_output=True)
        else:
            raise Exception(result.stderr)
    elif language == "py":
        result = subprocess.run(["python", file_name], input=input_data, text=True, capture_output=True)
    # Tambahkan kondisi untuk bahasa lainnya sesuai kebutuhan

    # Menghapus file sementara
    subprocess.run(["rm", file_name, "temp_code_executable"])

    # Mengembalikan hasil eksekusi
    if result.returncode == 0:
        return result.stdout
    else:
        raise Exception(result.stderr)

