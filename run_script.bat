cd C:\Users\techn\Documents\streaming-scripting
call config.cmd




C:\Users\techn\Documents\streaming-scripting\youtube_api\Scripts\python.exe youtube-streaming.py --yt_oauth_client_secret %secret_filename%  --stream_title %stream_title% --sheet %sheet_name% --obs_path "C:\Program Files\obs-studio\bin\64bit\obs64.exe" --schedule_file manual-schedule.json --club_calendar https://broomstones.com/index.php/calendar/ice-calendar  --ical_addr "%ical_url%" --ical_sheet_name "%ical_sheet_name%" --debug__print_upcoming_calendar_types --epilogue_minutes 8 --prologue_minutes 12 --broadcast_prefix Derby Presidents Regatta Griffin "Curling McCurlFace" "Chowder Bowl" "Loving Cup" Finlay "Mixed Doubles -" "Saturday Pickup"

rem C:\Users\techn\Documents\streaming-scripting\youtube_api\Scripts\python.exe youtube-streaming.py  --stream_title %stream_title% --sheet %sheet_name% --obs_path "C:\Program Files\obs-studio\bin\64bit\obs64.exe" --club_calendar https://broomstones.com/index.php/events/club-calendar --debug__print_upcoming_calendar_types --broadcast_prefix Derby Presidents Regatta Griffin "Curling McCurlFace" "Chowder Bowl" "Loving Cup" Finlay
rem C:\Users\Michal\youtube_api\Scripts\python.exe youtube-streaming.py --yt_oauth_client_secret %secret_filename%  --stream_title %stream_title% --sheet %sheet_name% --obs_path "C:\Program Files\obs-studio\bin\64bit\obs64.exe" --schedule_file manual-schedule.json --club_calendar https://broomstones.com/index.php/calendar/ice-calendar --debug__print_upcoming_calendar_types --epilogue_minutes 3 --prologue_minutes 3 --broadcast_prefix Derby Presidents Regatta Griffin "Curling McCurlFace" "Chowder Bowl" "Loving Cup" Finlay "Mixed Doubles" "Saturday Pickup"


time /t
pause


