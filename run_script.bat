cd C:\Users\Michal\Dropbox\Projects\broomstones-youtube
rem nothing really
call config.cmd
echo -%stream_title%-
echo C:\Users\Michal\youtube_api\Scripts\python.exe youtube-test.py --stream_title %stream_title% --sheet A --schedule_file schedule.json --obs_path "C:\Program Files\obs-studio\bin\64bit\obs64.exe" --club_calendar https://broomstones.com/index.php/events/club-calendar --debug__print_upcoming_calendar_types
C:\Users\Michal\youtube_api\Scripts\python.exe youtube-test.py --obs_path "C:\Program Files\obs-studio\bin\64bit\obs64.exe" --stop_obs
time /t
pause
