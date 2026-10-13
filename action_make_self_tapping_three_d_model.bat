@echo off
setlocal
pushd "%~dp0"
if errorlevel 1 exit /b 1
echo Generating the 26 self-tapping models and studio renders.
echo Uses supplied dimensions and user-authorized visual estimates, fully threaded to the head.
python "%~dp0working_three_d_model.py" --filter "hardware_screw_self_tapping_philips_black_*" --ensure-metadata --update-presentation --jobs 1 %*
set "model_exit=%errorlevel%"
popd
if not "%model_exit%"=="0" echo 3D model generation failed. See the error above.
exit /b %model_exit%
