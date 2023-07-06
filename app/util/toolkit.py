import logging
log = logging.getLogger('root')
from util.toolkit_debug import debug
from jira import JIRA
from dateutil.parser import *
import datetime
from datetime import timezone, timedelta
import traceback
import re
from util.jql import Status
import ipdb

# JIRA
def jira_authenticate(url, u, p):
    try:
        log.debug("Attempting to authenticate to '" + url + "' (username: '" + u + "' password: ----)")
        j = JIRA(url, basic_auth=(u, p))
        log.debug("Successful authentication!")
    except:
        log.error("Error when trying to authenticate to '" + url + "' (username: '" + u + "'" + "' password: ----)")
        raise
    return j

def jira_token_authenticate(url, t):
    try:
        log.debug("Attempting to authenticate to '" + url + "' (token: ---)")
        j = JIRA(server=url, token_auth=t)
        log.debug("Successful authentication!")
    except:
        log.error("Error when trying to authenticate to '" + url + "' (token: ---)")
        raise
    return j

def run_jql(jira, jql, max=False, debug=False):
    if debug:
        log.debug("JQL -> {}".format(jql))
    return jira.search_issues(jql, maxResults=max)

# @debug
def count_transitions(status_from, status_to, changelog):
    count = 0
    for history in reversed(changelog.histories):
        for item in history.items:
            if item.field == 'status' and item.fromString == status_from and item.toString == status_to:
                count += 1
    return count

# @debug
def calc_working_seconds(from_date, to_date):
    result = 0

    # log.debug("From date: {}".format(from_date))
    # log.debug("To date: {}".format(to_date))
    # log.debug("Total Delta: {}".format(str(to_date - from_date)))

    # Workday
    workday_start_time = datetime.datetime.strptime("09:00:00", "%H:%M:%S").time()
    workday_stop_time  = datetime.datetime.strptime("17:30:00", "%H:%M:%S").time()


    # ipdb.set_trace()
    # Check if from_date occurred outside working hours
    if workday_start_time > from_date.time():
        # log.debug("From time occurred before start of working hours (i.e. at {} on {})".format(from_date.time(), from_date.date()))
        from_date = from_date.replace(hour=workday_start_time.hour,
                                      minute=workday_start_time.minute,
                                      second=workday_start_time.second,
                                      microsecond=workday_start_time.microsecond)
        # log.debug("New from_date: {}".format(from_date))

    elif workday_stop_time < from_date.time():
        # log.debug("From time occurred after end of working hours (i.e. at {} on {})".format(from_date.time(), from_date.date()))
        from_date = from_date.replace(hour=workday_stop_time.hour,
                                      minute=workday_stop_time.minute,
                                      second=workday_stop_time.second,
                                      microsecond=workday_stop_time.microsecond)
        # log.debug("New from_date: {}".format(from_date))

    # Check if to_date occurred outside working hours
    if workday_start_time > to_date.time():
        # log.debug("To time occurred before start of working hours (i.e. at {} on {})".format(to_date.time(), to_date.date()))
        to_date = to_date.replace(hour=workday_start_time.hour,
                                  minute=workday_start_time.minute,
                                  second=workday_start_time.second,
                                  microsecond=workday_start_time.microsecond)
        # log.debug("New to_date: {}".format(to_date))

    elif workday_stop_time < to_date.time():
        # log.debug("To time occurred after end of working hours (i.e. at {} on {})".format(to_date.time(), to_date.date()))
        to_date = to_date.replace(hour=workday_stop_time.hour,
                                  minute=workday_stop_time.minute,
                                  second=workday_stop_time.second,
                                  microsecond=workday_stop_time.microsecond)
        # log.debug("New to_date: {}".format(to_date))


    if from_date.date() == to_date.date():
        # log.debug("From/To times occurred on same day")
        result = (to_date - from_date).total_seconds()
    elif from_date.date() < to_date.date():
        # log.debug("From/To times occurred on different days")

        # Get seconds until current EOD
        result = (datetime.timedelta(hours=workday_stop_time.hour,
                                     minutes=workday_stop_time.minute,
                                     seconds=workday_stop_time.second) -
                  datetime.timedelta(hours=from_date.time().hour,
                                     minutes=from_date.time().minute,
                                     seconds=from_date.time().second)).total_seconds()

        # log.debug("Seconds until EOD {} are {}".format(from_date.date(), str(result)))

        # Next day morning
        next_day = (from_date + datetime.timedelta(days=1)).replace(hour=workday_start_time.hour,
                                                                    minute=workday_start_time.minute,
                                                                    second=workday_start_time.second)

        while True:
            # log.debug("Next day {}".format(next_day))
            if next_day.date() == to_date.date():
                result += (to_date - next_day).total_seconds()
                # log.debug("to_date - next_day {} sec".format(str(result)))
                break
            elif next_day.date() < to_date.date() and next_day.weekday() < 5:
                # log.debug("Is weekday {}".format(next_day))
                result += (next_day.replace(hour=workday_stop_time.hour,
                                            minute=workday_stop_time.minute,
                                            second=workday_stop_time.second) - next_day).total_seconds()

            next_day += datetime.timedelta(days=1)

    return result


# @debug
def get_time_between_extreme_statuses(from_status, to_status, changelog):
    in_time = ""
    out_time = ""
    result = 0
    # log.debug("Getting time between first occurrence of {} -> last occurrence of {}".format(from_status, to_status))
    # Search for newest occurrence of needed status
    for history in changelog.histories:
        for item in history.items:
            if item.field == 'status' and not in_time:
                if from_status == Status.BACKLOG.value:
                    log.warning("Do NOT use this function for the first status that the ticket gets automatically when it is new as Jira doesnt write the first status as a status change but only as created date")
                    in_time = parse(history.created)
                elif from_status == item.toString:
                    # log.debug("Found {} on {}".format(from_status, str(history.created)))
                    in_time = parse(history.created)
                    break
    if in_time:
        # Search for oldest occurrence of needed status
        for history in changelog.histories:
            for item in history.items:
                if item.field == 'status':
                    if item.toString == to_status and not out_time:
                        # log.debug("Found {} on {}".format(to_status, str(history.created)))
                        out_time = parse(history.created)
                        result = calc_working_seconds(in_time, out_time)
                        log.debug("get_time_between_extreme_statuses {} -> {} = {} sec (workhours: {} duration: {})".format(from_status, to_status, result,
                                                                                      datetime.timedelta(seconds=result),
                                                                                      str(out_time - in_time)))
    return result

# @debug
def get_time_from_creation_to_extreme_status(created, to_status, changelog):
    in_time = parse(created)
    out_time = ""
    result = 0

    # log.debug("Getting time between issue creation -> last occurrence of {}".format(to_status))
    # log.debug("Found Issue creation on {}".format(in_time))
    # Search for oldest occurrence of needed status
    for history in changelog.histories:
        for item in history.items:
            if item.field == 'status':
                if item.toString == to_status and not out_time:
                    out_time = parse(history.created)
                    # log.debug("Found {} on {}".format(to_status, out_time))
                    result = calc_working_seconds(in_time, out_time)
                    log.debug("get_time_from_creation_to_extreme_status {} = {} sec (workhours: {} duration: {})".format(to_status, result, datetime.timedelta(seconds=result), str(out_time - in_time)))

    return result

# @debug
def get_time_between_distant_statuses(from_status, to_status, changelog):
    in_flag = False
    in_time = ""
    result = []

    # log.debug("Getting time between {} -> {}".format(from_status, to_status))

    for history in reversed(changelog.histories):
        for item in history.items:
            if item.field == 'status':
                if item.toString == from_status and not in_flag:
                    in_flag = True
                    in_time = parse(history.created)
                    # log.debug("Found  " + item.toString + " on  " + history.created)
                elif item.toString == to_status and in_flag:
                    in_flag = False
                    out_time = parse(history.created)
                    # log.debug("Found  " + item.toString + " on  " + history.created)
                    result.append(calc_working_seconds(in_time, out_time))

                    # log.debug("get_time_between_statuses {} -> {} = {} sec (working: {} actual: {})".format(from_status, to_status, result[len(result)-1], datetime.timedelta(seconds=result[len(result)-1]), str(out_time-in_time)))

    return result


def get_time_between_adjacent_statuses(from_status, to_status, changelog):
    in_flag = False
    in_time = ""
    result = []

    # log.debug("Getting time between {} -> {}".format(from_status, to_status))

    for history in reversed(changelog.histories):
        for item in history.items:
            if item.field == 'status':
                if item.toString == from_status and not in_flag:
                    in_flag = True
                    in_time = parse(history.created)
                    # log.debug("Found  " + item.toString + " on  " + history.created)
                    continue
                elif in_flag:
                    in_flag = False
                    if item.toString == to_status:
                        out_time = parse(history.created)
                        # log.debug("Found  " + item.toString + " on  " + history.created)
                        result.append(calc_working_seconds(in_time, out_time))
                        # log.debug("get_time_between_statuses {} -> {} = {} sec (working: {} actual: {})".format(from_status, to_status, result[len(result)-1], datetime.timedelta(seconds=result[len(result)-1]), str(out_time-in_time)))

    return result

# @debug
def get_time_in_status(status, changelog):
    in_flag = False
    in_time = ""
    result = []

    # log.debug("Getting time for status {}".format(status))

    for history in changelog.histories:
        for item in history.items:
            if item.field == 'status':
                # print(item.toString)
                if item.toString == status and not in_flag:
                    in_flag = True
                    in_time = parse(history.created)
                    # log.debug("Found  " + item.toString + " on  " + history.created)
                    continue
                elif in_flag:
                    in_flag = False
                    out_time = parse(history.created)
                    # log.debug("Found  " + item.toString + " on  " + history.created)
                    result.append(calc_working_seconds(in_time, out_time))
                    log.debug("get_time_in_status {} = {} sec (workhours: {} duration: {})".format(status, result[len(result)-1], datetime.timedelta(seconds=result[len(result)-1]), str(out_time-in_time)))

    return result

# @debug
def get_time_in_initial_status(status, changelog, created):
    in_time = parse(created)
    result = []

    # log.debug("Getting time for initial status {} created on {}".format(status, created))

    for history in changelog.histories:
        for item in history.items:
            if item.field == 'status':
                out_time = parse(history.created)
                # log.debug("Found  " + item.toString + " on  " + history.created)
                result.append(calc_working_seconds(in_time, out_time))
                # log.debug("get_time_in_initial_status {} = {} sec (working: {} actual: {})".format(status, result[len(result)-1], datetime.timedelta(seconds=result[len(result)-1]), str(out_time-in_time)))
                # Initial status may be obtained in later phases of the ticket lifecycle so we want to capture them too
                result.extend(get_time_in_status(status, changelog))
                return result


def get_time_in_current_status(status, changelog):
    in_flag = False
    in_time = ""
    result = []

    # log.debug("Getting time in current status {} ".format(status))

    for history in changelog.histories:
        for item in history.items:
            if item.field == 'status':
                if item.toString == status and not in_flag:
                    in_flag = True
                    # log.debug("Found  " + item.toString + " on " + history.created)
                    in_time = parse(history.created)

                    timezone_offset = 0.0  # UTC
                    tzinfo = timezone(timedelta(hours=timezone_offset))
                    out_time = datetime.datetime.now(tzinfo)
                    result.append(calc_working_seconds(in_time, out_time))
                    log.debug("get_time_in_current_status {} = {} sec (workhours: {} duration: {})".format(status, result[len(result)-1], datetime.timedelta(seconds=result[len(result)-1]), str(out_time-in_time)))

    return result


# @debug
def jql_results_amount(jira, jql):
    # Run JQL query
    jql_exec = run_jql(jira, jql, False, True)
    return len(jql_exec)

def seconds_to_hours(sec):
    return sec/3600
