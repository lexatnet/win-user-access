call :get_cur_date
call :analyze_config allowed.txt

:analyze_config
set config=%1

echo analizing %config%

for /f %%a in (%config%) do (
	setlocal
	call :read_config_from_string %%a
	if not defined day-of-week (
		if not defined day-of-week-range (
			echo day of week rule skeeped
		) else (
			for /f "delims=- tokens=1,2" %%a in ( %day-of-week-range% ) do (
				call :check_day_of_week_in_range %cur_day_of_week%  %%a %%b
			)
		)
	) else (
		call :check_day_of_week_in_range %cur_day_of_week%  %day-of-week% %day-of-week%
	)
	call :check_date_in_range %cur_date% %%a %%b %%c
	
	call :check_time_in_range %cur_time% %%a %%b %%c
	endlocal
)
goto shutdown








:check_day_of_week_in_range
set check_day_of_week=%1

set min_day_of_week=%2

set max_day_of_week=%3

:greater_then_min_day_of_week_check
if %check_day_of_week% geq %min_day_of_week% (
	if %check_day_of_week% leq %max_day_of_week% (
		exit /b
	)
)
goto shutdown





:check_date_in_range
set check_date=%1
set check_date_dd=%check_date:~0,2%
set check_date_mm=%check_date:~3,2%
set check_date_yyyy=%check_date:~5,2%

set min_date=%2
set min_date_dd=%min_date:~0,2%
set min_date_mm=%min_date:~3,2%
set min_date_yyyy=%min_date:~5,2%

set max_date=%3
set max_date_dd=%max_date:~0,2%
set max_date_mm=%max_date:~3,2%
set max_date_yyyy=%max_date:~5,2%

:greater_then_min_date_check
if %check_date_yyyy%%check_date_mm%%check_date_dd% geq %min_date_yyyy%%min_date_mm%%min_date_dd% (
	if %check_date_yyyy%%check_date_mm%%check_date_dd% leq %max_date_yyyy%%max_date_mm%%max_date_dd% (
		exit /b
	)
)
goto shutdown






	

:check_time_in_range
set check_time=%1
set check_time_hh=%check_time:~0,2%
set check_time_mm=%check_time:~3,2%

set min_time=%2
set min_time_hh=%min_time:~0,2%
set min_time_mm=%min_time:~3,2%


set max_time=%3
set max_time_hh=%max_time:~0,2%
set max_time_mm=%max_time:~3,2%

if %check_time_hh%%check_time_mm% geq %min_time_hh%%min_time_mm% (
	if %check_time_hh%%check_time_mm% leq %max_time_hh%%max_time_mm% (
		exit /b
	)
)
goto shutdown








:get_cur_day_of_week
for /f %%a in ('wmic path win32_localtime get dayofweek /format:list ^| findstr "="') do (
	set %%a
)
exit /b

:get_cur_date
set cur_date=%date%
exit /b

:read_config_from_string
set string=%1
for %%a in (%string%) do (
	echo %%a
	set %%a
)
exit /b






:shutdown
echo shutdown
rem shutdown -l -f
exit 

:defered_shutdown
echo defered shutdown
rem at %max_time% shutdown -l -f
exit


:get_cur_time 
set cur_time=%time%
exit /b




@ECHO OFF

SET man1=%1
SET man2=%2
SHIFT & SHIFT

:read_arg
IF NOT "%1"=="" (
    IF "%1"=="-username" (
        SET user=%2
        SHIFT
    )
    IF "%1"=="-otheroption" (
        SET other=%2
        SHIFT
    )
    SHIFT
    GOTO read_arg
)

ECHO Man1 = %man1%
ECHO Man2 = %man2%
ECHO Username = %user%
ECHO Other option = %other%

REM ...do stuff here...
