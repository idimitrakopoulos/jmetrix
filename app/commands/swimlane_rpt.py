import logging

import ipdb

log = logging.getLogger('root')
from util.jql import JQLs, Filters
from util.toolkit import jira_token_authenticate, run_jql, fancy_print_issue_summary, fancy_print_issue_history, fancy_print_jql_info, simple_print_issue_keys

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

    aggregates = dict()

    # TOTAL ISSUES CREATED
    total_issues_created_jql = "{} {} {}".format(JQLs.JQL_PROJECT.value.format(args.jira_project),
                                                  Filters.NOT_TYPE_EPIC.value,
                                                  Filters.IN_LABEL.value.format(args.jira_label) + " " + Filters.IN_LABEL.value.format(args.jira_extra_label) if args.jira_extra_label else "")
    total_issues_created = run_jql(jira, total_issues_created_jql)
    aggregates['total_issues_created'] = {'length': len(total_issues_created), 'jql': total_issues_created_jql}
    # print_result_list_keys("total_issues_created", total_issues_created)

    # TOTAL ISSUES CREATED IN DEPENDENCY
    total_issues_created_in_dependency_jql = "{} {} {} {}".format(JQLs.JQL_PROJECT.value.format(args.jira_project),
                                                  Filters.NOT_TYPE_EPIC.value,
                                                  Filters.IN_LABEL.value.format(args.jira_label) + " " + Filters.IN_LABEL.value.format(args.jira_extra_label) if args.jira_extra_label else "",
                                                  Filters.IN_LABEL.value.format("Dependency"))
    total_issues_created_in_dependency = run_jql(jira, total_issues_created_in_dependency_jql)
    aggregates['total_issues_created_in_dependency'] = {'length': len(total_issues_created_in_dependency), 'jql': total_issues_created_in_dependency_jql}

    # TOTAL ISSUES RELEASED
    total_issues_released_jql = "{} {} {} {}".format(JQLs.JQL_PROJECT.value.format(args.jira_project),
                                                  Filters.NOT_TYPE_EPIC.value,
                                                  Filters.IN_LABEL.value.format(args.jira_label) + " " + Filters.IN_LABEL.value.format(args.jira_extra_label) if args.jira_extra_label else "",
                                                  Filters.RELEASED.value)
    total_issues_released = run_jql(jira, total_issues_released_jql)
    aggregates['total_issues_released'] = {'length': len(total_issues_released), 'jql': total_issues_released_jql}


    # TOTAL ISSUES REJECTED
    total_issues_rejected_jql = "{} {} {} {}".format(JQLs.JQL_PROJECT.value.format(args.jira_project),
                                                  Filters.NOT_TYPE_EPIC.value,
                                                  Filters.IN_LABEL.value.format(args.jira_label) + " " + Filters.IN_LABEL.value.format(args.jira_extra_label) if args.jira_extra_label else "",
                                                  Filters.REJECTED.value)
    total_issues_rejected = run_jql(jira, total_issues_rejected_jql)
    aggregates['total_issues_rejected'] = {'length': len(total_issues_rejected), 'jql': total_issues_rejected_jql}

    # TOTAL ISSUES IN FLIGHT
    total_issues_in_flight_jql = "{} {} {} {}".format(JQLs.JQL_PROJECT.value.format(args.jira_project),
                                                  Filters.NOT_TYPE_EPIC.value,
                                                  Filters.IN_LABEL.value.format(args.jira_label) + " " + Filters.IN_LABEL.value.format(args.jira_extra_label) if args.jira_extra_label else "",
                                                  Filters.IN_FLIGHT.value)
    total_issues_in_flight = run_jql(jira, total_issues_in_flight_jql)
    aggregates['total_issues_in_flight'] = {'length': len(total_issues_in_flight), 'jql': total_issues_in_flight_jql}

    # TOTAL ISSUES CREATED BETWEEN DATES
    total_issues_created_between_dates_jql = "{} {} {} {}".format(JQLs.JQL_PROJECT.value.format(args.jira_project),
                                                  Filters.NOT_TYPE_EPIC.value,
                                                  Filters.IN_LABEL.value.format(args.jira_label) + " " + Filters.IN_LABEL.value.format(args.jira_extra_label) if args.jira_extra_label else "",
                                                  Filters.CREATED_DATES_FROM_TO.value.format(args.date_from, args.date_to))
    total_issues_created_between_dates = run_jql(jira, total_issues_created_between_dates_jql)
    aggregates['total_issues_created_between_dates'] = {'length': len(total_issues_created_between_dates), 'jql': total_issues_created_between_dates_jql}

    # TOTAL ISSUES RELEASED BETWEEN DATES
    total_issues_released_between_dates_jql = "{} {} {} {} {}".format(JQLs.JQL_PROJECT.value.format(args.jira_project),
                                                  Filters.NOT_TYPE_EPIC.value,
                                                  Filters.IN_LABEL.value.format(args.jira_label) + " " + Filters.IN_LABEL.value.format(args.jira_extra_label) if args.jira_extra_label else "",
                                                  Filters.RELEASED.value,
                                                  Filters.RESOLVED_DATES_FROM_TO.value.format(args.date_from, args.date_to))
    total_issues_released_between_dates = run_jql(jira, total_issues_released_between_dates_jql)
    aggregates['total_issues_released_between_dates'] = {'length': len(total_issues_released_between_dates), 'jql': total_issues_released_between_dates_jql}

    # TOTAL ISSUES REJECTED BETWEEN DATES
    total_issues_rejected_between_dates_jql = "{} {} {} {} {}".format(JQLs.JQL_PROJECT.value.format(args.jira_project),
                                                  Filters.NOT_TYPE_EPIC.value,
                                                  Filters.IN_LABEL.value.format(args.jira_label) + " " + Filters.IN_LABEL.value.format(args.jira_extra_label) if args.jira_extra_label else "",
                                                  Filters.REJECTED.value,
                                                  Filters.RESOLVED_DATES_FROM_TO.value.format(args.date_from, args.date_to))
    total_issues_rejected_between_dates = run_jql(jira, total_issues_rejected_between_dates_jql)
    aggregates['total_issues_rejected_between_dates'] = {'length': len(total_issues_rejected_between_dates), 'jql': total_issues_rejected_between_dates_jql}

    # TOTAL ISSUES IN FLIGHT BETWEEN DATES
    total_issues_in_flight_after_date_jql = "{} {} {} {} {}".format(JQLs.JQL_PROJECT.value.format(args.jira_project),
                                                  Filters.NOT_TYPE_EPIC.value,
                                                  Filters.IN_LABEL.value.format(args.jira_label) + " " + Filters.IN_LABEL.value.format(args.jira_extra_label) if args.jira_extra_label else "",
                                                  Filters.IN_FLIGHT.value,
                                                  Filters.CREATED_DATES_FROM_TO.value.format(args.date_from, args.date_to))
    total_issues_in_flight_after_date = run_jql(jira, total_issues_in_flight_after_date_jql)
    aggregates['total_issues_in_flight_after_date'] = {'length': len(total_issues_in_flight_after_date), 'jql': total_issues_in_flight_after_date_jql}

    # TOTAL ISSUES CREATED BETWEEN DATES IN DEPENDENCY
    total_issues_created_between_dates_in_dependency_jql = "{} {} {} {} {} {}".format(JQLs.JQL_PROJECT.value.format(args.jira_project),
                                                  Filters.NOT_TYPE_EPIC.value,
                                                  Filters.IN_LABEL.value.format(args.jira_label) + " " + Filters.IN_LABEL.value.format(args.jira_extra_label) if args.jira_extra_label else "",
                                                  Filters.IN_LABEL.value.format("Dependency"),
                                                  Filters.IN_FLIGHT.value,
                                                  Filters.RESOLVED_DATES_FROM_TO.value.format(args.date_from, args.date_to))
    total_issues_created_between_dates_in_dependency = run_jql(jira, total_issues_created_between_dates_in_dependency_jql)
    aggregates['total_issues_created_between_dates_in_dependency'] = {'length': len(total_issues_created_between_dates_in_dependency), 'jql': total_issues_created_between_dates_in_dependency_jql}

    # TOTAL ISSUES RELEASED BETWEEN DATES IN DEPENDENCY
    total_issues_released_between_dates_in_dependency_jql = "{} {} {} {} {} {}".format(JQLs.JQL_PROJECT.value.format(args.jira_project),
                                                  Filters.NOT_TYPE_EPIC.value,
                                                  Filters.IN_LABEL.value.format(args.jira_label) + " " + Filters.IN_LABEL.value.format(args.jira_extra_label) if args.jira_extra_label else "",
                                                  Filters.IN_LABEL.value.format("Dependency"),
                                                  Filters.RELEASED.value,
                                                  Filters.RESOLVED_DATES_FROM_TO.value.format(args.date_from, args.date_to))
    total_issues_released_between_dates_in_dependency = run_jql(jira, total_issues_released_between_dates_in_dependency_jql)
    aggregates['total_issues_released_between_dates_in_dependency'] = {'length': len(total_issues_released_between_dates_in_dependency), 'jql': total_issues_released_between_dates_in_dependency_jql}

    # TOTAL ISSUES REJECTED BETWEEN DATES IN DEPENDENCY
    total_issues_rejected_between_dates_in_dependency_jql = "{} {} {} {} {} {}".format(JQLs.JQL_PROJECT.value.format(args.jira_project),
                                                  Filters.NOT_TYPE_EPIC.value,
                                                  Filters.IN_LABEL.value.format(args.jira_label) + " " + Filters.IN_LABEL.value.format(args.jira_extra_label) if args.jira_extra_label else "",
                                                  Filters.IN_LABEL.value.format("Dependency"),
                                                  Filters.REJECTED.value,
                                                  Filters.RESOLVED_DATES_FROM_TO.value.format(args.date_from, args.date_to))
    total_issues_rejected_between_dates_in_dependency = run_jql(jira, total_issues_rejected_between_dates_in_dependency_jql)
    aggregates['total_issues_rejected_between_dates_in_dependency'] = {'length': len(total_issues_rejected_between_dates_in_dependency), 'jql': total_issues_rejected_between_dates_in_dependency_jql}

    # TOTAL ISSUES IN FLIGHT BETWEEN DATES IN DEPENDENCY
    total_issues_in_flight_after_date_in_dependency_jql = "{} {} {} {} {} {}".format(JQLs.JQL_PROJECT.value.format(args.jira_project),
                                                  Filters.NOT_TYPE_EPIC.value,
                                                  Filters.IN_LABEL.value.format(args.jira_label) + " " + Filters.IN_LABEL.value.format(args.jira_extra_label) if args.jira_extra_label else "",
                                                  Filters.IN_LABEL.value.format("Dependency"),
                                                  Filters.IN_FLIGHT.value,
                                                  Filters.CREATED_DATES_FROM_TO.value.format(args.date_from, args.date_to))
    total_issues_in_flight_after_date_in_dependency = run_jql(jira, total_issues_in_flight_after_date_in_dependency_jql)
    aggregates['total_issues_in_flight_after_date_in_dependency'] = {'length': len(total_issues_in_flight_after_date_in_dependency), 'jql': total_issues_in_flight_after_date_in_dependency_jql}
    # ipdb.set_trace()

    # Print rich tables
    fancy_print_jql_info(aggregates, "Swimlane report aggregates")
    simple_print_issue_keys(total_issues_created_between_dates, "total_issues_created_between_dates")
    simple_print_issue_keys(total_issues_released_between_dates, "total_issues_released_between_dates")
    # fancy_print_issue_history(total_issues_in_flight_after_date, total_issues_in_flight_after_date_jql)

