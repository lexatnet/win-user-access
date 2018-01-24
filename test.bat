@echo off
rem for /F "tokens=1,2 delims=-" %%a in (allowed.txt) do (
rem 	call :test %%a %%b
rem )




rem for %%a in ("12-23 34-45 56-67") do (
rem 	for /f "delims=- tokens=1,2" %%a in ("%%a") do (
rem 		echo a=%%a b=%%b
rem 	)
rem )
setlocal
call :get_cur_day_of_week
echo dayofweek=%day-of-week%
endlocal
exit


:get_cur_day_of_week
for /f %%a in ('wmic path win32_localtime get dayofweek /format:list ^| findstr "DayOfWeek="') do (
	call :set_cur_day_of_week %%a
)
exit /b

:set_cur_day_of_week
if not "%1"=="" (
    if "%1"=="DayOfWeek" (
		set day-of-week=%2
        shift
    )
    shift
    goto set_cur_day_of_week
)
exit /b

rem :get_day_of_week
rem for /f "skip=1" %%a in ('wmic path win32_localtime get dayofweek') do (
rem  	set day-of-week=%%a
rem 	exit /b
rem )
rem exit /b

rem :test
rem 	set min_time=%1
rem 	set max_time=%2
rem 	
rem 	echo min_time %min_time%
rem 	echo maxtime %max_time%
	
rem 	exit /b
	
