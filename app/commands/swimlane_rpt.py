import logging
log = logging.getLogger('root')
from util.jql import JQLs, Filters
from util.toolkit import jira_token_authenticate, run_jql, fancy_print_issue_summary, fancy_print_issue_history, fancy_print_jql_info

def exec(args):

    # import plotly.express as px
    # import pandas as pd
    #
    # df = pd.DataFrame(dict(
    #     x=[1, 3, 6, 4],
    #     y=[1, 2, 3, 4]
    # ))
    #
    # df2 = pd.DataFrame(dict(
    #     x=[1, 3, 6, 4],
    #     y=[1, 2, 3, 4]
    # ))
    #
    # fig = px.line(df, x="x", y="y", color_discrete_sequence=['blue'])
    #
    # fig = px.line(df2, x="x", y="y", color_discrete_sequence=['red'])
    #
    # # df = df.sort_values(by="x")
    # # fig = px.line(df, x="x", y="y", title="Sorted Input")
    # # fig.show()
    #
    # import plotly.graph_objects as go
    #
    # # Create traces
    # fig = go.Figure()
    # # fig.add_trace(go.Scatter(df, mode='lines', name='predicted'))
    # fig.add_trace(go.Scatter(x=[3.7, 7.4, 11.1, 14.8, 18.5, 22.2, 25.9, 29.6], y=[3, 4, 11, 1], mode='lines', name='optimistic', marker = {'color' : 'red'}))
    #
    # log.info("writing image")
    # fig.write_image("/tmp/fig1.pdf")

    # Connect to Jira instance
    jira = jira_token_authenticate(args.jira_server_url, args.jira_auth_token)

    # Add project to JQL
    jql_project = JQLs.JQL_PROJECT.value.format(args.jira_project)

    # Add identifier to JQL
    jql_project_identifier = "{} {} {}".format(jql_project, Filters.LABEL.value.format(args.jira_label), Filters.NOT_DEPENDENCY_LABEL.value)
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

    aggregates = dict()

    # TOTAL ISSUES
    total_issues = run_jql(jira, jql_project_identifier)
    aggregates['total_issues'] = {'length': len(total_issues), 'jql': jql_project_identifier}

    # TOTAL ISSUES RELEASED
    total_issues_released = run_jql(jira, jql_project_identifier_released)
    aggregates['total_issues_released'] = {'length': len(total_issues_released), 'jql': jql_project_identifier_released}

    # TOTAL ISSUES CREATED BETWEEN DATES
    total_issues_created_between_dates = run_jql(jira, jql_project_identifier_dates)
    aggregates['total_issues_created_between_dates'] = {'length': len(total_issues_created_between_dates), 'jql': jql_project_identifier_dates}

    # TOTAL ISSUES RELEASED BETWEEN DATES
    total_issues_released_between_dates = run_jql(jira, jql_project_identifier_released_dates)
    aggregates['total_issues_released_between_dates'] = {'length': len(total_issues_released_between_dates), 'jql': jql_project_identifier_released_dates}

    # TOTAL ISSUES REJECTED BETWEEN DATES
    total_issues_rejected_between_dates = run_jql(jira, jql_project_identifier_rejected_dates)
    aggregates['total_issues_rejected_between_dates'] = {'length': len(total_issues_rejected_between_dates), 'jql': jql_project_identifier_rejected_dates}

    # TOTAL ISSUES IN FLIGHT BETWEEN DATES
    total_issues_in_flight_after_date = run_jql(jira, jql_project_identifier_in_flight_dates)
    aggregates['total_issues_in_flight_after_date'] = {'length': len(total_issues_in_flight_after_date), 'jql': jql_project_identifier_in_flight_dates}

    # Print rich tables
    fancy_print_jql_info(aggregates, "Swimlane report aggregates")
    fancy_print_issue_summary(total_issues_created_between_dates, jql_project_identifier_dates)
    fancy_print_issue_history(total_issues_in_flight_after_date, jql_project_identifier_in_flight_dates)

