#!/usr/bin/env python3
import util.logger as logger
import argparse
log = logger.setup_custom_logger('root')
from util.toolkit import jira_token_authenticate, get_time_in_status, get_time_from_creation_to_extreme_status, get_time_between_extreme_statuses, get_time_in_initial_status
from util.jql import Status
import ipdb, json

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

    issues = dict()

    for issue in jql_results:
        print('{}: {}'.format(jira.server_url + "/browse/"+ issue.key, issue.fields.summary))
        values = dict()
        issues[issue.key] = values

        issues[issue.key]['key'] = issue.key

        issues[issue.key]['fields'] = dict()
        issues[issue.key]['fields']['url'] = jira.server_url + "/browse/"+ issue.key
        issues[issue.key]['fields']['summary'] = issue.fields.summary
        issues[issue.key]['fields']['status'] = issue.fields.status.name

        issues[issue.key]['aggregates'] = dict()
        issues[issue.key]['aggregates']['t_lead'] = get_time_from_creation_to_extreme_status(issue.fields.created, Status.DONE.value, issue.changelog)
        issues[issue.key]['aggregates']['t_cycle'] = get_time_between_extreme_statuses(Status.READY_TO_START.value, Status.DONE.value, issue.changelog)

        issues[issue.key]['t_backlog'] = sum(get_time_in_initial_status(Status.BACKLOG.value, issue.changelog, issue.fields.created))
        issues[issue.key]['t_ready_for_analysis'] = sum(get_time_in_status(Status.READY_FOR_ANALYSIS.value, issue.changelog))
        issues[issue.key]['t_in_analysis'] = sum(get_time_in_status(Status.IN_ANALYSIS.value, issue.changelog))
        issues[issue.key]['t_ready_for_uxd'] = sum(get_time_in_status(Status.READY_FOR_UXD.value, issue.changelog))
        issues[issue.key]['t_in_uxd'] = sum(get_time_in_status(Status.IN_UXD.value, issue.changelog))
        issues[issue.key]['t_ready_for_tech_review'] = sum(get_time_in_status(Status.READY_FOR_TECH_REVIEW.value, issue.changelog))
        issues[issue.key]['t_in_tech_review'] = sum(get_time_in_status(Status.IN_TECH_REVIEW.value, issue.changelog))
        issues[issue.key]['t_ready_for_refinement'] = sum(get_time_in_status(Status.READY_FOR_REFINEMENT.value, issue.changelog))
        issues[issue.key]['t_in_refinement'] = sum(get_time_in_status(Status.IN_REFINEMENT.value, issue.changelog))
        issues[issue.key]['t_ready_for_delivery'] = sum(get_time_in_status(Status.READY_FOR_DELIVERY.value, issue.changelog))
        issues[issue.key]['t_ready_to_start'] = sum(get_time_in_status(Status.READY_TO_START.value, issue.changelog))
        issues[issue.key]['t_in_progress'] = sum(get_time_in_status(Status.IN_PROGRESS.value, issue.changelog))
        issues[issue.key]['t_ready_for_code_review'] = sum(get_time_in_status(Status.READY_FOR_CODE_REVIEW.value, issue.changelog))
        issues[issue.key]['t_in_code_review'] = sum(get_time_in_status(Status.IN_CODE_REVIEW.value, issue.changelog))
        issues[issue.key]['t_ready_for_testing'] = sum(get_time_in_status(Status.READY_FOR_TESTING.value, issue.changelog))
        issues[issue.key]['t_in_testing'] = sum(get_time_in_status(Status.IN_TESTING.value, issue.changelog))
        issues[issue.key]['t_ready_for_sign_off'] = sum(get_time_in_status(Status.READY_FOR_SIGN_OFF.value, issue.changelog))
        issues[issue.key]['t_done'] = sum(get_time_in_status(Status.DONE.value, issue.changelog))

        # Process Efficiency = (Hands-on time / Total lead-time) * 100
        hands_off_time = [issues[issue.key]['t_ready_for_analysis'],
                          issues[issue.key]['t_ready_for_uxd'],
                          issues[issue.key]['t_ready_for_tech_review'],
                          issues[issue.key]['t_ready_for_refinement'],
                          issues[issue.key]['t_ready_for_delivery'],
                          issues[issue.key]['t_ready_to_start'],
                          issues[issue.key]['t_ready_for_code_review'] ,
                          issues[issue.key]['t_ready_for_testing'],
                          issues[issue.key]['t_ready_for_sign_off']]

        # If lead time is zero then the issue was worked off normal working hours so it should be counted as efficient
        issues[issue.key]['process_efficiency'] = ((issues[issue.key]['aggregates']['t_lead'] - sum(hands_off_time)) / issues[issue.key]['aggregates']['t_lead']) * 100 if issues[issue.key]['aggregates']['t_lead'] else -1

        log.debug(json.dumps(issues[issue.key], indent=4))


