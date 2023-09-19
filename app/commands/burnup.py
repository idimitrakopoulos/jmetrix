import logging
log = logging.getLogger('root')
from util.jql import JQLs, Filters, Status
from util.toolkit import jira_token_authenticate, run_jql, fancy_print_issue_timings, get_time_in_current_status, \
    get_time_between_distant_statuses, group_issues_by_assignee, seconds_to_hours
import ipdb, json

from datetime import datetime, timedelta


def calculate_weeks_without_weekends(from_date, to_date=None):
    result = {}
    counter = 1
    period_end = None
    try:
        # Convert the input date string to a datetime object
        input_date = datetime.strptime(from_date, '%Y-%m-%d')

        # Initialize the current week's starting date as the input date
        current_week_start = input_date

        # Calculate the end of the current week (Friday)
        current_week_end = current_week_start + timedelta(days=(4 - current_week_start.weekday() + 7) % 7, hours=23, minutes=59, seconds=59)

        result["week" + str(counter)] = (current_week_start, current_week_end)

        if to_date:
            period_end = datetime.strptime(to_date, '%Y-%m-%d')
        else:
            period_end = datetime.today()

        # Iterate through weeks and print them until we reach the end of the current week
        while current_week_end <= period_end:
            counter += 1
            # Move to the next week
            current_week_start = current_week_end + timedelta(hours=00, minutes=00, seconds=1)  # Start on Saturdays
            current_week_end = current_week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)  # End on Friday
            result["week" + str(counter)] = (current_week_start, current_week_end)
        return result
    except ValueError:
        print("Invalid date format. Please use the format 'YYYY-MM-DD'.")



def exec(args):

    # Connect to Jira instance
    jira = jira_token_authenticate(args.jira_server_url, args.jira_auth_token)

    aggregates = dict()

    project_weeks = calculate_weeks_without_weekends(args.date_from, args.date_to)

    for project_week in project_weeks.values():
        log.debug(f"Week from {project_week[0].strftime('%Y-%m-%d')} to {project_week[1].strftime('%Y-%m-%d')}")

        # # TOTAL ISSUES CREATED
        # total_issues_created_jql = "{} {} {}".format(JQLs.JQL_PROJECT.value.format(args.jira_project),
        #                                               Filters.NOT_TYPE_EPIC.value,
        #                                               Filters.IN_LABEL.value.format(args.jira_label) + " " + Filters.IN_LABEL.value.format(args.jira_extra_label) if args.jira_extra_label else "")
        # total_issues_created = run_jql(jira, total_issues_created_jql)
        # aggregates['total_issues_created'] = {'length': len(total_issues_created), 'jql': total_issues_created_jql}