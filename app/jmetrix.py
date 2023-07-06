#!/usr/bin/env python3
import util.logger as logger
import argparse
log = logger.setup_custom_logger('root')
import importlib


if __name__ == '__main__':
    # Instantiate the parser
    parser = argparse.ArgumentParser(prog='jmetrix', description='A CLI tool for Jira metrics', epilog='(c) 2012-present Iason Dimitrakopoulos - idimitrakopoulos@gmail.com')


    subparsers = parser.add_subparsers(help='sub-command help', dest='ab')
    parser_live = subparsers.add_parser('live', help='Live view of a JQL')
    requiredArgs= parser_live.add_argument_group('required arguments')
    requiredArgs.add_argument('-u', '--url', dest='jira_server_url', type=str, help='The Jira server base URL (e.g. https://xxxx.xxx.xxx)', required=True)
    requiredArgs.add_argument('-t', '--token', dest='jira_auth_token', type=str, help='The Jira authentication token', required=True)
    requiredArgs.add_argument('-j', '--jql', dest='jira_jql', type=str, help='The JQL query you want to get metrics for.', required=True)

    parser_history = subparsers.add_parser('history', help='Historic view of a JQL')
    requiredArgs= parser_history.add_argument_group('required arguments')
    requiredArgs.add_argument('-u', '--url', dest='jira_server_url', type=str, help='The Jira server base URL (e.g. https://xxxx.xxx.xxx)', required=True)
    requiredArgs.add_argument('-t', '--token', dest='jira_auth_token', type=str, help='The Jira authentication token', required=True)
    requiredArgs.add_argument('-j', '--jql', dest='jira_jql', type=str, help='The JQL query you want to get metrics for.', required=True)

    args = parser.parse_args()
    if args.ab is None:
        parser.print_help()
        exit(0)


    cmd = importlib.import_module("commands." + args.ab)
    cmd.args = args
    cmd.exec()




