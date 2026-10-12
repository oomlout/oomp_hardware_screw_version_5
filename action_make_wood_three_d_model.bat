@echo off
setlocal
pushd "%~dp0"
if errorlevel 1 exit /b 1
echo Generating 61 modern chipboard-style wood screw visualizations.
echo Every screw retains a plain section below the head. These are sourced similar-product models.
echo Existing verified renders are preserved. Pass --force to rebuild them.
python "%~dp0working_three_d_model.py" --filter "hardware_screw_wood_*" --ensure-metadata --update-presentation --jobs 1 %*
set "model_exit=%errorlevel%"
popd
exit /b %model_exit%
