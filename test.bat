rem for /F "tokens=1,2 delims=-" %%a in (allowed.txt) do (
rem 	call :test %%a %%b
rem )

rem :get_day_of_week
rem for /f %%a in ('wmic path win32_localtime get dayofweek /format:list ^| findstr "="') do (
rem 	set %%a
rem )


for %%a in ("12-23 34-45 56-67") do (
	for /f "delims=- tokens=1,2" %%a in ("%%a") do (
		echo a=%%a b=%%b
	)
)

echo dayofweek=%dayofweek%
exit

:test
	set min_time=%1
	set max_time=%2
	
	echo min_time %min_time%
	echo maxtime %max_time%
	
	exit /b
	
