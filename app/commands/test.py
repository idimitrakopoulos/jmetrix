import logging
log = logging.getLogger('root')
from util.jql import Filters, Status
from util.toolkit import jira_token_authenticate, run_jql, fancy_print_issue_timings, get_time_in_current_status, \
    get_time_between_distant_statuses, group_issues_by_assignee, seconds_to_hours
import ipdb, json

def exec(args):

    # Connect to Jira instance
    jira = jira_token_authenticate(args.jira_server_url, args.jira_auth_token)

    log.info("may")

    log.info(len(run_jql(jira, "project = 'OGST' AND issuetype NOT IN ('Epic', 'Initiative') AND status in (closed, done) AND resolved >= '2023-05-01 00:00' AND resolved <= '2023-05-30 23:59' and labels not in (Dependency)")))

    log.info("june")

    log.info(len(run_jql(jira, "project = 'OGST' AND issuetype NOT IN ('Epic', 'Initiative') AND status in (closed, done) AND resolved >= '2023-06-01 00:00' AND resolved <= '2023-06-30 23:59' and labels not in (Dependency)")))

    log.info("sept")

    log.info(len(run_jql(jira, "project = 'OGST' AND issuetype NOT IN ('Epic', 'Initiative') AND status in (closed, done) AND resolved >= '2023-09-01 00:00' AND resolved <= '2023-09-30 23:59' and labels not in (Dependency)")))




