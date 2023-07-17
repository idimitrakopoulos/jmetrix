import logging
log = logging.getLogger('root')
from util.jql import JQLs, Filters
from util.toolkit import jira_token_authenticate, run_jql, print_issue_summary, print_issue_history, fancy_print_issue_summary, fancy_print_issue_history

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
    fancy_print_issue_summary(jql_results)

    # TOTAL ISSUES RELEASED BETWEEN DATES
    jql_results = run_jql(jira, jql_project_identifier_released_dates)
    log.info("Total issues released between {} and {}: {}".format(args.date_from, args.date_to, len(jql_results)))

    # TOTAL ISSUES REJECTED BETWEEN DATES
    jql_results = run_jql(jira, jql_project_identifier_rejected_dates)
    log.info("Total issues rejected between {} and {}: {}".format(args.date_from, args.date_to, len(jql_results)))

    # TOTAL ISSUES IN FLIGHT BETWEEN DATES
    jql_results = run_jql(jira, jql_project_identifier_in_flight_dates)
    log.info("Total issues in flight NOT created after {}: {}".format(args.date_from, len(jql_results)))
    fancy_print_issue_history(jql_results)