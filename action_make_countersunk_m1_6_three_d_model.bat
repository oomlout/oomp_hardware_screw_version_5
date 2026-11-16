@echo off
setlocal
pushd "%~dp0"
if errorlevel 1 exit /b 1
echo Rebuilding the six M1.6 Phillips countersunk models and studio renders.
echo Lengths: 3, 4, 5, 6, 8 and 10 mm. Existing outputs for these parts will be replaced.
python "%~dp0working_three_d_model.py" --filter "hardware_screw_countersunk_philips_black_m1_6_diameter_*" --ensure-metadata --update-presentation --force --jobs 1 %*
set "model_exit=%errorlevel%"
popd
if not "%model_exit%"=="0" echo 3D model generation failed. See the error above.
exit /b %model_exit%
