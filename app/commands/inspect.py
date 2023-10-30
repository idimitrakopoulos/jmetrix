import logging
log = logging.getLogger('root')
from util.jql import Status
from collections import Counter
import ipdb, json
from operator import itemgetter
from util.toolkit import jira_token_authenticate, get_time_in_status, get_time_from_creation_to_extreme_status, \
    get_time_between_extreme_statuses, get_time_in_initial_status, get_time_in_current_status, run_jql, \
    get_time_from_creation_to_now, seconds_to_hours, add_worktimes_and_durations


def exec(args):

    # Connect to Jira instance
    jira = jira_token_authenticate(args.jira_server_url, args.jira_auth_token)

    # Execute JQL
    jql_results = run_jql(jira, args.jira_jql)
    log.debug("Got '{}' result(s) from JQL execution".format(len(jql_results)))
    if len(jql_results) == 0:
        log.info("Exiting as there are zero results to process")
        exit(0)

    from rich.console import Console
    from rich.table import Table

    table = Table(title=args.jira_jql)

    table.add_column("Key", justify="left", style="bright_yellow", no_wrap=True)
    table.add_column("Status", justify="left", style="white", no_wrap=True)
    table.add_column("Est(h)", justify="left", style="white")
    table.add_column("Anal", justify="left", style="white")
    table.add_column("UXD", justify="left", style="white")
    table.add_column("TRev", justify="left", style="white")
    table.add_column("Dev", justify="left", style="white")
    table.add_column("Test", justify="left", style="white")

    issues = dict()
    print('key;type;labels;original_estimate;created;updated;t_backlog;t_ready_for_analysis;t_in_analysis;t_ready_for_uxd;t_in_uxd;t_ready_for_tech_review;t_in_tech_review;t_ready_for_refinement;t_in_refinement;t_ready_for_delivery;t_ready_to_start;t_in_progress;t_ready_for_code_review;t_in_code_review;t_ready_for_testing;t_in_testing;t_ready_for_sign_off;t_done;t_current_status;t_overall;lead_time;cycle_time')

    for issue in jql_results:
        log.debug('{}: {}'.format(jira.server_url + "/browse/"+ issue.key, issue.fields.summary))
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
        issues[issue.key]['fields']['created'] = issue.fields.created
        issues[issue.key]['fields']['updated'] = issue.fields.updated



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
        issues[issue.key]['t_overall'] = get_time_from_creation_to_now(issue.fields.created)

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

        issues[issue.key]['aggregates']['t_discovery_analysis'] = add_worktimes_and_durations([Counter(issues[issue.key]['t_ready_for_analysis']),
                                                                   Counter(issues[issue.key]['t_in_analysis'])])

        issues[issue.key]['aggregates']['t_discovery_uxd'] = add_worktimes_and_durations([Counter(issues[issue.key]['t_ready_for_uxd']),
                                                              Counter(issues[issue.key]['t_in_uxd'])])

        issues[issue.key]['aggregates']['t_discovery_tech_review'] = add_worktimes_and_durations([Counter(issues[issue.key]['t_ready_for_tech_review']),
                                                                      Counter(issues[issue.key]['t_in_tech_review']),
                                                                      Counter(issues[issue.key]['t_ready_for_refinement']),
                                                                      Counter(issues[issue.key]['t_in_refinement'])])

        issues[issue.key]['aggregates']['t_delivery_dev'] = add_worktimes_and_durations([Counter(issues[issue.key]['t_in_progress']),
                                                                 Counter(issues[issue.key]['t_ready_for_code_review']),
                                                                 Counter(issues[issue.key]['t_in_code_review'])])

        issues[issue.key]['aggregates']['t_delivery_test'] = add_worktimes_and_durations([Counter(issues[issue.key]['t_ready_for_testing']),
                                                                 Counter(issues[issue.key]['t_in_testing']),
                                                                 Counter(issues[issue.key]['t_ready_for_sign_off'])])

        # If lead time is zero then the issue was worked off normal working hours so it should be counted as efficient
        issues[issue.key]['flow_efficiency_pct'] = round(((issues[issue.key]['aggregates']['t_lead']['duration'] - sum(t_idle)) / issues[issue.key]['aggregates']['t_lead']['duration']) * 100 if issues[issue.key]['aggregates']['t_lead']['duration'] else -1, 2)

        # Sizing Efficiency = (Size estimated / cycle time) * 100
        issues[issue.key]['sizing_accuracy_pct'] = round((issues[issue.key]['fields']['original_estimate'] / issues[issue.key]['aggregates']['t_cycle']['worktime']) * 100 if issues[issue.key]['fields']['original_estimate'] and issues[issue.key]['aggregates']['t_cycle']['worktime'] else -1, 2)

        if issues[issue.key]['fields']['original_estimate']:
            table.add_row(issue.key,
                          issues[issue.key]['fields']['status'],
                          "{}h".format(str(seconds_to_hours(issues[issue.key]['fields']['original_estimate']))),
                          "0%" if not issues[issue.key]['aggregates']['t_discovery_analysis'] else "{}%".format(str(round((issues[issue.key]['aggregates']['t_discovery_analysis']['worktime']/issues[issue.key]['t_overall']['worktime'])*100, 2))),
                          "0%" if not issues[issue.key]['aggregates']['t_discovery_uxd'] else "{}%".format(str(round((issues[issue.key]['aggregates']['t_discovery_uxd']['worktime']/issues[issue.key]['t_overall']['worktime'])*100, 2))),
                          "0%" if not issues[issue.key]['aggregates']['t_discovery_tech_review'] else "{}%".format(str(round((issues[issue.key]['aggregates']['t_discovery_tech_review']['worktime']/issues[issue.key]['t_overall']['worktime'])*100, 2))),
                          "0%" if not issues[issue.key]['aggregates']['t_delivery_dev'] else "{}%".format(str(round((issues[issue.key]['aggregates']['t_delivery_dev']['worktime']/issues[issue.key]['t_overall']['worktime'])*100, 2))),
                          "0%" if not issues[issue.key]['aggregates']['t_delivery_test'] else "{}%".format(str(round((issues[issue.key]['aggregates']['t_delivery_test']['worktime']/issues[issue.key]['t_overall']['worktime'])*100, 2))),
                          )

        else:
            table.add_row(issue.key, issues[issue.key]['fields']['status'], "n/a",  "-%", "-%", "-%", "-%", "-%")

        if args.csv:
            # ipdb.set_trace()
            print("{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};".format(
                                        issues[issue.key]['key'],
                                        issues[issue.key]['fields']['type'],
                                        ','.join(issues[issue.key]['fields']['labels']),
                                        issues[issue.key]['fields']['original_estimate'],
                                        issues[issue.key]['fields']['created'],
                                        issues[issue.key]['fields']['updated'],
                                        issues[issue.key]['t_backlog']['worktime'],
                                        issues[issue.key]['t_ready_for_analysis']['worktime'],
                                        issues[issue.key]['t_in_analysis']['worktime'],
                                        issues[issue.key]['t_ready_for_uxd']['worktime'],
                                        issues[issue.key]['t_in_uxd']['worktime'],
                                        issues[issue.key]['t_ready_for_tech_review']['worktime'],
                                        issues[issue.key]['t_in_tech_review']['worktime'],
                                        issues[issue.key]['t_ready_for_refinement']['worktime'],
                                        issues[issue.key]['t_in_refinement']['worktime'],
                                        issues[issue.key]['t_ready_for_delivery']['worktime'],
                                        issues[issue.key]['t_ready_to_start']['worktime'],
                                        issues[issue.key]['t_in_progress']['worktime'],
                                        issues[issue.key]['t_ready_for_code_review']['worktime'],
                                        issues[issue.key]['t_in_code_review']['worktime'],
                                        issues[issue.key]['t_ready_for_testing']['worktime'],
                                        issues[issue.key]['t_in_testing']['worktime'],
                                        issues[issue.key]['t_ready_for_sign_off']['worktime'],
                                        issues[issue.key]['t_done']['worktime'],
                                        issues[issue.key]['t_current_status']['worktime'],
                                        issues[issue.key]['t_overall']['worktime'],
                                        issues[issue.key]['aggregates']['t_lead']['worktime'],
                                        issues[issue.key]['aggregates']['t_cycle']['worktime']
                                              ))
        else:
            log.debug(json.dumps(issues[issue.key], indent=4))

    max_t_lead = sorted(issues.items(), key=lambda kv: kv[1]['aggregates']['t_lead']['duration'], reverse=True)
    max_t_cycle = sorted(issues.items(), key=lambda kv: kv[1]['aggregates']['t_cycle']['duration'], reverse=True)
    max_t_in_same_status = sorted(issues.items(), key=lambda kv: kv[1]['t_current_status']['worktime'], reverse=True)
    min_flow_efficiency_pct = sorted(issues.items(), key=lambda kv: kv[1]['flow_efficiency_pct'], reverse=False)
    min_sizing_accuracy_pct = sorted(issues.items(), key=lambda kv: kv[1]['sizing_accuracy_pct'], reverse=False)

    # log.debug(json.dumps(min_flow_efficiency_pct, indent=4))
    # print("------------------------------------------------")
    # log.debug(json.dumps(min_sizing_accuracy_pct, indent=4))

    if not args.csv:
        console = Console()
        console.print(table)

