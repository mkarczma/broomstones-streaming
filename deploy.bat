cd C:\Users\techn\Documents\streaming-scripting

echo Downloading deploy script from github
curl https://raw.githubusercontent.com/mkarczma/broomstones-streaming/main/deploy_script.cmd -o deploy_script.cmd

echo Running deploy script
call deploy_script.cmd

time /t
pause



