#!/usr/bin/env python3
import logging

import util.logger as logger
import argparse
import importlib


if __name__ == '__main__':
    # Instantiate the parser
    parser = argparse.ArgumentParser(prog='jmetrix', description='A CLI tool for Jira metrics', epilog='(c) 2012-present Iason Dimitrakopoulos - idimitrakopoulos@gmail.com')

    subparsers = parser.add_subparsers(help='sub-command help', dest='ab')
    live_parser = subparsers.add_parser('live', help='Live view of a JQL')
    live_required_args= live_parser.add_argument_group('required arguments')
    live_required_args.add_argument('-u', '--url', dest='jira_server_url', type=str, help='The Jira server base URL (e.g. https://xxxx.xxx.xxx)', required=True)
    live_required_args.add_argument('-t', '--token', dest='jira_auth_token', type=str, help='The Jira authentication token', required=True)
    live_required_args.add_argument('-j', '--jql', dest='jira_jql', type=str, help='The JQL query you want to get metrics for.', required=True)

    history_parser = subparsers.add_parser('history', help='Historic view of a JQL')
    history_required_args= history_parser.add_argument_group('required arguments')
    history_required_args.add_argument('-u', '--url', dest='jira_server_url', type=str, help='The Jira server base URL (e.g. https://xxxx.xxx.xxx)', required=True)
    history_required_args.add_argument('-t', '--token', dest='jira_auth_token', type=str, help='The Jira authentication token', required=True)
    history_required_args.add_argument('-j', '--jql', dest='jira_jql', type=str, help='The JQL query you want to get metrics for.', required=True)
    history_optional_args= history_parser.add_argument_group('optional arguments')
    history_optional_args.add_argument('-V', '--verbose', action='store_true', help='Run script in Verbose mode')


    burnup_parser = subparsers.add_parser('burnup', help='Burnups from Jira')
    burnup_required_args= burnup_parser.add_argument_group('required arguments')
    burnup_required_args.add_argument('-u', '--url', dest='jira_server_url', type=str, help='The Jira server base URL (e.g. https://xxxx.xxx.xxx)', required=True)
    burnup_required_args.add_argument('-t', '--token', dest='jira_auth_token', type=str, help='The Jira authentication token', required=True)
    burnup_required_args.add_argument('-f', '--from', dest='date_from', type=str, help='The date from which to search in the format of yyyy-mm-dd', required=True)
    burnup_required_args.add_argument('-T', '--to', dest='date_to', type=str, help='The date up to which to search in the format of yyyy-mm-dd', required=True)
    burnup_required_args.add_argument('-p', '--project', dest='jira_project', type=str, help='The Jira project key (e.g. OGST)', required=True)
    burnup_required_args.add_argument('-l', '--label', dest='jira_label', type=str, help='The issue label to use for issue search', required=True)

    burnup_optional_args= burnup_parser.add_argument_group('optional arguments')
    burnup_optional_args.add_argument('-L', '--extralabel', dest='jira_extra_label', type=str, help='An extra issue label to use for issue search', required=False)
    burnup_optional_args.add_argument('-V', '--verbose', action='store_true', help='Run script in Verbose mode')

    # Parse arguments
    args = parser.parse_args()
    log = logger.setup_custom_logger('root', logging.DEBUG if args.verbose else logging.INFO)

    if args.ab is None:  # End execution with help if no arguments were supplied
        parser.print_help()
        exit(0)
    else:  # Execute the appropriate command
        cmd = importlib.import_module("commands." + args.ab)
        cmd.exec(args)




