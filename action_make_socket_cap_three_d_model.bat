@echo off
setlocal
pushd "%~dp0"
if errorlevel 1 exit /b 1
echo Generating ISO 4762 socket caps with full and display solids and both studio poses.
python "%~dp0working_three_d_model.py" --filter "hardware_screw_socket_cap_hex_head_*" --ensure-metadata --update-presentation --jobs 1 %*
set "model_exit=%errorlevel%"
popd
exit /b %model_exit%
