cd C:\Users\techn\Documents\streaming-scripting
call config.cmd

C:\Users\techn\Documents\streaming-scripting\youtube_api\Scripts\python.exe youtube-streaming.py   --stream_title %stream_title% --sheet %sheet_name% --club_calendar https://broomstones.com/index.php/events/club-calendar --schedule_file manual_schedule.json --only_check_schedule

time /t
pause



