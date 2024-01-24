cd C:\Users\techn\Documents\streaming-scripting
call config.cmd

C:\Users\techn\Documents\streaming-scripting\youtube_api\Scripts\python.exe youtube-streaming.py   --stream_title %stream_title% --sheet %sheet_name% --obs_path "C:\Program Files\obs-studio\bin\64bit\obs64.exe" --schedule_file manual-schedule.json --club_calendar https://broomstones.com/index.php/events/club-calendar --debug__print_upcoming_calendar_types --broadcast_prefix Derby Presidents Regatta Griffin "Curling McCurlFace" "Chowder Bowl" "Loving Cup" Finlay

rem C:\Users\techn\Documents\streaming-scripting\youtube_api\Scripts\python.exe youtube-streaming.py  --stream_title %stream_title% --sheet %sheet_name% --obs_path "C:\Program Files\obs-studio\bin\64bit\obs64.exe" --club_calendar https://broomstones.com/index.php/events/club-calendar --debug__print_upcoming_calendar_types --broadcast_prefix Derby Presidents Regatta Griffin "Curling McCurlFace" "Chowder Bowl" "Loving Cup" Finlay
rem C:\Users\Michal\youtube_api\Scripts\python.exe youtube-test.py --stream_title %stream_title% --sheet A --schedule_file schedule.json --obs_path "C:\Program Files\obs-studio\bin\64bit\obs64.exe" --club_calendar https://broomstones.com/index.php/events/club-calendar --debug__print_upcoming_calendar_types
rem C:\Users\Michal\youtube_api\Scripts\python.exe youtube-test.py --obs_path "C:\Program Files\obs-studio\bin\64bit\obs64.exe" --stop_obs


time /t
pause



