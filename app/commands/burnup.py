import logging
log = logging.getLogger('root')
from util.jql import Filters, Status, IssueType
from util.toolkit import jira_token_authenticate, run_jql, fancy_print_issue_timings, get_time_in_current_status, \
    get_time_between_distant_statuses, group_issues_by_assignee, seconds_to_hours, prepare_jira_labels, get_jira_issue_keys, \
    fancy_print_jql_info, fancy_print_issue_history
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

    generic_aggregates = dict()
    week_aggregates = dict()

    # Determine Weeks
    project_weeks = calculate_weeks_without_weekends(args.date_from, args.date_to)

    # Prepare lvl1 and lvl2 labels as given by user
    prepared_jira_lvl1_labels = prepare_jira_labels(args.jira_lvl1_labels)
    prepared_jira_lvl2_labels = prepare_jira_labels(args.jira_lvl2_labels)

    # ALL
    total_initiative_issues_jql = "{} {} {}".format(Filters.PROJECT.value.format(args.jira_project),
                                                          Filters.IN_ISSUETYPE.value.format("{}, {}, {}, {}".format(IssueType.STORY.value, IssueType.BUG.value, IssueType.TASK.value, IssueType.SPIKE.value)),
                                                          prepared_jira_lvl1_labels)
    total_initiative_issues = run_jql(jira, total_initiative_issues_jql)
    generic_aggregates['total_initiative_issues_jql'] = {'length': len(total_initiative_issues), 'keys': get_jira_issue_keys(total_initiative_issues), 'jql': total_initiative_issues_jql}

    # UNCATEGORIZED
    total_uncategorized_issues_jql = "{} {} {} {}".format(Filters.PROJECT.value.format(args.jira_project),
                                                          # Filters.CREATED_DATETIME_FROM_TO.value.format(datetime.strftime(project_week[0], '%Y-%m-%d %H:%M'), datetime.strftime(project_week[1], '%Y-%m-%d %H:%M')),
                                                          Filters.EPIC_LINK_IS_EMPTY.value,
                                                          Filters.IN_ISSUETYPE.value.format("{}, {}, {}, {}".format(IssueType.STORY.value, IssueType.BUG.value, IssueType.TASK.value, IssueType.SPIKE.value)),
                                                          prepared_jira_lvl1_labels)

    total_uncategorized_issues = run_jql(jira, total_uncategorized_issues_jql)
    generic_aggregates['total_uncategorized_issues'] = {'length': len(total_uncategorized_issues), 'keys': get_jira_issue_keys(total_uncategorized_issues), 'jql': total_uncategorized_issues_jql}

    # UNPLANNED
    total_unplanned_issues_jql = "{} {} {} {} {}".format(Filters.PROJECT.value.format(args.jira_project),
                                                         # Filters.CREATED_DATETIME_FROM_TO.value.format(datetime.strftime(project_week[0], '%Y-%m-%d %H:%M'), datetime.strftime(project_week[1], '%Y-%m-%d %H:%M')),
                                                         Filters.EPIC_LINK_IS_EMPTY.value,
                                                         Filters.IN_ISSUETYPE.value.format("{}, {}, {}, {}".format(IssueType.STORY.value, IssueType.BUG.value, IssueType.TASK.value, IssueType.SPIKE.value)),
                                                         prepared_jira_lvl1_labels,
                                                         prepared_jira_lvl2_labels)

    total_unplanned_issues = run_jql(jira, total_unplanned_issues_jql)
    generic_aggregates['total_unplanned_issues'] = {'length': len(total_unplanned_issues), 'keys': get_jira_issue_keys(total_unplanned_issues), 'jql': total_unplanned_issues_jql}


    fancy_print_jql_info(generic_aggregates, "Generic Aggregates")

    # Get all epics
    # epics_jql = "{} {} {}".format(Filters.PROJECT.value.format(args.jira_project),
    #                               prepared_jira_lvl1_labels,
    #                               Filters.IN_ISSUETYPE.value.format(IssueType.EPIC.value))
    # prepared_jira_epic_keys = get_jira_issue_keys(run_jql(jira, epics_jql))


    # prepared_jira_lvl1_epics = get_jira_issue_keys(run_jql(jira, "project = OGST and issuetype = Epic AND created >= '{}' AND created <= '{}'".format(datetime.strftime(project_week[0], '%Y-%m-%d %H:%M'), datetime.strftime(project_week[1], '%Y-%m-%d %H:%M'))))

    for project_week in project_weeks.values():
        log.debug(f"Week from {project_week[0].strftime('%Y-%m-%d %H:%M')} to {project_week[1].strftime('%Y-%m-%d %H:%M')}")

        # ADDED
        total_added_issues_within_period_jql = "{} {} {} {} {}".format(Filters.PROJECT.value.format(args.jira_project),
                                                                 Filters.CREATED_DATETIME_FROM_TO.value.format(datetime.strftime(project_week[0], '%Y-%m-%d %H:%M'), datetime.strftime(project_week[1], '%Y-%m-%d %H:%M')),
                                                                 Filters.EPIC_LINK_IS_NOT_EMPTY.value,
                                                                 Filters.IN_ISSUETYPE.value.format("{}, {}, {}, {}".format(IssueType.STORY.value, IssueType.BUG.value, IssueType.TASK.value, IssueType.SPIKE.value)),
                                                                 prepared_jira_lvl1_labels)

        total_added_issues_within_period = run_jql(jira, total_added_issues_within_period_jql)
        week_aggregates['total_added_issues_within_period'] = {'length': len(total_added_issues_within_period), 'keys': get_jira_issue_keys(total_added_issues_within_period),'jql': total_added_issues_within_period_jql}

        # UPDATED
        total_updated_issues_within_period_jql = "{} {} {} {} {}".format(Filters.PROJECT.value.format(args.jira_project),
                                                                 Filters.UPDATED_DATETIME_FROM_TO.value.format(datetime.strftime(project_week[0], '%Y-%m-%d %H:%M'), datetime.strftime(project_week[1], '%Y-%m-%d %H:%M')),
                                                                 Filters.EPIC_LINK_IS_NOT_EMPTY.value,
                                                                 Filters.IN_ISSUETYPE.value.format("{}, {}, {}, {}".format(IssueType.STORY.value, IssueType.BUG.value, IssueType.TASK.value, IssueType.SPIKE.value)),
                                                                 prepared_jira_lvl1_labels)

        total_updated_issues_within_period = run_jql(jira, total_updated_issues_within_period_jql)
        week_aggregates['total_updated_issues_within_period'] = {'length': len(total_updated_issues_within_period), 'keys': get_jira_issue_keys(total_updated_issues_within_period),'jql': total_updated_issues_within_period_jql}

        # REJECTED
        total_rejected_issues_within_period_jql = "{} {} {} {} {} {}".format(Filters.PROJECT.value.format(args.jira_project),
                                                                 Filters.UPDATED_DATETIME_FROM_TO.value.format(datetime.strftime(project_week[0], '%Y-%m-%d %H:%M'), datetime.strftime(project_week[1], '%Y-%m-%d %H:%M')),
                                                                 Filters.EPIC_LINK_IS_NOT_EMPTY.value,
                                                                 Filters.IN_ISSUETYPE.value.format("{}, {}, {}, {}".format(IssueType.STORY.value, IssueType.BUG.value, IssueType.TASK.value, IssueType.SPIKE.value)),
                                                                 prepared_jira_lvl1_labels,
                                                                 Filters.REJECTED.value)
        total_rejected_issues_within_period = run_jql(jira, total_rejected_issues_within_period_jql)
        week_aggregates['total_rejected_issues_within_period'] = {'length': len(total_rejected_issues_within_period), 'keys': get_jira_issue_keys(total_rejected_issues_within_period),'jql': total_rejected_issues_within_period_jql}




        # Print in nice table
        fancy_print_jql_info(week_aggregates, f"Week from {project_week[0].strftime('%Y-%m-%d %H:%M')} to {project_week[1].strftime('%Y-%m-%d %H:%M')}")
        fancy_print_issue_history(total_updated_issues_within_period, f"Changes from {project_week[0].strftime('%Y-%m-%d %H:%M')} to {project_week[1].strftime('%Y-%m-%d %H:%M')}")