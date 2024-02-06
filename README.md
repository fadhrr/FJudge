### FJudge

#### Introduction
FJudge is an easy-to-use judge system with FastAPI technology for competitive programming. 

#### Clone Repository
```bash
git clone https://github.com/fadhrr/FJudge.git
cd FJudge
```

### Running FJudge Without Docker
To run FJudge without Docker, you need to follow these steps:

#### Prerequisites
- Make sure Python is installed on your system.

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Replace `8000` with the desired port.

3. **Access Application:**
   Open a web browser and access `http://localhost:8000` or the port you have specified.

4. **Stop the Application:**
   Press `Ctrl + C` in the terminal to stop the application.


### Running FJudge With Docker
To run FJudge without Docker, you need to follow these steps:

#### Build Docker Image
```bash
docker-compose build
```

#### Run Docker Container
- Customize port in `docker-compose.yml` if needed(Default is `8008`).
- Run the container:
  ```bash
  docker-compose up -d
  ```
- Access the application at `http://localhost:8008`.

#### Stop Docker Container
```bash
docker-compose down
```

#### Default Endpoints

- **Docs (Swagger UI):**
  - URL: `http://localhost:8008/docs`
  - Description: FastAPI documentation with Swagger UI.

- **Redoc:**
  - URL: `http://localhost:8008/redoc`
  - Description: FastAPI documentation with ReDoc.

- **FJudge Editor:**
  - URL: `http://localhost:8008/`
  - Description: FJudge code editor.


#### Notes
- Ensure Docker and Docker Compose are installed.
- Modify the `docker-compose.yml` file for custom configurations.
- Customize the port in both `docker-compose.yml` and during the container run.
- Save changes to `docker-compose.yml` before running the container.
- Adjust the provided examples in the API documentation according to your needs.
