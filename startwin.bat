@echo off
TITLE Application de Gestion Patrimoniale

REM Vérifier si Python est installé
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python n'est pas installé. Veuillez l'installer avant de continuer.
    pause
    exit /b
)

REM Vérifier si les dépendances sont installées
python -c "import streamlit" >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Installation des dépendances...
    pip install -r requirements.txt
)

REM Vérifier si la configuration initiale a été effectuée
IF NOT EXIST "data\patrimoine.db" (
    echo Configuration initiale de l'application...
    python setup.py
)

REM Démarrer l'application
echo Démarrage de l'application...
streamlit run main.py