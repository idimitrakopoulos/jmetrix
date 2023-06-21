#!/usr/bin/env python3
import util.logger as logger
log = logger.setup_custom_logger('root')
import os
from util.jira_obj import PBIMetricCollection, CompositePBIMetricCollection, TPRMetricCollection
from prometheus_client import start_http_server
from util.toolkit import jira_authenticate
from util.jql import Status, IssueType, TimeValue
import ipdb
import time

# Environment variables
jira_url = os.environ['jira_url']
jira_username = os.environ['jira_username']
jira_password = os.environ['jira_password']
wit_bind_address = os.environ['wit_bind_address']
wit_port = int(os.environ['PORT'])
wit_update_interval_sec = int(os.environ['wit_update_interval_sec'])
jql_project = os.environ['jql_project']




if __name__ == '__main__':
    # Connect to Jira instance
    jira = jira_authenticate(jira_url, jira_username, jira_password)

    # Start up the server to expose the metrics.
    log.debug("Starting up server at: {}:{}".format(str(wit_bind_address), str(wit_port)))
    start_http_server(wit_port if wit_port != "" else 9000, wit_bind_address if wit_bind_address != "" else "localhost")

    # Stories
    story_metrics = PBIMetricCollection(jira, jql_project, IssueType.STORY.value, Status.CLOSED.value, TimeValue.MINUS_1_MONTH.value)
    story_metrics.register_prometheus_metrics()

    # Bugs
    bug_metrics = PBIMetricCollection(jira, jql_project, IssueType.BUG.value, Status.CLOSED.value, TimeValue.MINUS_1_MONTH.value)
    bug_metrics.register_prometheus_metrics()

    # Development Tasks
    development_task_metrics = PBIMetricCollection(jira, jql_project, IssueType.DEVELOPMENT_TASK.value, Status.CLOSED.value, TimeValue.MINUS_1_MONTH.value)
    development_task_metrics.register_prometheus_metrics()

    # PBIs
    pbi_metrics = CompositePBIMetricCollection([story_metrics, bug_metrics, development_task_metrics])
    pbi_metrics.register_prometheus_metrics()

    # Throughput Requests
    throughput_request_metrics = TPRMetricCollection(jira, jql_project, IssueType.THROUGHPUT_REQUEST.value, Status.CLOSED.value, TimeValue.MINUS_1_MONTH.value)
    throughput_request_metrics.register_prometheus_metrics()


    while True:
        # Sleep before reloading metrics
        time.sleep(wit_update_interval_sec)
        log.debug("Refreshing data from Jira NOW....")

        # Refresh metrics
        story_metrics.refresh_prometheus_metrics()
        bug_metrics.refresh_prometheus_metrics()
        development_task_metrics.refresh_prometheus_metrics()
        pbi_metrics.refresh_prometheus_metrics()
        throughput_request_metrics.refresh_prometheus_metrics()
