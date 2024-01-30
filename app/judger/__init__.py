
import subprocess


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
    
