import logging
log = logging.getLogger('root')
from util.jql import JQLs, Filters, Status
from util.toolkit import jira_token_authenticate, run_jql, fancy_print_issue_timings, get_time_in_current_status, \
    get_time_between_distant_statuses, group_issues_by_assignee, seconds_to_hours
import ipdb, json

def exec(args):

    # Connect to Jira instance
    jira = jira_token_authenticate(args.jira_server_url, args.jira_auth_token)

    print("hello")

    log.info(len(run_jql(jira, "project = 'OGST' AND issuetype NOT IN ('Epic') AND created >= '2023-07-13 00:00'")))



