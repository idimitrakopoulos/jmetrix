#!/usr/bin/env python3
import logging

import util.logger as logger
import argparse
import importlib


if __name__ == '__main__':
    # Instantiate the parser
    parser = argparse.ArgumentParser(prog='jmetrix', description='A CLI tool for Jira metrics', epilog='(c) 2012-present Iason Dimitrakopoulos - idimitrakopoulos@gmail.com')
    parser.add_argument('-V', '--verbose', action='store_true', help='Run script in Verbose mode')

    subparsers = parser.add_subparsers(help='sub-command help', dest='commands')

    # Test
    test_parser = subparsers.add_parser('test', help='Test stuff')
    test_required_args = test_parser.add_argument_group('required arguments')
    test_required_args.add_argument('-u', '--url', dest='jira_server_url', type=str, help='The Jira server base URL (e.g. https://xxxx.xxx.xxx)', required=True)
    test_required_args.add_argument('-t', '--token', dest='jira_auth_token', type=str, help='The Jira authentication token', required=True)

    # Inspect
    inspect_parser = subparsers.add_parser('inspect', help='Inspect a JQL')
    inspect_required_args = inspect_parser.add_argument_group('required arguments')
    inspect_required_args.add_argument('-u', '--url', dest='jira_server_url', type=str, help='The Jira server base URL (e.g. https://xxxx.xxx.xxx)', required=True)
    inspect_required_args.add_argument('-t', '--token', dest='jira_auth_token', type=str, help='The Jira authentication token', required=True)
    inspect_required_args.add_argument('-j', '--jql', dest='jira_jql', type=str, help='The JQL query you want to get metrics for.', required=True)
    inspect_optional_args = inspect_parser.add_argument_group('optional arguments')
    inspect_optional_args.add_argument('-V', '--verbose', action='store_true', help='Run script in Verbose mode')

    # Swimlane report
    swimlane_rpt_parser = subparsers.add_parser('swimlane_rpt', help='Swimlane Report from Jira based on specific label')
    swimlane_rpt_required_args = swimlane_rpt_parser.add_argument_group('required arguments')
    swimlane_rpt_required_args.add_argument('-u', '--url', dest='jira_server_url', type=str, help='The Jira server base URL (e.g. https://xxxx.xxx.xxx)', required=True)
    swimlane_rpt_required_args.add_argument('-t', '--token', dest='jira_auth_token', type=str, help='The Jira authentication token', required=True)
    swimlane_rpt_required_args.add_argument('-p', '--project', dest='jira_project', type=str, help='The Jira project key (e.g. OGST)', required=True)
    swimlane_rpt_required_args.add_argument('-f', '--from', dest='date_from', type=str, help='The date from which to search in the format of yyyy-mm-dd', required=True)
    swimlane_rpt_required_args.add_argument('-T', '--to', dest='date_to', type=str, help='The date up to which to search in the format of yyyy-mm-dd', required=True)
    swimlane_rpt_required_args.add_argument('-l', '--label', dest='jira_label', type=str, help='The issue label to use for issue search', required=True)
    # burnup_required_args.add_argument('-s', '--stories_optimistic', dest='stories_optimistic', type=float, help='Optimistic prediction of stories per week', required=True)
    # burnup_required_args.add_argument('-S', '--stories_expected', dest='stories_expected', type=float, help='Expected prediction of stories per week', required=True)
    # burnup_required_args.add_argument('-b', '--project_beginning', dest='project_beginning', type=float, help='Date when project begun in the format of yyyy-mm-dd', required=True)
    swimlane_rpt_optional_args = swimlane_rpt_parser.add_argument_group('optional arguments')
    swimlane_rpt_optional_args.add_argument('-L', '--extralabel', dest='jira_extra_label', type=str, help='An extra issue label to use for issue search', required=False)
    swimlane_rpt_optional_args.add_argument('-V', '--verbose', action='store_true', help='Run script in Verbose mode')

    # Daily report
    daily_rpt_parser = subparsers.add_parser('daily_rpt', help='Daily Report from Jira')
    daily_rpt_required_args = daily_rpt_parser.add_argument_group('required arguments')
    daily_rpt_required_args.add_argument('-u', '--url', dest='jira_server_url', type=str, help='The Jira server base URL (e.g. https://xxxx.xxx.xxx)', required=True)
    daily_rpt_required_args.add_argument('-t', '--token', dest='jira_auth_token', type=str, help='The Jira authentication token', required=True)
    daily_rpt_required_args.add_argument('-p', '--project', dest='jira_project', type=str, help='The Jira project key (e.g. OGST)', required=True)
    daily_rpt_optional_args = daily_rpt_parser.add_argument_group('optional arguments')
    # daily_rpt_optional_args.add_argument('-l', '--label', dest='jira_label', type=str, help='The issue label to use for issue search')
    daily_rpt_optional_args.add_argument('-d', '--discovery', action='store_true', help='Run report for discovery board too')
    daily_rpt_optional_args.add_argument('-V', '--verbose', action='store_true', help='Run script in Verbose mode')

    # Burn-up report
    burnup_parser = subparsers.add_parser('burnup', help='Burnup Report from Jira based on specific values')
    burnup_required_args = burnup_parser.add_argument_group('required arguments')
    burnup_required_args.add_argument('-u', '--url', dest='jira_server_url', type=str, help='The Jira server base URL (e.g. https://xxxx.xxx.xxx)', required=True)
    burnup_required_args.add_argument('-t', '--token', dest='jira_auth_token', type=str, help='The Jira authentication token', required=True)
    burnup_required_args.add_argument('-p', '--project', dest='jira_project', type=str, help='The Jira project key (e.g. OGST)', required=True)
    burnup_required_args.add_argument('-f', '--from', dest='date_from', type=str, help='The date from which to search in the format of yyyy-mm-dd', required=True)
    burnup_required_args.add_argument('-l', '--lvl1_labels', dest='jira_lvl1_labels', type=str, help='Jira labels in comma separated string will be joined and any labels separated with colon will be split. For example "label1,label2;label3", you can use ! before each field to negate them', required=True)
    burnup_required_args.add_argument('-L', '--lvl2_labels', dest='jira_lvl2_labels', type=str, help='Jira labels in comma separated string will be joined and any labels separated with colon will be split. For example "label1,label2;label3", you can use ! before each field to negate them', required=True)
    burnup_optional_args = burnup_parser.add_argument_group('optional arguments')
    burnup_optional_args.add_argument('-T', '--to', dest='date_to', type=str, help='The date up to which to search in the format of yyyy-mm-dd')
    burnup_optional_args.add_argument('-c', '--changes', action='store_true', help='See issue changes')
    burnup_optional_args.add_argument('-V', '--verbose', action='store_true', help='Run script in Verbose mode')

    # Parse arguments
    args = parser.parse_args()

    # Create logger with proper log level
    log = logger.setup_custom_logger('root', logging.DEBUG if args.verbose else logging.INFO)

    if args.commands is None:  # End execution with help if no arguments were supplied
        parser.print_help()
        exit(0)
    else:  # Execute the appropriate command
        cmd = importlib.import_module("commands." + args.commands)
        cmd.exec(args)


