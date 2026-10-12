@echo off
setlocal
pushd "%~dp0"
if errorlevel 1 exit /b 1
python "%~dp0working_three_d_model.py" --ensure-metadata --check %*
set "model_exit=%errorlevel%"
popd
exit /b %model_exit%
