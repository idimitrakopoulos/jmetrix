import logging
log = logging.getLogger('root')
from util.toolkit_debug import debug
from jira import JIRA
from dateutil.parser import *
import datetime
from datetime import timezone, timedelta
import traceback
import re
from util.jql import Status, Filters

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
        j = JIRA(server=url, token_auth=t, options={'verify': False})
        log.debug("Successful authentication!")
    except:
        log.error("Error when trying to authenticate to '" + url + "' (token: ---)")
        raise
    return j

def run_jql(jira, jql, max=False, debug=True):
    if debug:
        log.debug("JQL -> {}".format(jql))
    return jira.search_issues(jql, expand='changelog', maxResults=max)

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
    result = {'worktime': 0, 'duration': 0}

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
                        result['worktime'] = calc_working_seconds(in_time, out_time)
                        result['duration'] = (out_time - in_time).total_seconds()
                        # log.debug("get_time_between_extreme_statuses {} -> {} = {} sec (workhours: {} duration: {})".format(from_status, to_status, result,
                        #                                                               datetime.timedelta(seconds=result),
                        #                                                               str(out_time - in_time)))
    return result

# @debug
def get_time_from_creation_to_extreme_status(created, to_status, changelog):
    in_time = parse(created)
    out_time = ""
    result = {'worktime': 0, 'duration': 0}

    # log.debug("Getting time between issue creation -> last occurrence of {}".format(to_status))
    # log.debug("Found Issue creation on {}".format(in_time))
    # Search for oldest occurrence of needed status
    # ipdb.set_trace()
    for history in changelog.histories:
        for item in history.items:
            if item.field == 'status':
                if item.toString == to_status and not out_time:
                    out_time = parse(history.created)
                    # log.debug("Found {} on {}".format(to_status, out_time))
                    result['worktime'] = calc_working_seconds(in_time, out_time)
                    result['duration'] = (out_time - in_time).total_seconds()
                    # log.debug("get_time_from_creation_to_extreme_status {} = {} sec (workhours: {} duration: {})".format(to_status, result, datetime.timedelta(seconds=result), str(out_time - in_time)))

    return result

# @debug
def get_time_between_distant_statuses(from_status, to_status, changelog):
    in_flag = False
    in_time = ""
    out_time = ""

    result = {'worktime': 0, 'duration': 0}

    # log.debug("Getting time between {} -> {}".format(from_status, to_status))

    for history in changelog.histories:
        for item in history.items:
            if item.field == 'status':
                if item.fromString == from_status and not in_flag:
                    in_flag = True
                    in_time = parse(history.created)
                    # log.debug("{} -> {} on {}".format(item.fromString, item.toString, in_time))
                elif item.toString == to_status and in_flag:
                    in_flag = False
                    out_time = parse(history.created)
                    result['worktime'] = calc_working_seconds(in_time, out_time)
                    result['duration'] = (out_time - in_time).total_seconds()
                    # log.debug("{} -> {} on {}".format(item.fromString, item.toString, out_time))

    return result

def get_time_from_creation_to_now(created):
    in_time = parse(created)
    out_time = ""
    timezone_offset = 0.0  # UTC
    tzinfo = timezone(timedelta(hours=timezone_offset))
    out_time = datetime.datetime.now(tzinfo)
    result = {'worktime': 0, 'duration': 0}

    result['worktime'] = calc_working_seconds(in_time, out_time)
    result['duration'] = (out_time - in_time).total_seconds()

    return result

# @debug
def get_time_in_status(status, changelog):
    in_flag = False
    in_time = ""
    out_time = ""
    result = {'worktime': 0, 'duration': 0}

    # log.debug("Getting time for status {}".format(status))

    for history in changelog.histories:
        for item in history.items:
            if item.field == 'status':
                # print(item.field + " " + item.fromString + "->" + item.toString)
                if item.toString == status and not in_flag:
                    in_flag = True
                    in_time = parse(history.created)
                    # log.debug("Found " + item.toString + " on  " + history.created)
                    continue
                elif in_flag:
                    in_flag = False
                    out_time = parse(history.created)
                    # log.debug("Found " + item.toString + " on  " + history.created)
                    result['worktime'] = calc_working_seconds(in_time, out_time)
                    result['duration'] = (out_time - in_time).total_seconds()
                    # log.debug("get_time_in_status {} = {} sec (workhours: {} duration: {})".format(status, result[len(result)-1], datetime.timedelta(seconds=result[len(result)-1]), str(out_time-in_time)))
                    return result

    # If out_time isnt found then the issue is currently being worked on this status so set the end date/time as the current date/time and return it
    if in_time and out_time == "":
        timezone_offset = 0.0  # UTC
        tzinfo = timezone(timedelta(hours=timezone_offset))
        out_time = datetime.datetime.now(tzinfo)
        result['worktime'] = calc_working_seconds(in_time, out_time)
        result['duration'] = (out_time - in_time).total_seconds()

    return result


# @debug
def get_time_in_initial_status(status, changelog, created):
    in_time = parse(created)
    result = {}

    # log.debug("Getting time for initial status {} created on {}".format(status, created))
    for history in changelog.histories:
        for item in history.items:
            if item.field == 'status':
                out_time = parse(history.created)
                # log.debug("Found " + item.toString + " on  " + history.created)
                result['worktime'] = calc_working_seconds(in_time, out_time)
                result['duration'] = (out_time - in_time).total_seconds()

                # log.debug("get_time_in_initial_status {} = {} sec (working: {} actual: {})".format(status, result[len(result) - 1], datetime.timedelta(seconds=result[len(result) - 1]), str(out_time - in_time)))
                return result

    # If no result it means that jira doesnt have a history for it so force it
    if not result:
        timezone_offset = 0.0  # UTC
        tzinfo = timezone(timedelta(hours=timezone_offset))
        out_time = datetime.datetime.now(tzinfo)
        result['worktime'] = calc_working_seconds(in_time, out_time)
        result['duration'] = (out_time - in_time).total_seconds()

    # ipdb.set_trace()
    return result



def get_time_in_current_status(status, changelog):
    in_flag = False
    in_time = ""
    result = {'worktime': 0, 'duration': 0}

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
                    result['worktime'] = calc_working_seconds(in_time, out_time)
                    result['duration'] = (out_time - in_time).total_seconds()
                    # log.debug("get_time_in_current_status {} = {} sec (workhours: {} duration: {})".format(status, result[len(result)-1], datetime.timedelta(seconds=result[len(result)-1]), str(out_time-in_time)))
                    return result

    return result

def group_issues_by_assignee(issues):
    import collections
    grouped_dict = collections.defaultdict(list)
    for key, value in issues.items():
        assignee = value['fields']['assignee']
        grouped_dict[assignee].append(value)
    return grouped_dict

def seconds_to_hours(seconds, rounding=2):
    return round(seconds/3600, rounding)


def fancy_print_issue_summary(issues, title=""):
    if issues:
        from rich.console import Console
        from rich.table import Table

        table = Table(title=title)

        table.add_column("Key", justify="left", style="bright_yellow", no_wrap=True)
        table.add_column("Type", justify="left", style="white", no_wrap=True)
        table.add_column("Summary", justify="left", style="white")
        table.add_column("Labels", justify="left", style="white")
        table.add_column("Status", justify="left", style="white", no_wrap=True)
        table.add_column("Resolution", justify="left", style="white")
        for issue in issues:
            table.add_row(issue.key,
                          issue.fields.issuetype.name,
                          issue.fields.summary,
                          ', '.join(map(str, issue.fields.labels)),
                          issue.fields.status.name,
                          "None" if isinstance(issue.fields.resolution, type(None)) else issue.fields.resolution.name)

        console = Console()
        console.print(table)
    else:
        log.debug("No issues to print.")



def fancy_print_issue_history(issues, title="", from_to_date=None):
    if issues:
        from rich.console import Console
        from rich.table import Table

        table = Table(title=title)

        table.add_column("Key", justify="left", style="bright_yellow", no_wrap=True)
        table.add_column("Epic", justify="left", style="bright_cyan", no_wrap=True)
        table.add_column("User", justify="left", style="white", no_wrap=True)
        table.add_column("Date", justify="left", style="white", no_wrap=True)
        table.add_column("Type", justify="left", style="white")
        table.add_column("From", justify="left", style="white")
        table.add_column("To", justify="left", style="white")

        for issue in issues:
            # log.debug("Key: {}, Type: {}".format(issue.key, issue.fields.issuetype))
            for history in issue.changelog.histories:
                for item in history.items:
                    if item.field == 'status' or item.field == 'summary' or item.field == 'type' or item.field == 'labels':
                        table.add_row(issue.key, issue.fields.customfield_13520, history.author.displayName, str(parse(history.created).date()), item.field, item.fromString, item.toString)
                    elif (item.field == 'Acceptance Criteria'):
                        table.add_row(issue.key, issue.fields.customfield_13520, history.author.displayName, str(parse(history.created).date()), item.field, "***", "***")
                    # else:
                    #     print(item.field)
            table.add_section()
        console = Console()
        console.print(table)
    else:
        log.debug("No issues to print.")


def fancy_print_issue_timings(issues, title=""):
    if issues:
        from rich.console import Console
        from rich.table import Table

        table = Table(title=title)

        table.add_column("Key", justify="left", style="bright_yellow", no_wrap=True)
        table.add_column("Type", justify="left", style="white")
        table.add_column("Assignee", justify="left", style="white", no_wrap=True)
        table.add_column("Labels", justify="left", style="white")
        table.add_column("Status", justify="left", style="white", no_wrap=True)
        table.add_column("Workhours in status (h)", justify="left", style="white")
        table.add_column("Duration in status (h)", justify="left", style="white")
        table.add_column("Original Estimation (h)", justify="left", style="white")
        table.add_column("Actual Workhours (h)", justify="left", style="white")
        table.add_column("Consumed %", justify="left", style="white")

        for issue in issues:
            # ipdb.set_trace()
            # log.debug("Key: {}, Type: {}".format(issue.key, issue.fields.issuetype))
            table.add_row(issues[issue]['key'],
                          issues[issue]['fields']['type'],
                          "Unassigned" if isinstance(issues[issue]['fields']['assignee'], type(None)) else issues[issue]['fields']['assignee'],
                          ', '.join(map(str, issues[issue]['fields']['labels'])),
                          issues[issue]['fields']['status'],
                          str(seconds_to_hours(issues[issue]['t_current_status']['worktime'])),
                          str(seconds_to_hours(issues[issue]['t_current_status']['duration'])),
                          "n/a" if isinstance(issues[issue]['fields']['original_estimate'], type(None)) else str(seconds_to_hours(issues[issue]['fields']['original_estimate'])),
                          str(seconds_to_hours(issues[issue]['t_overall']['worktime'])),
                          "{}%".format(str(round(issues[issue]['pct_consumed'], 2))) if issues[issue]['pct_consumed'] >= 0 else "n/a")

        console = Console()
        console.print(table)
    else:
        log.debug("No issues to print.")


def fancy_print_jql_info(aggregates, title=""):
    if aggregates:
        from rich.console import Console
        from rich.table import Table

        table = Table(title=title)

        table.add_column("Label", justify="left", style="bright_yellow", no_wrap=True)
        table.add_column("JQL", justify="left", style="white")
        table.add_column("Issue Keys", justify="left", style="white")
        table.add_column("Number of issues", justify="left", style="white", no_wrap=True)


        for aggregate in aggregates:
            # ipdb.set_trace()
            table.add_row(str(aggregate),
                          str(aggregates[aggregate]['jql']),
                          str(aggregates[aggregate]['keys']),
                          str(aggregates[aggregate]['length']))
            table.add_section()

        console = Console()
        console.print(table)
    else:
        log.debug("No aggregates to print.")

# def fancy_print_issue_assignees(issues):
#     # ipdb.set_trace()
#     if issues:
#         from rich.console import Console
#         from rich.table import Table
#
#         table = Table()
#         table.add_column("W", justify="left", style="bright_red")
#         table.add_column("Assignee", justify="left", style="bright_yellow", no_wrap=True)
#         table.add_column("Key", justify="left", style="white", no_wrap=True)
#         table.add_column("Type", justify="left", style="white")
#         table.add_column("Labels", justify="left", style="white")
#         table.add_column("Status", justify="left", style="white", no_wrap=True)
#         table.add_column("Workhours in status (h)", justify="left", style="white", no_wrap=True)
#
#         for assignee in issues:
#             # log.debug("Key: {}, Type: {}".format(issue.key, issue.fields.issuetype))
#             table.add_row("*" if (issues[assignee] is None and not issue[assignee]['fields']['status'].startswith("Ready")) or assignee is not None and issues[assignee]['fields']['status'].startswith("Ready") else "",
#                           "Unassigned" if isinstance(issues[assignee].fields.assignee, type(None)) else assignee.fields.assignee.displayName,
#                           assignee.key,
#                           assignee.fields.issuetype.name,
#                           ', '.join(map(str, assignee.fields.labels)),
#                           assignee.fields.status.name,
#                           str(seconds_to_hours(sum(get_time_in_current_status(assignee.fields.status.name, assignee.changelog)))))
#
#         console = Console()
#         console.print(table)
#     else:
#         log.debug("No issues to print.")

def add_worktimes_and_durations(counters):
    from collections import Counter
    result = Counter()
    for c in counters:
        result = result + c

    if not result['worktime']:
        result['worktime'] = 0

    if not result['duration']:
        result['duration'] = 0

    return dict(result)

def print_result_list_keys(title, lst):
    log.debug(title)
    for key in lst:
        print(key)

def simple_print_issue_keys(issues, title=""):
    result = []
    if issues:
        log.debug(title)
        for issue in issues:
            result.append(issue.key)

        log.debug(', '.join(result))

def prepare_jira_labels(input):
    labels = input.split(";")
    result = ""

    for idx, label in enumerate(labels):
        if label[0] == "!":
            labels[idx] = Filters.NOT_IN_LABEL.value.format(label)
        else:
            labels[idx] = Filters.IN_LABEL.value.format(label)

    return ' '.join(labels)

def get_jira_issue_keys(issues):
    result = []
    if issues:
        for issue in issues:
            result.append(issue.key)
    return ', '.join(result)

def get_jira_issue_and_epic_keys(issues):
    from collections import defaultdict
    result = ""
    key_array = []
    if issues:
        for issue in issues:
            key_array.append([issue.key, issue.fields.customfield_13520])

    grouped_strings = defaultdict(list)
    for item, group in key_array:
        grouped_strings[group].append(item)
    for group, items in grouped_strings.items():
        result += f"{group}: {' '.join(items)}\n"

    return result