import logging
log = logging.getLogger('root')
from util.jql import JQLs, Filters, Status
from util.toolkit import jira_token_authenticate, run_jql, fancy_print_issue_timings, get_time_in_current_status, \
    get_time_between_distant_statuses, group_issues_by_assignee, seconds_to_hours
import ipdb, json

def get_daily_metrics(raw_issues):
    issues = dict()
    for issue in raw_issues:
        # print('{}: {}'.format(issue.key, issue.fields.summary))
        values = dict()

        issues[issue.key] = values

        issues[issue.key]['key'] = issue.key

        issues[issue.key]['fields'] = dict()
        issues[issue.key]['fields']['summary'] = issue.fields.summary
        issues[issue.key]['fields']['assignee'] = None if isinstance(issue.fields.assignee, type(None)) else issue.fields.assignee.displayName
        issues[issue.key]['fields']['status'] = issue.fields.status.name
        issues[issue.key]['fields']['type'] = issue.fields.issuetype.name
        issues[issue.key]['fields']['labels'] = issue.fields.labels
        issues[issue.key]['fields']['original_estimate'] = issue.fields.timeoriginalestimate

        issues[issue.key]['t_current_status'] = get_time_in_current_status(issues[issue.key]['fields']['status'], issue.changelog)
        issues[issue.key]['t_overall'] = get_time_in_current_status(issues[issue.key]['fields']['status'], issue.changelog) if Status.IN_PROGRESS.value == issue.fields.status.name else get_time_between_distant_statuses(Status.IN_PROGRESS.value, issue.fields.status.name, issue.changelog)
        issues[issue.key]['pct_consumed'] = -1 if isinstance(issues[issue.key]['fields']['original_estimate'], type(None)) else (issues[issue.key]['t_overall']['worktime'] / issues[issue.key]['fields']['original_estimate'])*100

    return issues

def print_daily_assignee_status(raw_issues):
    for assignee, issues in group_issues_by_assignee(raw_issues).items():
      print(f"{assignee}")
      for issue in issues:
        if (assignee is None and not issue['fields']['status'].startswith("Ready")) \
                or assignee is not None and issue['fields']['status'].startswith("Ready"):
            print("  * {} | {} | {}h".format(issue['key'], issue['fields']['status'], seconds_to_hours(issue['t_current_status']['worktime'])))
        else:
            print("    {} | {} | {}h".format(issue['key'], issue['fields']['status'], seconds_to_hours(issue['t_current_status']['worktime'])))

def print_header(text):
    from rich import print
    from rich.panel import Panel
    from rich.text import Text
    panel = Panel(Text(text, style="bold white"), border_style="bright_yellow")
    print(panel)

def exec(args):

    # Connect to Jira instance
    jira = jira_token_authenticate(args.jira_server_url, args.jira_auth_token)


    # Add project to JQL
    jql_project = JQLs.JQL_PROJECT.value.format(args.jira_project)

    # Delivery board
    jql_project_delivery_in_flight = "{} {}".format(jql_project, Filters.DELIVERY_IN_FLIGHT.value)
    delivery_issues_in_flight = run_jql(jira, jql_project_delivery_in_flight)
    delivery_issue_metrics = get_daily_metrics(delivery_issues_in_flight)

    print_header("Delivery board items")
    fancy_print_issue_timings(delivery_issue_metrics, jql_project_delivery_in_flight)
    print_daily_assignee_status(delivery_issue_metrics)

    # Discovery board
    if (args.discovery):
        jql_project_discovery_in_flight = "{} {}".format(jql_project, Filters.DISCOVERY_IN_FLIGHT.value)
        discovery_issues_in_flight = run_jql(jira, jql_project_discovery_in_flight)
        discovery_issue_metrics = get_daily_metrics(discovery_issues_in_flight)

        print_header("Discovery board items")
        fancy_print_issue_timings(discovery_issue_metrics, jql_project_discovery_in_flight)
        print_daily_assignee_status(discovery_issue_metrics)


    # log.debug(json.dumps(issues, indent=4))

    # max_t_in_same_status = sorted(issues.items(), key=lambda kv: kv[1]['t_current_status']['worktime'], reverse=True)
    # max_pct_overdue = sorted(issues.items(), key=lambda kv: kv[1]['pct_overdue'], reverse=True)

    # fancy_print_issue_assignees(group_issues_by_assignee(issues))






