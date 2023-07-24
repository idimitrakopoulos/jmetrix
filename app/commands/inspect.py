import logging
log = logging.getLogger('root')
from util.jql import Status
from collections import Counter
import ipdb, json
from operator import itemgetter
from util.toolkit import jira_token_authenticate, get_time_in_status, get_time_from_creation_to_extreme_status, \
    get_time_between_extreme_statuses, get_time_in_initial_status, get_time_in_current_status, run_jql

def exec(args):

    # Connect to Jira instance
    jira = jira_token_authenticate(args.jira_server_url, args.jira_auth_token)

    # JQL append required filters for this command to work
    # jql = "{} AND status in ({},{})".format(args.jira_jql, Status.DONE.value, Status.CLOSED.value)
    # log.info("Executing JQL after modification '{}'".format(jql))

    # Execute JQL
    jql_results = run_jql(jira, args.jira_jql)
    log.debug("Got '{}' result(s) from JQL execution".format(len(jql_results)))
    if len(jql_results) == 0:
        log.info("Exiting as there are zero results to process")
        exit(0)

    issues = dict()

    for issue in jql_results:
        print('{}: {}'.format(jira.server_url + "/browse/"+ issue.key, issue.fields.summary))
        values = dict()
        issues[issue.key] = values

        issues[issue.key]['key'] = issue.key

        issues[issue.key]['fields'] = dict()
        issues[issue.key]['fields']['url'] = jira.server_url + "/browse/"+ issue.key
        issues[issue.key]['fields']['summary'] = issue.fields.summary
        issues[issue.key]['fields']['assignee'] = None if isinstance(issue.fields.assignee, type(None)) else issue.fields.assignee.displayName
        issues[issue.key]['fields']['status'] = issue.fields.status.name
        issues[issue.key]['fields']['type'] = issue.fields.issuetype.name
        issues[issue.key]['fields']['labels'] = issue.fields.labels
        issues[issue.key]['fields']['original_estimate'] = issue.fields.timeoriginalestimate

        issues[issue.key]['t_backlog'] = get_time_in_initial_status(Status.BACKLOG.value, issue.changelog, issue.fields.created)
        issues[issue.key]['t_ready_for_analysis'] = get_time_in_status(Status.READY_FOR_ANALYSIS.value, issue.changelog)
        issues[issue.key]['t_in_analysis'] = get_time_in_status(Status.IN_ANALYSIS.value, issue.changelog)
        issues[issue.key]['t_ready_for_uxd'] = get_time_in_status(Status.READY_FOR_UXD.value, issue.changelog)
        issues[issue.key]['t_in_uxd'] = get_time_in_status(Status.IN_UXD.value, issue.changelog)
        issues[issue.key]['t_ready_for_tech_review'] = get_time_in_status(Status.READY_FOR_TECH_REVIEW.value, issue.changelog)
        issues[issue.key]['t_in_tech_review'] = get_time_in_status(Status.IN_TECH_REVIEW.value, issue.changelog)
        issues[issue.key]['t_ready_for_refinement'] = get_time_in_status(Status.READY_FOR_REFINEMENT.value, issue.changelog)
        issues[issue.key]['t_in_refinement'] = get_time_in_status(Status.IN_REFINEMENT.value, issue.changelog)
        issues[issue.key]['t_ready_for_delivery'] = get_time_in_status(Status.READY_FOR_DELIVERY.value, issue.changelog)

        issues[issue.key]['t_ready_to_start'] = get_time_in_status(Status.READY_TO_START.value, issue.changelog)
        issues[issue.key]['t_in_progress'] = get_time_in_status(Status.IN_PROGRESS.value, issue.changelog)
        issues[issue.key]['t_ready_for_code_review'] = get_time_in_status(Status.READY_FOR_CODE_REVIEW.value, issue.changelog)
        issues[issue.key]['t_in_code_review'] = get_time_in_status(Status.IN_CODE_REVIEW.value, issue.changelog)
        issues[issue.key]['t_ready_for_testing'] = get_time_in_status(Status.READY_FOR_TESTING.value, issue.changelog)
        issues[issue.key]['t_in_testing'] = get_time_in_status(Status.IN_TESTING.value, issue.changelog)
        issues[issue.key]['t_ready_for_sign_off'] = get_time_in_status(Status.READY_FOR_SIGN_OFF.value, issue.changelog)
        issues[issue.key]['t_done'] = get_time_in_status(Status.DONE.value, issue.changelog)
        issues[issue.key]['t_current_status'] = get_time_in_current_status(issues[issue.key]['fields']['status'], issue.changelog)

        # Flow Efficiency = (Hands-on time / Total lead-time) * 100
        t_idle = [issues[issue.key]['t_ready_for_analysis']['duration'],
                          issues[issue.key]['t_ready_for_uxd']['duration'],
                          issues[issue.key]['t_ready_for_tech_review']['duration'],
                          issues[issue.key]['t_ready_for_refinement']['duration'],
                          issues[issue.key]['t_ready_for_delivery']['duration'],
                          issues[issue.key]['t_ready_to_start']['duration'],
                          issues[issue.key]['t_ready_for_code_review']['duration'],
                          issues[issue.key]['t_ready_for_testing']['duration'],
                          issues[issue.key]['t_ready_for_sign_off']['duration']]

        issues[issue.key]['aggregates'] = dict()
        issues[issue.key]['aggregates']['t_lead'] = get_time_from_creation_to_extreme_status(issue.fields.created, Status.DONE.value, issue.changelog)
        issues[issue.key]['aggregates']['t_cycle'] = get_time_between_extreme_statuses(Status.READY_TO_START.value, Status.DONE.value, issue.changelog)

        issues[issue.key]['aggregates']['t_discovery_analysis'] = dict(Counter(issues[issue.key]['t_ready_for_analysis']) +
                                                                   Counter(issues[issue.key]['t_in_analysis']))

        issues[issue.key]['aggregates']['t_discovery_uxd'] = dict(Counter(issues[issue.key]['t_ready_for_uxd']) +
                                                              Counter(issues[issue.key]['t_in_uxd']))

        issues[issue.key]['aggregates']['t_discovery_tech_review'] = dict(Counter(issues[issue.key]['t_ready_for_tech_review']) +
                                                                      Counter(issues[issue.key]['t_in_tech_review']) +
                                                                      Counter(issues[issue.key]['t_ready_for_refinement']) +
                                                                      Counter(issues[issue.key]['t_in_refinement']))

        issues[issue.key]['aggregates']['t_delivery_dev'] = dict(Counter(issues[issue.key]['t_in_progress']) +
                                                                 Counter(issues[issue.key]['t_ready_for_code_review']) +
                                                                 Counter(issues[issue.key]['t_in_code_review']))

        issues[issue.key]['aggregates']['t_delivery_test'] = dict(Counter(issues[issue.key]['t_ready_for_testing']) +
                                                                 Counter(issues[issue.key]['t_in_testing']) +
                                                                 Counter(issues[issue.key]['t_ready_for_sign_off']))

        # If lead time is zero then the issue was worked off normal working hours so it should be counted as efficient
        issues[issue.key]['flow_efficiency_pct'] = round(((issues[issue.key]['aggregates']['t_lead']['duration'] - sum(t_idle)) / issues[issue.key]['aggregates']['t_lead']['duration']) * 100 if issues[issue.key]['aggregates']['t_lead']['duration'] else -1, 2)

        # Sizing Efficiency = (Size estimated / cycle time) * 100
        issues[issue.key]['sizing_accuracy_pct'] = round((issues[issue.key]['fields']['original_estimate'] / issues[issue.key]['aggregates']['t_cycle']['worktime']) * 100 if issues[issue.key]['fields']['original_estimate'] and issues[issue.key]['aggregates']['t_cycle']['worktime'] else -1, 2)

        log.debug(json.dumps(issues[issue.key], indent=4))

    max_t_lead = sorted(issues.items(), key=lambda kv: kv[1]['aggregates']['t_lead']['duration'], reverse=True)
    max_t_cycle = sorted(issues.items(), key=lambda kv: kv[1]['aggregates']['t_cycle']['duration'], reverse=True)
    max_t_in_same_status = sorted(issues.items(), key=lambda kv: kv[1]['t_current_status']['worktime'], reverse=True)
    min_flow_efficiency_pct = sorted(issues.items(), key=lambda kv: kv[1]['flow_efficiency_pct'], reverse=False)
    min_sizing_accuracy_pct = sorted(issues.items(), key=lambda kv: kv[1]['sizing_accuracy_pct'], reverse=False)

    # log.debug(json.dumps(min_flow_efficiency_pct, indent=4))
    # print("------------------------------------------------")
    # log.debug(json.dumps(min_sizing_accuracy_pct, indent=4))
