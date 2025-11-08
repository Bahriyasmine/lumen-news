@echo off
echo ========================================
echo Lumen News - Docker Setup
echo ========================================
echo.

docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed!
    pause
    exit /b 1
)

docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running!
    pause
    exit /b 1
)

if not exist .env (
    (
        echo SECRET_KEY=dev-secret-key-change-in-production
        echo DEBUG=True
        echo ALLOWED_HOSTS=localhost,127.0.0.1
        echo DB_NAME=lumen_news
        echo DB_USER=postgres
        echo DB_PASSWORD=postgres
        echo DB_HOST=db
        echo DB_PORT=5432
        echo REDIS_URL=redis://redis:6379/0
        echo CELERY_BROKER_URL=redis://redis:6379/0
        echo CELERY_RESULT_BACKEND=redis://redis:6379/0
        echo GROQ_API_KEY=your-groq-api-key-here
    ) > .env
    echo .env created! Update GROQ_API_KEY before running!
    pause
)

docker-compose build
docker-compose up -d db redis
docker-compose run --rm web python -m spacy download en_core_web_sm
timeout /t 10 /nobreak >nul
@REM docker-compose run --rm web python manage.py migrate
@REM docker-compose run --rm web python manage.py createsuperuser

echo Setup complete! Run run.bat to start.
pause
