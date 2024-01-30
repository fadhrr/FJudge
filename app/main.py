import os
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from enum import Enum
from typing import List, Annotated
import subprocess
from fastapi.staticfiles import StaticFiles
import uvicorn
from dotenv import load_dotenv
from app.judger import run_code

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory='templates')
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get('/', response_class=HTMLResponse)
def main(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "base_url": str(request.url)})


class Language(str, Enum):
    cpp = "cpp"
    py = "py"

class CodeExecutionRequest(BaseModel):
    source_code: str
    language: str
    test_cases: List[dict]


class CodeExecutionResponse(BaseModel):
    results: List[dict]


@app.post("/api/judge")
async def judge(
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


