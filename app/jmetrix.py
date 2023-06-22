#!/usr/bin/env python3
import util.logger as logger
import argparse
log = logger.setup_custom_logger('root')
import os
from util.jira_obj import PBIMetricCollection, CompositePBIMetricCollection, TPRMetricCollection
from prometheus_client import start_http_server
from util.toolkit import jira_token_authenticate, get_time_in_status
from util.jql import Status, IssueType, TimeValue
import ipdb
import time

if __name__ == '__main__':
    # Instantiate the parser
    parser = argparse.ArgumentParser(prog='jmetrix', description='A CLI tool for Jira metrics', epilog='(c) 2012-present Iason Dimitrakopoulos - idimitrakopoulos@gmail.com')
    requiredArgs= parser.add_argument_group('required arguments')
    requiredArgs.add_argument('-u', '--url', dest='jira_server_url', type=str, help='The Jira server base URL (e.g. https://xxxx.xxx.xxx)', required=True)
    requiredArgs.add_argument('-t', '--token', dest='jira_auth_token', type=str, help='The Jira authentication token', required=True)
    requiredArgs.add_argument('-j', '--jql', dest='jira_jql', type=str, help='The JQL query you want to get metrics for.', required=True)

    args = parser.parse_args()

    # Connect to Jira instance
    jira = jira_token_authenticate(args.jira_server_url, args.jira_auth_token)

    jql_results = jira.search_issues(args.jira_jql, expand='changelog')

    for issue in jql_results:
        print('{}: {}'.format(issue.key, issue.fields.summary))
        # print(dir(issue.changelog))
        # for history in reversed(issue.changelog.histories):
        #     for item in history.items:
        #         print(item.field)
        print(sum(get_time_in_status(Status.IN_PROGRESS.value, issue.changelog)))

    # # Start up the server to expose the metrics.
    # log.debug("Starting up server at: {}:{}".format(str(wit_bind_address), str(wit_port)))
    # start_http_server(wit_port if wit_port != "" else 9000, wit_bind_address if wit_bind_address != "" else "localhost")
    #
    # # Stories
    # story_metrics = PBIMetricCollection(jira, jql_project, IssueType.STORY.value, Status.CLOSED.value, TimeValue.MINUS_1_MONTH.value)
    # story_metrics.register_prometheus_metrics()
    #
    # # Bugs
    # bug_metrics = PBIMetricCollection(jira, jql_project, IssueType.BUG.value, Status.CLOSED.value, TimeValue.MINUS_1_MONTH.value)
    # bug_metrics.register_prometheus_metrics()
    #
    # # Development Tasks
    # development_task_metrics = PBIMetricCollection(jira, jql_project, IssueType.DEVELOPMENT_TASK.value, Status.CLOSED.value, TimeValue.MINUS_1_MONTH.value)
    # development_task_metrics.register_prometheus_metrics()
    #
    # # PBIs
    # pbi_metrics = CompositePBIMetricCollection([story_metrics, bug_metrics, development_task_metrics])
    # pbi_metrics.register_prometheus_metrics()
    #
    # # Throughput Requests
    # throughput_request_metrics = TPRMetricCollection(jira, jql_project, IssueType.THROUGHPUT_REQUEST.value, Status.CLOSED.value, TimeValue.MINUS_1_MONTH.value)
    # throughput_request_metrics.register_prometheus_metrics()
    #
    #
    # while True:
    #     # Sleep before reloading metrics
    #     time.sleep(wit_update_interval_sec)
    #     log.debug("Refreshing data from Jira NOW....")
    #
    #     # Refresh metrics
    #     story_metrics.refresh_prometheus_metrics()
    #     bug_metrics.refresh_prometheus_metrics()
    #     development_task_metrics.refresh_prometheus_metrics()
    #     pbi_metrics.refresh_prometheus_metrics()
    #     throughput_request_metrics.refresh_prometheus_metrics()
