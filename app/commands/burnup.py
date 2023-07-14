import logging
log = logging.getLogger('root')
from util.jql import JQLs, Filters
from util.toolkit import jira_token_authenticate, run_jql, print_issue_summary, print_issue_history

def exec(args):

    # Connect to Jira instance
    jira = jira_token_authenticate(args.jira_server_url, args.jira_auth_token)

    # Add project to JQL
    jql_project = JQLs.JQL_BURNUP.value.format(args.jira_project)

    # Add identifier to JQL
    jql_project_identifier = "{} {}".format(jql_project, Filters.LABEL.value.format(args.jira_label))
    if (args.jira_extra_label):
        jql_project_identifier = "{} {}".format(jql_project_identifier, Filters.LABEL.value.format(args.jira_extra_label))


    # Add released filter
    jql_project_identifier_released = "{} {}".format(jql_project_identifier, Filters.RELEASED.value)

    # Add rejected filter
    jql_project_identifier_rejected = "{} {}".format(jql_project_identifier, Filters.REJECTED.value)

    # Add in flight filter
    jql_project_identifier_inflight = "{} {}".format(jql_project_identifier, Filters.IN_FLIGHT.value)

    # Add dates from/to
    jql_project_identifier_dates = "{} {}".format(jql_project_identifier, Filters.CREATED_DATES_FROM_TO.value.format(args.date_from, args.date_to))

    # Add dates to released filter
    jql_project_identifier_released_dates = "{} {}".format(jql_project_identifier_released, Filters.RESOLVED_DATES_FROM_TO.value.format(args.date_from, args.date_to))

    # Add dates to rejected filter
    jql_project_identifier_rejected_dates = "{} {}".format(jql_project_identifier_rejected, Filters.CREATED_DATES_FROM_TO.value.format(args.date_from, args.date_to))

    # Add dates to in flight filter
    jql_project_identifier_in_flight_dates = "{} {}".format(jql_project_identifier_inflight, Filters.NOT_CREATED_DATES_FROM_TO.value.format(args.date_from))



    # TOTAL ISSUES
    jql_results = run_jql(jira, jql_project_identifier)
    log.info("Total issues: {}".format(len(jql_results)))

    # TOTAL ISSUES RELEASED
    jql_results = run_jql(jira, jql_project_identifier_released)
    log.info("Total issues released: {}".format(len(jql_results)))

    # TOTAL ISSUES CREATED BETWEEN DATES
    jql_results = run_jql(jira, jql_project_identifier_dates)
    log.info("Total issues created between {} and {}: {}".format(args.date_from, args.date_to, len(jql_results)))
    print_issue_summary(jql_results)

    # TOTAL ISSUES RELEASED BETWEEN DATES
    jql_results = run_jql(jira, jql_project_identifier_released_dates)
    log.info("Total issues released between {} and {}: {}".format(args.date_from, args.date_to, len(jql_results)))

    # TOTAL ISSUES REJECTED BETWEEN DATES
    jql_results = run_jql(jira, jql_project_identifier_rejected_dates)
    log.info("Total issues rejected between {} and {}: {}".format(args.date_from, args.date_to, len(jql_results)))

    # TOTAL ISSUES IN FLIGHT BETWEEN DATES
    jql_results = run_jql(jira, jql_project_identifier_in_flight_dates)
    log.info("Total issues in flight NOT created after {}: {}".format(args.date_from, len(jql_results)))
    print_issue_history(jql_results)