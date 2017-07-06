call python_venv\Scripts\activate.bat
pip3 install -r req.txt
:start_app
python sw_clicker.py
@REM TIMEOUT /T 5 /NOBREAK 
goto start_app