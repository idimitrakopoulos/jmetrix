import logging
log = logging.getLogger('root')
from util.debug_toolkit import debug
from jira import JIRA
from dateutil.parser import *
import datetime
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
def calc_days_from_now_using_working_hours(working_seconds):
    result = None
    # Date NOW
    from_date = datetime.datetime.now()
    # log.debug("Date now {}".format(from_date))
    # Workday
    workday_hours = 8
    working_days = int((working_seconds/3600) / workday_hours)

    # log.debug("Working Days {}".format(working_days))


    while working_days > 0:
        from_date += datetime.timedelta(days=1)
        weekday = from_date.weekday()
        if weekday >= 5:
            continue
        working_days -= 1

    result = from_date.strftime("%Y-%m-%d")
    # log.debug("result {}".format(result))

    return result


# @debug
def count_field_values(field_name, changelog):
    result = {}
    for history in reversed(changelog.histories):
        for item in history.items:
            if item.field == field_name:
                reasons = [x.strip() for x in item.toString.split(',')]
                for r in reasons:
                    if r in result and r != "":
                        result[r] += 1
                        # log.debug("{} {} times due to '{}' (Total Transitions: {})".format(field_name, str(result[r]), r, sum(result.values())))
                    elif r not in result and r != "":
                        result[r] = 1
                        # log.debug("{} 1 time due to '{}' (Total Transitions: {})".format(field_name, r, sum(result.values())))


    return result

# @debug
def get_time_between_extreme_statuses(from_status, to_status, changelog):
    in_time = ""
    out_time = ""
    result = 0
    # log.debug("Getting time between first occurrence of {} -> last occurrence of {}".format(from_status, to_status))
    # Search for newest occurrence of needed status
    for history in reversed(changelog.histories):
        for item in history.items:
            if item.field == 'status' and not in_time:
                if from_status == Status.BACKLOG.value:
                    log.warning("Do NOT use this function for OPEN status as Jira doesnt write the first status as a status change but only as created date")
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

    for history in reversed(changelog.histories):
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
                    result.append(calc_working_seconds(out_time, in_time))
                    log.debug("get_time_in_status {} = {} sec (workhours: {} duration: {})".format(status, result[len(result)-1], datetime.timedelta(seconds=result[len(result)-1]), str(in_time-out_time)))

    return result

# @debug
def get_time_in_initial_status(status, changelog, created):
    in_time = parse(created)
    result = []

    # log.debug("Getting time for initial status {} created on {}".format(status, created))

    for history in reversed(changelog.histories):
        for item in history.items:
            if item.field == 'status':
                out_time = parse(history.created)
                # log.debug("Found  " + item.toString + " on  " + history.created)
                result.append(calc_working_seconds(in_time, out_time))
                # log.debug("get_time_in_initial_status {} = {} sec (working: {} actual: {})".format(status, result[len(result)-1], datetime.timedelta(seconds=result[len(result)-1]), str(out_time-in_time)))
                # Initial status may be obtained in later phases of the ticket lifecycle so we want to capture them too
                result.extend(get_time_in_status(status, changelog))
                return result

# @debug
def retrieve_pbi_data(jira, jql):
    from util.jira_obj import PBI

    # Run JQL query
    jql_exec = run_jql(jira, jql, False, True)
    pbi_list = []

    try:
        # Skip execution for this JQL if it's empty
        if len(jql_exec) == 0: raise RuntimeWarning

        # Loop on every issue
        for issue in jql_exec:
            log.debug("{} | {} | {}".format(issue, issue.fields.issuetype.name, issue.fields.summary))
            pbi = PBI(jira.issue(issue.key, expand='changelog'))
            pbi_list.append(pbi)

    except RuntimeWarning:
        log.warning('JQL "{}" did not return any issues.'.format(jql))

    except Exception:
        log.exception("Oops...")
        # print(traceback.format_exc())


    return pbi_list

# @debug
def retrieve_tpr_data(jira, jql):
    from util.jira_obj import TPR

    # Run JQL query
    jql_exec = run_jql(jira, jql, False, True)
    tpr_list = []

    try:
        # Skip execution for this JQL if it's empty
        if len(jql_exec) == 0: raise RuntimeWarning

        # Loop on every issue
        for issue in jql_exec:
            log.debug("{} | {} | {}".format(issue, issue.fields.issuetype.name, issue.fields.summary))
            tpr = TPR(jira.issue(issue.key, expand='changelog'))
            tpr_list.append(tpr)

    except RuntimeWarning:
        log.warning('JQL "{}" did not return any issues.'.format(jql))

    except Exception:
        log.exception("Oops...")
        # print(traceback.format_exc())


    return tpr_list


# @debug
def jql_results_amount(jira, jql):
    # Run JQL query
    jql_exec = run_jql(jira, jql, False, True)
    return len(jql_exec)

def seconds_to_hours(sec):
    return sec/3600

# @debug
def get_sizing_accuracy(size, seconds_to_compare):
    result = -1
    ranges = {'XS' : range(1, 3601),
              'S' : range(3601, 14401),
              'M' : range(14401, 57601),
              'L' : range(57601, 115201),
              'XL' : range(115201, 144002),}

    if size != 'NB' and seconds_to_compare != 0:
        if seconds_to_compare in ranges[size]:
            # log.debug('Seconds {} are within range of {} ({})'.format(seconds_to_compare, size, str(ranges[size])))
            result = 100
        elif seconds_to_compare < ranges[size].start:
            # log.debug('Seconds {} are less than range of {} ({})'.format(seconds_to_compare, size, str(ranges[size])))
            result = (seconds_to_compare / ranges[size].start) * 100
        elif seconds_to_compare > ranges[size].stop:
            # log.debug('Seconds {} are more than range of {} ({})'.format(seconds_to_compare, size, str(ranges[size])))
            result = (ranges[size].stop / seconds_to_compare) * 100

    return result


def get_unique_keys_from_list_of_dicts(lst):
    return list(set(key for dic in lst for key in dic.keys()))


def switch_string_to_var_name(string):
    return re.sub('\W+',' ', string).lower().strip().replace(' ', '_')

def retrieve_metric_from_composite_pbi_list(metric_name, cpbis):
    result = list()

    for cpbi in cpbis:
        # log.debug("pbi type: {} items: {}".format(cpbi.jira_issuetype, len(cpbi.pbis)))
        for pbi in cpbi.pbis:
            result.append(pbi.values[metric_name])

    return result
