@echo off
setlocal
pushd "%~dp0"
if errorlevel 1 exit /b 1
echo Generating models, studio isometric renders, side product renders and SVG views.
echo Includes all ready screw families, including the 61 modern wood screws.
echo Existing renders are preserved. Pass --force to rebuild them.
echo Blender Cycles will run in the background. Outputs go in each part's three_d_model folder.
python "%~dp0working_three_d_model.py" --filter "*" --jobs 1 --ensure-metadata --update-presentation %*
set "model_exit=%errorlevel%"
popd
if not "%model_exit%"=="0" echo 3D model generation failed. See the error above.
exit /b %model_exit%
