import os.path
import datetime
import argparse
import json
import pprint
import time
import subprocess
import wmi
import io
import requests
import math

import urllib.request
import icalendar

from googleapiclient.discovery import build

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


token_filename='ggl_oauth_token.json'
secrets_filename='client_secret_846837736816-gh4fg7fvng3g9i9e46qrprtnrmtk0l57.apps.googleusercontent.com.json'

SCOPES = [ 'https://www.googleapis.com/auth/youtube' ]

parser = argparse.ArgumentParser(description='YouTube interface')
parser.add_argument('--sid', help='stream ID to manipulate')
parser.add_argument('--bid', help='broadcast ID to manipulate')
parser.add_argument('--stream_title', help='stream title to manipulate')
parser.add_argument('--delete', action='store_true')
parser.add_argument('--list', action='store_true')
parser.add_argument('--list_active', action='store_true')
parser.add_argument('--list_upcoming', action='store_true')
parser.add_argument('--list_completed', action='store_true')
parser.add_argument('--schedule_now', action='store_true')
parser.add_argument('--bind', action='store_true')
parser.add_argument('--status', action='store_true')
parser.add_argument('--config', help="")
parser.add_argument('--transition', help="set status of broadcast to one of allowed values: statusUnspecified, testing, live, complete")
parser.add_argument('--schedule_file', help='the schedule file to use and take immediate actions')
parser.add_argument('--sheet', help='the ice sheet for the stream')
parser.add_argument('--print_schedule', action='store_true')
parser.add_argument('--start_obs', action='store_true')
parser.add_argument('--stop_obs', action='store_true')
parser.add_argument('--always_auto_stop_obs', action='store_true')
parser.add_argument('--obs_path')
parser.add_argument('--club_calendar')
parser.add_argument('--debug__print_upcoming_calendar_types', action='store_true')
parser.add_argument('--broadcast_prefix', action='append', nargs='+')
parser.add_argument('--override_time')
parser.add_argument('--only_check_schedule', action='store_true')
parser.add_argument('--yt_oauth_client_secret', help='YouTube OAuth Client Secret JSON')
parser.add_argument('--prologue_minutes', default=5, type=int)
parser.add_argument('--epilogue_minutes', default=5, type=int)
parser.add_argument('--ical_addr', help='"Secret address in iCal format" from specific Calendar Settings')
parser.add_argument('--ical_sheet_name', help='Sheet string name in iCal - must be in LOCATION field')


args = parser.parse_args()



args_broadcast_prefixes = []
if args.broadcast_prefix: args_broadcast_prefixes = args.broadcast_prefix
broadcast_prefixes = []
for l in args_broadcast_prefixes:
    for p in l:
        broadcast_prefixes.append(p)


if args.yt_oauth_client_secret:
    secrets_filename = args.yt_oauth_client_secret

prologue_time = datetime.timedelta(minutes=args.prologue_minutes)
epilogue_time = datetime.timedelta(minutes=args.epilogue_minutes)
diff_10minutes = datetime.timedelta(minutes=10)
diff_1minute = datetime.timedelta(minutes=1)


real_start_time = None
def get_now():
    global local_tz
    global now
    global today
    global today_weekday
    local_tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    now = datetime.datetime.now().replace(tzinfo=local_tz)

    if args.override_time:
        global real_start_time
        if real_start_time is None:
            real_start_time = now
            now = datetime.datetime.fromisoformat(args.override_time)
        else:
            time_since_start = now - real_start_time
            now = datetime.datetime.fromisoformat(args.override_time) + time_since_start

    today = now.date()
    today_weekday = today.weekday()

    print("Time now is %s" % now)

get_now()

calendar_sched = [ ]
if args.club_calendar:
    cal_lines = []
    if args.club_calendar.startswith("http://") or args.club_calendar.startswith("https://"):
        print("downloading calendar from %s" % args.club_calendar)
        u = requests.get(args.club_calendar, stream=True)
        f = io.BytesIO()
        f.write(u.content)
        f.seek(0)

        cal_lines = f.readlines()
        for n in range(len(cal_lines)):
            cal_lines[n] = cal_lines[n].decode()
        print("downloaded %d lines" % len(cal_lines))

    else:
        with open(args.club_calendar) as cal_data:
            cal_lines = cal_data.readlines()

    events = json.loads('[ ]')
    add_events = [ ]
    resources = { }

    for line in cal_lines:
        l = line.strip()

        if l.startswith("resources: ") :
            print(l)
            resources_line = l[11:][:-1]
            resoures_list = json.loads(resources_line)
            for r in resoures_list:
                resources[r["id"]] = r["title"]
            print ("resources dictionary: %s" % resources)
        if l.startswith("////initialEvents: ") :
            print("events before stripping: " + l[:30] + " === " + l[-30:])
            events_line = l[:-1][19:]
            print("events after stripping: " + events_line[:30] + " === " + events_line[-30:])
            events = json.loads(events_line)
            print("first event: %s" % events[0])
        if l.startswith("cal.addEvent(") :
            add_event_json = '['  + l[:-2][13:] + ']'
            if len(add_events) == 0:
                print ("first add_event: " + l)
                print ("first add_event in json: " + add_event_json)            
            add_events.append(json.loads(add_event_json))


    print('done parsing calendar. add_events = %d events = %d' % (len(add_events), len(events)))

    tomorrow = now + datetime.timedelta(days=7)

    trimmed_events = [ ]
    trimmed_add_events = [ ]

    for e in add_events:
        try:
            start = datetime.datetime.fromisoformat(e[3])
            end = datetime.datetime.fromisoformat(e[4])

            if start > tomorrow or end < now : continue

            # we want to include this event
            trimmed_add_events.append(e)
        except Exception as err:
            print("caught an error %s while processing add_event %s" % (err, e))


    for e in events:
        try:
            start = datetime.datetime.fromisoformat(e['start'])
            end = datetime.datetime.fromisoformat(e['end'])

            if start > tomorrow or end < now : continue

            # we want to include this event
            trimmed_events.append(e)

        except Exception as err:
            print("caught an error %s while processing event %s" % (err, e))


    print('done parsing calendar. for next 24h: add_events = %d events = %d' % (len(trimmed_add_events), len(trimmed_events)))


    wanted_types = { "7" : "Pickup", "3" : "Leagues", "5" : "Spiels" }
    print(wanted_types)

    if args.debug__print_upcoming_calendar_types:
        printed_types = { }
        for n in range(len(trimmed_events)):
            e = trimmed_events[n]
            t = e['extendedProps']['type']
            if t in printed_types : continue
            print('type %s: %s %s' % (t, t in wanted_types, trimmed_add_events[n]))
            printed_types[t] = 0

    for n in range(len(trimmed_events)):
        e = trimmed_events[n]
        t = e['extendedProps']['type']

        include_this_event = t in wanted_types

        if include_this_event and broadcast_prefixes:
            include_this_event = False

            for p in broadcast_prefixes:
                if trimmed_add_events[n][0].startswith(p):
                    include_this_event = True
                    break

        if include_this_event :
            print("-%s- %s %s : %s" % (resources[e['resourceId']], e['start'], e['extendedProps']['type'], trimmed_add_events[n][0]))
            if resources[e['resourceId']] == args.sheet :
                start = datetime.datetime.fromisoformat(e['start'])
                end = datetime.datetime.fromisoformat(e['end'])
                event_duration = end-start
                event_duration_in_minutes = math.ceil(event_duration.total_seconds() / 60)
                game_name = trimmed_add_events[n][0].split(' - ')[0]
                title = "%s - %s, %s" % (game_name, start.strftime("%b %d, %Y %#I:%M %p"), resources[e['resourceId']])
                calendar_sched.append( { 'title' : title, 'when' : e['start'], 'duration_minutes' : event_duration_in_minutes } )
                print('added %s' % calendar_sched[-1]['title'])





if args.ical_addr:
    try:
        ical_sheet_name = args.ical_sheet_name
        print("gcal:", args.ical_addr, " sheet name: ", ical_sheet_name)
        if not ical_sheet_name:
            print("ERROR: if --ical_addr is given, --ical_sheet_name must also be present")
            quit()
        response = urllib.request.urlopen(args.ical_addr)
        ical = response.read().decode('utf-8')
        gcal = icalendar.Calendar.from_ical(ical)
        for event in gcal.walk('VEVENT'):
            if "DTSTART" not in event : continue
            if "SUMMARY" not in event : continue
            if "DTEND" not in event : continue
            if "LOCATION" not in event : continue

            start_time = event["DTSTART"].dt
            end_time = event["DTEND"].dt
            duration_minutes = math.ceil((end_time - start_time).total_seconds() / 60)
            title = event["SUMMARY"].to_ical().decode()
            location = event["LOCATION"].to_ical().decode()

            if ical_sheet_name not in location : continue

            if isinstance(start_time, datetime.datetime):
                if start_time + datetime.timedelta(days=1) > now and end_time < now + datetime.timedelta(days=1):

                    calendar_sched.append( { 'title' : title, 'when' : datetime.datetime.fromisoformat(start_time.isoformat()).astimezone(local_tz).isoformat(), 'duration_minutes' : duration_minutes } )
                    print('added %s' % calendar_sched[-1]['title'])
    except Exception as err:
        print("ERROR %s while reading or parsing ical %s" % (err, args.ical_addr))
        if args.only_check_schedule : quit()


obs_exe = r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"
if args.obs_path : obs_exe = args.obs_path
obs_process = None

def find_process(path=obs_exe):
    assert path
    pname = os.path.basename(path)
    for process in wmi.WMI().Win32_Process():
        if process.name == pname:
            return process
    return None


def start_obs():
    if find_process(obs_exe) is None:
        obs_args = [ obs_exe, "--startstreaming", "--disable-shutdown-check" ]
        obs_dir = os.path.dirname(obs_exe)
        print("Starting OBS and streaming - this will take about 10 seconds")

        obs_process = subprocess.Popen(obs_args, cwd = obs_dir)

        time.sleep(10)
    else:
        print("OBS is already running!")

def stop_obs():
    obs_process = find_process(obs_exe)
    if obs_process:
        print("Stopping OBS")
        obs_process.Terminate()
    else:
        print("OBS is alrady not running!")

if args.start_obs:
    start_obs()

if args.stop_obs:
    stop_obs()


#define an empty schedule
schedule = { "weekly" : [ ], "individual" : [ ] }

if args.schedule_file is not None:
    try:
        with open(args.schedule_file) as json_data:
            file_schedule = json.load(json_data)
            json_data.close()

            if "individual" not in file_schedule : file_schedule["individual"] = [ ]
            if "weekly" not in file_schedule : file_schedule["weekly"] = [ ]

            # copy the schedule over
            schedule = file_schedule
    except Exception as err:
        print("error while reading schedule file:", err)
        if args.only_check_schedule : quit()


# add the schedule from the calendar
schedule ['individual'] = schedule ['individual'] + calendar_sched

# within the schedule, find the entry that is *ending* soonest

class ScheduledStream:

    def __init__(self, start, end, title):
        self.start = start
        self.end = end
        self.title = title

    def __str__(self):
        return '{ title: "' + self.title + '", start: ' + str(self.start) + ', end: ' + str(self.end) + ' }'

schedule_list = [ ]


# first go through the "weekly" entries
for s in schedule['weekly']:
    try:
        if "disabled" in s and s["disabled"] == True: continue
        if "weekday" not in s :
            raise Exception ("no 'weekday' in %s" % str(s))
        s_weekday = s['weekday']
        if s_weekday == "Monday" : wd = 0
        elif s_weekday == "Tuesday" : wd = 1
        elif s_weekday == "Wednesday" : wd = 2
        elif s_weekday == "Thursday" : wd = 3
        elif s_weekday == "Friday" : wd = 4
        elif s_weekday == "Saturday" : wd = 5
        elif s_weekday == "Sunday" : wd = 6
        else:
            raise Exception ("invalid weekday in %s" % str(s))
        diff_days = (7 + today_weekday - wd) % 7
        s_date = today + datetime.timedelta(days=diff_days  )
        #print("days_diff %d date %s" % (diff_days, s_date.isoformat()))

        if "when" not in s :
            raise Exception ("no 'when' in %s" % str(s))
        start_str = s_date.isoformat() + " " + s['when']
        start = datetime.datetime.fromisoformat(start_str).replace(tzinfo=local_tz)
        if "duration_minutes" not in s :
            raise Exception ("no 'duration_minutes' in %s" % str(s))
        duration = s['duration_minutes']
        end = start + datetime.timedelta(minutes=duration)

        if "title" not in s :
            raise Exception ("no 'title' in %s" % str(s))
        schedule_list.append(ScheduledStream(start=start, end=end, title=s['title']))
    except Exception as err:
        print("ERROR %s while reading weekly schedule entry: %s" % ( err, str(s) ))
        if args.only_check_schedule : quit()

# now go through the "individual" entries
for s in schedule['individual']:
    try:
        if "when" not in s :
            raise Exception ("no 'when' in %s" % str(s))
        start_str = s['when']
        start = datetime.datetime.fromisoformat(start_str).replace(tzinfo=local_tz)
        if "duration_minutes" not in s :
            raise Exception ("no 'duration_minutes' in %s" % str(s))
        duration = s['duration_minutes']
        end = start + datetime.timedelta(minutes=duration)

        if "title" not in s :
            raise Exception ("no 'title' in %s" % str(s))
        schedule_list.append(ScheduledStream(start=start, end=end, title=s['title']))
    except Exception as err:
        print("ERROR %s while reading individual schedule entry: %s" % ( err, str(s) ))
        if args.only_check_schedule : quit()

# update the title
for s in schedule_list:
    if args.sheet:
        s.title = s.title.replace("%SHEET%", args.sheet)
    s.title = s.title.replace("%DATE%", s.start.strftime("%b %d, %Y"))
    s.title = s.title.replace("%DATETIME%", s.start.strftime("%b %d, %Y %I:%M %p"))

sched_string = ""
for s in schedule_list: sched_string = sched_string + " " + str(s)
print("schedule list: %s" % sched_string)

if args.only_check_schedule : quit()

# build a list of streams that should either be active right now
# of should go active in the next 10 minutes
upcoming_list = []
active_list = []
for s in schedule_list:

    if args.print_schedule:
        print('"%s" %s to %s' % ( s.title, s.start, s.end))

    # first the currently active
    if (s.start - prologue_time <= now) and (s.end + epilogue_time >= now):
        active_list.append(s)
    # now the soon-to-start
    elif s.start > now and s.start - prologue_time - diff_10minutes <= now:
        upcoming_list.append(s)


sched_string = ""
for s in active_list: sched_string = sched_string + " " + str(s)
print("active list: %s" % sched_string)
sched_string = ""
for s in upcoming_list: sched_string = sched_string + " " + str(s)
print("upcoming list: %s" % sched_string)



sid=args.sid
bid=args.bid

print("starting authentication")
ggl_creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authoriggl_credszation flow completes for the first
# time.
if os.path.exists(token_filename):
    print ("getting credentials from token filename %s" % token_filename)
    ggl_creds = Credentials.from_authorized_user_file(token_filename, SCOPES)

# If there are no (valid) credentials available, let the user log in.
if not ggl_creds or not ggl_creds.valid:
    print ("creds not valid")
    if ggl_creds and ggl_creds.expired and ggl_creds.refresh_token:
        print ("creds expired")
        ggl_creds.refresh(Request())
    else:
        print ("making flow")
        flow = InstalledAppFlow.from_client_secrets_file(secrets_filename, SCOPES)
        print ("getting creds from local server")
        ggl_creds = flow.run_local_server(port=8080, prompt="consent") # prompt like this causes to always get a refresh token
    # Save the credentials for the next run
    with open(token_filename, 'w') as token:
        print ("writing creds to json")
        token.write(ggl_creds.to_json())
print("authentication done")


yt = build('youtube', 'v3',  credentials=ggl_creds)
ls = yt.liveStreams()
br = yt.liveBroadcasts()



def list_yt_streams():

    global yt_streams_list
    global yt_streams

    yt_streams_list = []
    yt_streams = { }

    # get my livestreams
    rq = ls.list(part="id,status,snippet,cdn", mine=True)

    while True:
        response = rq.execute()
        items = response.get("items")
        yt_streams_list = yt_streams_list + items
        if "nextPageToken" not in response: break

        rq = ls.list_next(previous_request=rq, previous_response=response)
        response = rq.execute

    for s in yt_streams_list:
        yt_streams[s['id']] = s

    print("found %d streams" % len(yt_streams_list))
    if args.list: print(yt_streams_list)

if args.list or args.stream_title is not None or args.schedule_file is not None or args.club_calendar is not None:
    list_yt_streams()

# find the particular stream I'm interested in
if args.stream_title is not None:
    assert sid is None
    for s in yt_streams_list:
        name = s.get('snippet')['title']
        if name == args.stream_title:
            sid = s.get('id')
            break

    if sid is None:
        print("unable to find stream_title=`%s` in yt_streams_list=%s" % (args.stream_title, yt_streams_list))
        quit(255)

    print ('stream "' + args.stream_title + '" has ID ' + sid)


# if requested, we can immediately insert a broadcast

def schedule_broadcast(title, start, end):
    print("scheduling broadcast: " + title)
    rq = br.insert(part="id, snippet, contentDetails,status",
        body = {
            "contentDetails" : {
                #"boundStreamId" : sid, # livestream ID, not key
                #"enableAutoStart" : True,
                "enableAutoStop" : True,
            },
            "snippet" : {
                "title" : title,
                "scheduledStartTime" : start.isoformat(),
                "scheduledEndTime" : end.isoformat(),
            },
            "status" : {
                "privacyStatus" : "public",
                "selfDeclaredMadeForKids" : False
            }
        }
    )
    response = rq.execute()
    print ("Inserted broadcast ID " + response["id"])

    return response


if args.schedule_now:
    assert bid is None
    response = schedule_broadcast("try " + now.isoformat(), now, now + datetime.timedelta(minutes=10))
    print(response)
    bid = response["id"]

def bind_broadcast(bid, sid):
    assert bid is not None
    assert sid is not None

    print ("Binding stream " + sid + " to broadcast " + bid)

    rq = br.bind(id=bid, streamId=sid, part="id,snippet,contentDetails,status")
    response = rq.execute()
    return response

if args.bind:
    bind_broadcast(bid, sid)

def transition_broadcast(bid, target_status):
    assert bid is not None
    assert target_status is not None
    rq = br.transition(broadcastStatus=target_status, id=bid, part="id, snippet, status")
    response = rq.execute()
    return response['status']['lifeCycleStatus']


if args.transition:
    print("transitioning bid %s to %s" % (bid, args.transition))
    transition_broadcast(bid, args.transition)


def delete_broadcast(bid=None):
    print("deleting. bid=%s" % ( bid ))

    rq = br.delete(id=bid)
    response = rq.execute()


if args.delete:
    delete_broadcast(bid=bid)


def yt_broadcast_complete(b): 
    if 'scheduledStartTime' not in b['snippet']: return False
    if 'scheduledEndTime' not in b['snippet']: return False
    if 'title' not in b['snippet']: return False

    return True


def run_schedule():
    schedule_needs_retry = False
    # get active broadcasts
    yt_active_list = []
    if args.list_active or args.schedule_file or args.list or args.club_calendar:
        # get the first page
        rq = br.list(part="id,status,snippet,contentDetails", broadcastStatus="active", broadcastType="all")
        while True:
            response = rq.execute()
            items = response.get("items")
            yt_active_list = yt_active_list + items
            if "nextPageToken" not in response: break

            rq = br.list_next(previous_request=rq, previous_response=response)
            response = rq.execute

        print("found %d active broadcasts in youtube" % len(yt_active_list))
        if args.list_active: print(yt_active_list)

    # get upcoming broadcasts
    yt_upcoming_list = []
    if args.list_upcoming or args.schedule_file or args.list or args.club_calendar:
        # get the first page
        rq = br.list(part="id,status,snippet,contentDetails", broadcastStatus="upcoming", broadcastType="all")
        while True:
            response = rq.execute()
            items = response.get("items")
            yt_upcoming_list = yt_upcoming_list + items
            if "nextPageToken" not in response: break

            rq = br.list_next(previous_request=rq, previous_response=response)
            response = rq.execute

        print("found %d upcoming broadcasts in youtube" % len(yt_upcoming_list))
        if args.list_upcoming: print(yt_upcoming_list)


    # filter out broadcasts which do not have complete data

    yt_active_list = [ b for b in yt_active_list if yt_broadcast_complete(b) ]
    yt_upcoming_list = [ b for b in yt_upcoming_list if yt_broadcast_complete(b) ]


    if args.list:
        print("upcoming and active lists:")
        print(yt_upcoming_list + yt_active_list)

    if args.list_completed:
        # get completed broadcasts

        print("completed broadcasts")
        rq = br.list(part="id,status,snippet,contentDetails", broadcastStatus="completed", broadcastType="all")
        response = rq.execute()
        print(response)

    if args.status:
        # get status for the broadcast
        if bid is not None:
            rq = br.list(part="id,status,snippet,contentDetails", broadcastType="all", id=bid)
            response = rq.execute()
            print(response)

        if sid is not None:
            rq = ls.list(id=sid, part="id,status,snippet,cdn")
            response = rq.execute()
            print(response)

    need_obs = False
    obs_is_running = (find_process(obs_exe) is not None)

    yt_to_sched = { }

    if sid is not None:
        need_obs = upcoming_list or active_list

        # check if there are streams in the schedule which either should be active
        # or need to be inserted into YouTube
        yt_possible_list = yt_active_list + yt_upcoming_list
        for s in upcoming_list + active_list:
            # find the stream in the yt_possible_list
            # it would be easier to turn the combined list into a dictionary and
            # search it by title, but there is a possibility of having multiple identical titles!
            # so instead we will do a search for an entry that maybe satisfies our critera
            # (title and end time match exactly, start time is either in the past or matches exactly,
            # and it must either be bound to our stream)
            for b in yt_possible_list:

                start = datetime.datetime.fromisoformat(b['snippet']['scheduledStartTime'])
                end = datetime.datetime.fromisoformat(b['snippet']['scheduledEndTime'])
                title = b['snippet']['title']
                bsid = b['contentDetails']['boundStreamId'] if 'boundStreamId' in b['contentDetails'] else None

                if (True
                        and s.title == title
                        and ((s.start == start) or ((s.start < start) and (s.start < now)))
                        and bsid == sid):
                    # have to remove this broadcast from my list so it is not confused with another stream
                    yt_possible_list.remove(b)
                    # also remember that this YT broadcast is really this one
                    yt_to_sched[b['id']] = s
                    break
            else:

                # TODO: what about scheduled streams we cannot schedule in YT?
                # - probably want to actually count streams in YT that should get streamed and if that list is empty we should set needs_obs=False

                # disabling below because it messes up need_obs which then starts obs and leaves it running
                # # this broadcast is not in YT yet. Do not schedule it if the end time is
                # # in less than a minute - it is just not worth it!
                # if s.end - diff_1minute < now :
                #     print("skipping broadcast", s.title, " because it will end in less than a minute at ", s.end, " now ", now, " end-1min ", s.end-diff_1minute)
                #     continue
                start = s.start
                end = s.end
                start = start if start > now else now + datetime.timedelta(seconds=5)
                end = end if start < end else start + datetime.timedelta(seconds=60)
                b = schedule_broadcast(title=s.title, start=start, end=end)
                new_broadcast = bind_broadcast(sid=sid, bid=b["id"])
                yt_upcoming_list.append(new_broadcast)


    # first process the upcoming broadcasts
    # note that we make a copy of the list so we can manipulate the original list in the loop
    # see https://stackoverflow.com/questions/1207406/how-to-remove-items-from-a-list-while-iterating/1207427#1207427
    for b in yt_upcoming_list[:]:

        start = datetime.datetime.fromisoformat(b['snippet']['scheduledStartTime'])
        end = datetime.datetime.fromisoformat(b['snippet']['scheduledEndTime'])
        bid = b['id']
        title = b['snippet']['title']

        # if the schedule has an end time that is later
        # than the current end time, use that instead
        # this will allow us to extend scheduled event times
        if b['id'] in yt_to_sched:
            s_end = yt_to_sched[b['id']].end
            if s_end > end:
                print('extending broadcast %s till %s (from %s)' % (title, s_end, end))
                end = s_end

        # check if the broadcast should have ended by now
        if now > end:
            # delete it since the broadcast should be over but hasn't started yet
            print('deleting "%s"' % title)
            delete_broadcast(bid=bid)
            continue

        # check if the broadcast needs to bind to a stream - note that we cannot handle that here!
        if 'boundStreamId' not in b['contentDetails']:
            # this has to be handled elsewhere or will get deleted later
            continue

        if b['contentDetails']['boundStreamId'] != sid:
            # avoid having issues with races by having each machine manage its own broadcasts
            continue

        stream = yt_streams[b['contentDetails']['boundStreamId']]
        if stream['status']['streamStatus'] != 'active':
            print('cannot setup broadcast "%s" because stream "%s" is not active' %
                ( title, stream['snippet']['title'] ))
            need_obs = True
            schedule_needs_retry = True
            continue

        # we always want to move from created to testing
        if b['status']['lifeCycleStatus'] == 'ready':
            print('transitioning "%s" to "testing"' % title)
            new_status = transition_broadcast(bid=bid, target_status='testing')
            b['status']['lifeCycleStatus'] = new_status
            print("transitioned to state " + new_status)
            need_obs = True

        # if we should have started, we should transition to live!
        # allow myself to start early according to prologue_time
        if now + prologue_time >= start:
            if b['status']['lifeCycleStatus'] == 'testStarting' :
                print('broadcast "%s" needs a few seconds to transition to "testing". Will try again.' % title)
                schedule_needs_retry = True
                need_obs = True
            if b['status']['lifeCycleStatus'] == 'testing':
                print('transitioning "%s" to "live"' % title)
                new_status = transition_broadcast(bid=bid, target_status='live')
                b['status']['lifeCycleStatus'] = new_status
                need_obs = True
                # we will leave this broadcast in "upcoming" list for now

    if need_obs and not obs_is_running:
        start_obs()
        obs_is_running = True

    # now process the active broadcasts
    # note that we make a copy of the list so we can manipulate the original list in the loop
    # see https://stackoverflow.com/questions/1207406/how-to-remove-items-from-a-list-while-iterating/1207427#1207427
    stopped_stream = False
    for b in yt_active_list[:]:
        end = datetime.datetime.fromisoformat(b['snippet']['scheduledEndTime'])
        bid = b['id']
        title = b['snippet']['title']


        # if the schedule has an end time that is later
        # than the current end time, use that instead
        # this will allow us to extend scheduled event times
        if b['id'] in yt_to_sched:
            s_end = yt_to_sched[b['id']].end
            if s_end > end:
                print('extending broadcast %s till %s (from %s)' % (title, s_end, end))
                end = s_end

        extra_minutes = epilogue_time
        extra_minutes += datetime.timedelta(seconds=0) if b['contentDetails']['boundStreamId'] == sid else datetime.timedelta(minutes=30)

        # check if the broadcast should have ended by now
        if now > end + extra_minutes:
            # delete it since the broadcast should be over but hasn't started yet
            print('transitioning "%s" to "complete"' % title)
            new_status = transition_broadcast(bid=bid, target_status='complete')
            yt_active_list.remove(b)
            stopped_stream = True
            continue

        if 'boundStreamId' not in b['contentDetails']:
            # this is strange and maybe impossible, but harmless to check
            continue

        if b['contentDetails']['boundStreamId'] == sid:
            need_obs = True


    if not need_obs and obs_is_running and (stopped_stream or args.always_auto_stop_obs):
        stop_obs()


    return not schedule_needs_retry


schedule_successful = False
first_iter = True
num_iters = 0
while not schedule_successful:

    if not first_iter:
        list_yt_streams()

    first_iter = False

    schedule_successful = run_schedule()

    if not schedule_successful:
        print("Sleeping for 15 seconds before checking on broadcasts with YouTube")
        time.sleep(15)
        get_now()

    num_iters += 1
    if num_iters > 4 : break



yt.close()


