from util.jql import Status, JQLs, TimeValue, CustomFieldNames
from util.metrics import AggregatedMetric, ThroughputMetric, CompositeAggregatedMetric, InfoMetric
from util.toolkit import count_transitions, get_time_between_extreme_statuses, get_time_between_distant_statuses, \
    get_time_in_initial_status, get_time_in_status, get_sizing_accuracy, retrieve_pbi_data, count_field_values, \
    get_time_from_creation_to_extreme_status, retrieve_metric_from_composite_pbi_list, retrieve_tpr_data, \
    calc_days_from_now_using_working_hours

from collections import Counter
import ipdb

class PBI(object):

    values = dict()
    pbi = None

    def __init__(self, pbi):
        self.pbi = pbi
        changelog = pbi.changelog
        self.values = dict()


        # Count times from status to status
        # Times Open from Preparation
        self.values['times_stopped_preparation'] = count_transitions(Status.PREPARATION.value, Status.OPEN.value, changelog)
        # Times Stopped Analysis
        self.values['times_stopped_analysis'] = count_transitions(Status.ANALYSIS.value, Status.READY.value, changelog)
        # Times Returned from Ready
        self.values['times_returned'] = count_transitions(Status.ANALYSIS.value, Status.RETURNED.value, changelog)
        # Times Ready from In Progress
        self.values['times_stopped_work'] = count_transitions(Status.IN_PROGRESS.value, Status.READY.value, changelog)
        # Times Reopened from Done
        self.values['times_reopened_from_done'] = count_transitions(Status.DONE.value, Status.REOPENED.value, changelog)
        # Times Reopened from Acceptance
        self.values['times_reopened_from_acceptance'] = count_transitions(Status.ACCEPTANCE.value, Status.REOPENED.value, changelog)
        # Times Reopened from Release
        self.values['times_reopened_from_release'] = count_transitions(Status.RELEASE.value, Status.REOPENED.value, changelog)
        # Times Reopened from Closed
        self.values['times_reopened_from_closed'] = count_transitions(Status.CLOSED.value, Status.REOPENED.value, changelog)

        # TODO - Count times field value obtained
        # Reopen Reasons
        self.values['reopen_reasons'] = Counter(count_field_values(CustomFieldNames.REOPEN_REASON.value, changelog))

        # Pause Preparation Reasons
        self.values['pause_preparation_reasons'] = Counter(count_field_values(CustomFieldNames.PAUSE_PREPARATION_REASON.value, changelog))

        # Pause Work Reasons
        self.values['pause_work_reasons'] = Counter(count_field_values(CustomFieldNames.PAUSE_WORK_REASON.value, changelog))

        # Revision Reasons
        self.values['revision_reasons'] = Counter(count_field_values(CustomFieldNames.REVISION_REASON.value, changelog))

        # Origin
        self.values['origin'] = Counter(count_field_values(CustomFieldNames.ORIGIN.value, changelog))


        # Lead Time
        self.values['lead_time'] = get_time_from_creation_to_extreme_status(self.pbi.fields.created, Status.CLOSED.value, changelog)

        # Cycle Time
        self.values['cycle_time'] = get_time_between_extreme_statuses(Status.IN_PROGRESS.value, Status.CLOSED.value, changelog)

        # Count time between statuses
        # Initial Preparation Time
        prep_time_lst = get_time_between_distant_statuses(Status.PREPARATION.value, Status.READY.value, changelog)
        self.values['initial_prep_time'] = prep_time_lst[0] if prep_time_lst != [] else 0

        # Initial Development Time
        dev_time_lst = get_time_between_distant_statuses(Status.IN_PROGRESS.value, Status.DONE.value, changelog)
        self.values['initial_dev_time'] = dev_time_lst[0] if dev_time_lst != [] else 0

        # Time in Status
        self.values['time_in_open'] = sum(get_time_in_initial_status(Status.OPEN.value, changelog, self.pbi.fields.created))
        self.values['time_in_preparation'] = sum(get_time_in_status(Status.PREPARATION.value,changelog))
        self.values['time_in_returned'] = sum(get_time_in_status(Status.RETURNED.value,changelog))
        self.values['time_in_ready'] = sum(get_time_in_status(Status.READY.value,changelog))
        self.values['time_in_analysis'] = sum(get_time_in_status(Status.ANALYSIS.value,changelog))
        self.values['time_in_in_progress'] = sum(get_time_in_status(Status.IN_PROGRESS.value, changelog))
        self.values['time_in_done'] = sum(get_time_in_status(Status.DONE.value, changelog))
        self.values['time_in_acceptance'] = sum(get_time_in_status(Status.ACCEPTANCE.value, changelog))
        self.values['time_in_release'] = sum(get_time_in_status(Status.RELEASE.value, changelog))
        self.values['time_in_reopened'] = sum(get_time_in_status(Status.REOPENED.value, changelog))


        # Process Efficiency = (Hands-on time / Total lead-time) * 100
        hands_off_time = [self.values['time_in_open'],
                          self.values['time_in_returned'],
                          self.values['time_in_ready'],
                          self.values['time_in_done'],
                          self.values['time_in_reopened']]

        # If lead time is zero then the issue was worked off normal working hours so it should be counted as efficient
        self.values['process_efficiency'] = ((self.values['lead_time'] - sum(hands_off_time)) / self.values['lead_time']) * 100 if self.values['lead_time'] else 100

        # Sizing Efficiency = (Size estimated / In Progress overall time) * 100
        self.values['size']  = pbi.fields.customfield_11541
        if self.values['size']:
            self.values['sizing_accuracy'] = get_sizing_accuracy(self.values['size'].value,
                                                                 round(self.values['time_in_in_progress']))
        else:
            self.values['sizing_accuracy'] = -1


        # if pbi.key == "ET-23":
        #     ipdb.set_trace()


class PBIMetricCollection(object):
    pbis = list()

    metrics = dict()
    reason_metrics = dict()
    throughput_metrics = dict()

    jql_pbi = JQLs.JQL_PBI.value
    jira = None
    jira_project = ""
    jira_issuetype = ""
    jira_issuetype_to_lower = ""
    jira_workflow_end_status = ""
    jira_minus_time = ""
    jira_option_customfield_possible_values = dict()


    def __init__(self, jira, jira_project, jira_issuetype, jira_workflow_end_status, jira_minus_time):
        self.jira = jira
        self.jira_issuetype = jira_issuetype
        self.jira_issuetype_to_lower = jira_issuetype.replace(' ', '_').lower()
        self.jira_project = jira_project
        self.jira_workflow_end_status = jira_workflow_end_status
        self.jira_minus_time = jira_minus_time

        self.metrics = dict()
        self.reason_metrics = dict()
        self.throughput_metrics = dict()
        self.cancellation_metrics = dict()

        # Populate PBIs with data
        self.pbis = self.refresh_metric_values()

        # If JQL query returned PBIs
        if self.pbis:
            # times_stopped_preparation
            self.metrics['times_stopped_preparation'] = AggregatedMetric(self.jira_issuetype_to_lower + "_times_stopped_preparation",
                                                                         [pbi.values['times_stopped_preparation'] for pbi in self.pbis])
            # times_stopped_analysis
            self.metrics['times_stopped_analysis'] = AggregatedMetric(self.jira_issuetype_to_lower + "_times_stopped_analysis",
                                                                      [pbi.values['times_stopped_analysis'] for pbi in self.pbis])
            # times_returned
            self.metrics['times_returned'] = AggregatedMetric(self.jira_issuetype_to_lower + "_times_returned",
                                                   [pbi.values['times_returned'] for pbi in self.pbis])

            # times_stopped_work
            self.metrics['times_stopped_work'] = AggregatedMetric(self.jira_issuetype_to_lower + "_times_stopped_work",
                                                       [pbi.values['times_stopped_work'] for pbi in self.pbis])

            # times_reopened_from_done
            self.metrics['times_reopened_from_done'] = AggregatedMetric(self.jira_issuetype_to_lower + "_times_reopened_from_done",
                                                             [pbi.values['times_reopened_from_done'] for pbi in self.pbis])

            # times_reopened_from_acceptance
            self.metrics['times_reopened_from_acceptance'] = AggregatedMetric(self.jira_issuetype_to_lower + "_times_reopened_from_acceptance",
                                                                   [pbi.values['times_reopened_from_acceptance'] for pbi in self.pbis])

            # times_reopened_from_release
            self.metrics['times_reopened_from_release'] = AggregatedMetric(self.jira_issuetype_to_lower + "_times_reopened_from_release",
                                                                [pbi.values['times_reopened_from_release'] for pbi in self.pbis])

            # times_reopened_from_closed
            self.metrics['times_reopened_from_closed'] = AggregatedMetric(self.jira_issuetype_to_lower + "_times_reopened_from_closed",
                                                               [pbi.values['times_reopened_from_closed'] for pbi in self.pbis])

            # lead_time
            self.metrics['lead_time'] = AggregatedMetric(self.jira_issuetype_to_lower + "_lead_time",
                                              [pbi.values['lead_time'] for pbi in self.pbis])

            # cycle_time
            self.metrics['cycle_time'] = AggregatedMetric(self.jira_issuetype_to_lower + "_cycle_time",
                                               [pbi.values['cycle_time'] for pbi in self.pbis])

            # initial_prep_time
            self.metrics['initial_prep_time'] = AggregatedMetric(self.jira_issuetype_to_lower + "_initial_prep_time",
                                                      [pbi.values['initial_prep_time'] for pbi in self.pbis])

            # initial_dev_time
            self.metrics['initial_dev_time'] = AggregatedMetric(self.jira_issuetype_to_lower + '_initial_dev_time',
                                                     [pbi.values['initial_dev_time'] for pbi in self.pbis])

            # process_efficiency
            self.metrics['process_efficiency'] = AggregatedMetric(self.jira_issuetype_to_lower + "_process_efficiency",
                                                                [pbi.values['process_efficiency'] for pbi in self.pbis])

            # sizing_accuracy (Filter out any pbi that has sizing -1 (either NB or None set))
            self.metrics['sizing_accuracy'] = AggregatedMetric(self.jira_issuetype_to_lower + "_sizing_accuracy",
                                                                [y for y in [pbi.values['sizing_accuracy'] for pbi in self.pbis] if y != -1])

            # time_in_open
            self.metrics['time_in_open'] = AggregatedMetric(self.jira_issuetype_to_lower + "_time_in_open",
                                                                [pbi.values['time_in_open'] for pbi in self.pbis])
            # time_in_preparation
            self.metrics['time_in_preparation'] = AggregatedMetric(self.jira_issuetype_to_lower + "_time_in_preparation",
                                                                [pbi.values['time_in_preparation'] for pbi in self.pbis])

            # time_in_returned
            self.metrics['time_in_returned'] = AggregatedMetric(self.jira_issuetype_to_lower + "_time_in_returned",
                                                                [pbi.values['time_in_returned'] for pbi in self.pbis])

            # time_in_analysis
            self.metrics['time_in_analysis'] = AggregatedMetric(self.jira_issuetype_to_lower + "_time_in_analysis",
                                                                [pbi.values['time_in_analysis'] for pbi in self.pbis])

            # time_in_ready
            self.metrics['time_in_ready'] = AggregatedMetric(self.jira_issuetype_to_lower + "_time_in_ready",
                                                                [pbi.values['time_in_ready'] for pbi in self.pbis])

            # time_in_in_progress
            self.metrics['time_in_in_progress'] = AggregatedMetric(self.jira_issuetype_to_lower + "_time_in_in_progress",
                                                                [pbi.values['time_in_in_progress'] for pbi in self.pbis])

            # time_in_done
            self.metrics['time_in_done'] = AggregatedMetric(self.jira_issuetype_to_lower + "_time_in_done",
                                                                [pbi.values['time_in_done'] for pbi in self.pbis])

            # time_in_acceptance
            self.metrics['time_in_acceptance'] = AggregatedMetric(self.jira_issuetype_to_lower + "_time_in_acceptance",
                                                                [pbi.values['time_in_acceptance'] for pbi in self.pbis])
            # time_in_release
            self.metrics['time_in_release'] = AggregatedMetric(self.jira_issuetype_to_lower + "_time_in_release",
                                                                [pbi.values['time_in_release'] for pbi in self.pbis])

            # time_in_reopened
            self.metrics['time_in_reopened'] = AggregatedMetric(self.jira_issuetype_to_lower + "_time_in_reopened",
                                                                [pbi.values['time_in_reopened'] for pbi in self.pbis])

            # reopen_reasons
            self.metrics['reopen_reasons'] = CompositeAggregatedMetric(self.jira_issuetype_to_lower + "_reopen_reason_{}",
                                                                       [pbi.values['reopen_reasons'] for pbi in self.pbis])

            # pause_preparation_reasons
            self.metrics['pause_preparation_reasons'] = CompositeAggregatedMetric(self.jira_issuetype_to_lower + "_pause_preparation_reason_{}",
                                                                       [pbi.values['pause_preparation_reasons'] for pbi in self.pbis])

            # pause_work_reasons
            self.metrics['pause_work_reasons'] = CompositeAggregatedMetric(self.jira_issuetype_to_lower + "_pause_work_reason_{}",
                                                                       [pbi.values['pause_work_reasons'] for pbi in self.pbis])

            # revision_reasons
            self.metrics['revision_reasons'] = CompositeAggregatedMetric(self.jira_issuetype_to_lower + "_revision_reason_{}",
                                                                       [pbi.values['revision_reasons'] for pbi in self.pbis])

            # weekly_throughput
            self.throughput_metrics['weekly_throughput'] = ThroughputMetric(self.jira_issuetype_to_lower + '_weekly_throughput',
                                                                            self.jira,
                                                                            JQLs.JQL_THROUGHPUT.value.format(self.jira_project,
                                                                                                             self.jira_issuetype,
                                                                                                             self.jira_workflow_end_status,
                                                                                                             self.jira_workflow_end_status,
                                                                                                             TimeValue.MINUS_1_WEEK.value))

            # monthly_throughput
            self.throughput_metrics['monthly_throughput'] = ThroughputMetric(self.jira_issuetype_to_lower + '_monthly_throughput',
                                                                             self.jira,
                                                                             JQLs.JQL_THROUGHPUT.value.format(self.jira_project,
                                                                                                              self.jira_issuetype,
                                                                                                              self.jira_workflow_end_status,
                                                                                                              self.jira_workflow_end_status,
                                                                                                              TimeValue.MINUS_1_MONTH.value))
            #
            # self.cancellation_metrics['weekly_wasted_time_due_to_cancellation'] = ThroughputMetric(self.jira_issuetype_to_lower + '_weekly_wasted_time_due_to_cancellation',
            #                                                                                     self.jira,
            #                                                                                     JQLs.JQL_CANCELLED.value.format(self.jira_project,
            #                                                                                                                      self.jira_issuetype,
            #                                                                                                                      self.jira_workflow_end_status,
            #                                                                                                                      self.jira_workflow_end_status,
            #                                                                                                                      TimeValue.MINUS_1_WEEK.value))

    def refresh_metric_values(self):
        return retrieve_pbi_data(self.jira, self.jql_pbi.format(self.jira_project, self.jira_issuetype, self.jira_workflow_end_status, self.jira_workflow_end_status, self.jira_minus_time))

    def register_prometheus_metrics(self):
        for key in self.metrics:
            self.metrics[key].register_prometheus_metric()
            self.metrics[key].populate_prometheus_metric()
        for key in self.throughput_metrics:
            self.throughput_metrics[key].register_prometheus_metric()
            self.throughput_metrics[key].populate_prometheus_metric()

    def refresh_prometheus_metrics(self):
        self.pbis = self.refresh_metric_values()
        for key in self.metrics:
            self.metrics[key].refresh([pbi.values[key] for pbi in self.pbis])
            self.metrics[key].populate_prometheus_metric()
        for key in self.throughput_metrics:
            self.throughput_metrics[key].refresh(None)
            
            
class CompositePBIMetricCollection(object):
    composite_pbis = list()
    metrics = dict()

    def __init__(self, pbis):
        self.composite_pbis = pbis
        self.metrics = dict()

        # Populate PBIs with data
        self.metrics = self.refresh_metric_values()

    def refresh_metric_values(self):
        m = dict()

        # lead_time
        m['lead_time'] = AggregatedMetric("composite_pbi_lead_time",
                                          retrieve_metric_from_composite_pbi_list("lead_time", self.composite_pbis))
        # cycle_time
        m['cycle_time'] = AggregatedMetric("composite_pbi_cycle_time",
                                           retrieve_metric_from_composite_pbi_list("cycle_time", self.composite_pbis))
        # process_efficiency
        m['process_efficiency'] = AggregatedMetric("composite_pbi_process_efficiency",
                                                   retrieve_metric_from_composite_pbi_list("process_efficiency", self.composite_pbis))

        # sizing_accuracy
        m['sizing_accuracy'] = AggregatedMetric("composite_pbi_sizing_accuracy",
                                                [i for i in retrieve_metric_from_composite_pbi_list("sizing_accuracy", self.composite_pbis) if i != -1])

        return m

    def register_prometheus_metrics(self):
        for key in self.metrics:
            self.metrics[key].register_prometheus_metric()
            self.metrics[key].populate_prometheus_metric()


    def refresh_prometheus_metrics(self):
        self.metrics = self.refresh_metric_values()



class TPR(object):

    values = dict()
    tpr = None

    def __init__(self, tpr):
        self.tpr = tpr
        changelog = tpr.changelog
        self.values = dict()

        # Count times from status to status
        # Times Open from Preparation
        self.values['times_stopped_preparation'] = count_transitions(Status.PREPARATION.value, Status.OPEN.value, changelog)

        # Times Stopped Triage
        self.values['times_stopped_triage'] = count_transitions(Status.TRIAGE.value, Status.READY.value, changelog)
        # Times Returned from Triage
        self.values['times_returned'] = count_transitions(Status.TRIAGE.value, Status.RETURNED.value, changelog)

        # Lead Time
        self.values['lead_time'] = get_time_from_creation_to_extreme_status(self.tpr.fields.created, Status.CLOSED.value, changelog)

        # Formation Time
        self.values['formation_time'] = get_time_from_creation_to_extreme_status(self.tpr.fields.created, Status.COMMITTED.value, changelog)

        # Cycle Time
        self.values['cycle_time'] = get_time_between_extreme_statuses(Status.COMMITTED.value, Status.CLOSED.value, changelog)

        # Time in Status
        self.values['time_in_open'] = sum(get_time_in_initial_status(Status.OPEN.value, changelog, self.tpr.fields.created))
        self.values['time_in_preparation'] = sum(get_time_in_status(Status.PREPARATION.value, changelog))
        self.values['time_in_returned'] = sum(get_time_in_status(Status.RETURNED.value, changelog))
        self.values['time_in_ready_for_triage'] = sum(get_time_in_status(Status.READY_FOR_TRIAGE.value, changelog))
        self.values['time_in_ready_to_pull'] = sum(get_time_in_status(Status.READY_FOR_TRIAGE.value, changelog))
        self.values['time_in_triage'] = sum(get_time_in_status(Status.TRIAGE.value, changelog))
        self.values['time_in_committed'] = sum(get_time_in_status(Status.COMMITTED.value, changelog))

        # Process Efficiency = (Hands-on time / Total lead-time) * 100
        hands_off_time = [self.values['time_in_open'],
                          self.values['time_in_returned'],
                          self.values['time_in_ready_for_triage'],
                          self.values['time_in_ready_to_pull']]

        # If lead time is zero then the issue was worked off normal working hours so it should be counted as efficient
        self.values['process_efficiency'] = ((self.values['lead_time'] - sum(hands_off_time)) / self.values['lead_time']) * 100 if self.values['lead_time'] else 100


        # if tpr.key == "LPT-3998":
        #     ipdb.set_trace()

class TPRMetricCollection(object):
    tprs = list()

    metrics = dict()
    reason_metrics = dict()
    throughput_metrics = dict()

    jql_tpr = JQLs.JQL_TPR.value
    jira = None
    jira_project = ""
    jira_issuetype = ""
    jira_issuetype_to_lower = ""
    jira_workflow_end_status = ""
    jira_minus_time = ""
    jira_option_customfield_possible_values = dict()


    def __init__(self, jira, jira_project, jira_issuetype, jira_workflow_end_status, jira_minus_time):
        self.jira = jira
        self.jira_issuetype = jira_issuetype
        self.jira_issuetype_to_lower = jira_issuetype.replace(' ', '_').lower()
        self.jira_project = jira_project
        self.jira_workflow_end_status = jira_workflow_end_status
        self.jira_minus_time = jira_minus_time

        self.metrics = dict()
        self.reason_metrics = dict()
        self.throughput_metrics = dict()
        self.cancellation_metrics = dict()
        self.info_metrics = dict()

        # Populate TPRs with data
        self.tprs = self.refresh_metric_values()

        # If JQL query returned TPRs
        if self.tprs:


            # times_stopped_preparation
            self.metrics['times_stopped_preparation'] = AggregatedMetric(self.jira_issuetype_to_lower + "_times_stopped_preparation", [tpr.values['times_stopped_preparation'] for tpr in self.tprs])
            # times_stopped_triage
            self.metrics['times_stopped_triage'] = AggregatedMetric(self.jira_issuetype_to_lower + "_times_stopped_triage",
                                                                      [tpr.values['times_stopped_triage'] for tpr in self.tprs])
            # times_returned
            self.metrics['times_returned'] = AggregatedMetric(self.jira_issuetype_to_lower + "_times_returned",
                                                   [tpr.values['times_returned'] for tpr in self.tprs])

            # lead_time
            self.metrics['lead_time'] = AggregatedMetric(self.jira_issuetype_to_lower + "_lead_time",
                                              [tpr.values['lead_time'] for tpr in self.tprs])

            # formation_time
            self.metrics['formation_time'] = AggregatedMetric(self.jira_issuetype_to_lower + "_formation_time",
                                              [tpr.values['formation_time'] for tpr in self.tprs])

            # cycle_time
            self.metrics['cycle_time'] = AggregatedMetric(self.jira_issuetype_to_lower + "_cycle_time",
                                               [tpr.values['cycle_time'] for tpr in self.tprs])

            # process_efficiency
            self.metrics['process_efficiency'] = AggregatedMetric(self.jira_issuetype_to_lower + "_process_efficiency",
                                                                [tpr.values['process_efficiency'] for tpr in self.tprs])

            # time_in_open
            self.metrics['time_in_open'] = AggregatedMetric(self.jira_issuetype_to_lower + "_time_in_open",
                                                                [tpr.values['time_in_open'] for tpr in self.tprs])
            # time_in_preparation
            self.metrics['time_in_preparation'] = AggregatedMetric(self.jira_issuetype_to_lower + "_time_in_preparation",
                                                                [tpr.values['time_in_preparation'] for tpr in self.tprs])

            # time_in_returned
            self.metrics['time_in_returned'] = AggregatedMetric(self.jira_issuetype_to_lower + "_time_in_returned",
                                                                [tpr.values['time_in_returned'] for tpr in self.tprs])

            # time_in_ready_for_triage
            self.metrics['time_in_ready_for_triage'] = AggregatedMetric(self.jira_issuetype_to_lower + "_time_in_ready_for_triage",
                                                                [tpr.values['time_in_ready_for_triage'] for tpr in self.tprs])

            # time_in_ready_to_pull
            self.metrics['time_in_ready_to_pull'] = AggregatedMetric(self.jira_issuetype_to_lower + "_time_in_ready_to_pull",
                                                                [tpr.values['time_in_ready_to_pull'] for tpr in self.tprs])

            # time_in_triage
            self.metrics['time_in_triage'] = AggregatedMetric(self.jira_issuetype_to_lower + "_time_in_triage",
                                                                [tpr.values['time_in_triage'] for tpr in self.tprs])

            # time_in_committed
            self.metrics['time_in_committed'] = AggregatedMetric(self.jira_issuetype_to_lower + "_time_in_committed",
                                                                [tpr.values['time_in_committed'] for tpr in self.tprs])



            # weekly_throughput
            self.throughput_metrics['weekly_throughput'] = ThroughputMetric(self.jira_issuetype_to_lower + '_weekly_throughput',
                                                                            self.jira,
                                                                            JQLs.JQL_THROUGHPUT.value.format(self.jira_project,
                                                                                                             self.jira_issuetype,
                                                                                                             self.jira_workflow_end_status,
                                                                                                             self.jira_workflow_end_status,
                                                                                                             TimeValue.MINUS_1_WEEK.value))

            # monthly_throughput
            self.throughput_metrics['monthly_throughput'] = ThroughputMetric(self.jira_issuetype_to_lower + '_monthly_throughput',
                                                                             self.jira,
                                                                             JQLs.JQL_THROUGHPUT.value.format(self.jira_project,
                                                                                                              self.jira_issuetype,
                                                                                                              self.jira_workflow_end_status,
                                                                                                              self.jira_workflow_end_status,
                                                                                                              TimeValue.MINUS_1_MONTH.value))
            # ipdb.set_trace()

            self.info_metrics['estimated_date_from_open_to_closed'] = InfoMetric("estimated_date_from_open_to_closed", {'date': calc_days_from_now_using_working_hours(self.metrics['lead_time'].avg())})
            self.info_metrics['estimated_date_from_open_to_committed'] = InfoMetric("estimated_date_from_open_to_committed", {'date': calc_days_from_now_using_working_hours(self.metrics['formation_time'].avg())})
            self.info_metrics['estimated_date_from_committed_to_closed'] = InfoMetric("estimated_date_from_committed_to_closed", {'date': calc_days_from_now_using_working_hours(self.metrics['cycle_time'].avg())})



    def refresh_metric_values(self):
        return retrieve_tpr_data(self.jira, self.jql_tpr.format(self.jira_project, self.jira_issuetype,
                                                                self.jira_workflow_end_status,
                                                                self.jira_workflow_end_status, self.jira_minus_time))

    def register_prometheus_metrics(self):
        for key in self.metrics:
            self.metrics[key].register_prometheus_metric()
            self.metrics[key].populate_prometheus_metric()
        for key in self.throughput_metrics:
            self.throughput_metrics[key].register_prometheus_metric()
            self.throughput_metrics[key].populate_prometheus_metric()
        for key in self.info_metrics:
            self.info_metrics[key].register_prometheus_metric()
            self.info_metrics[key].populate_prometheus_metric()

    def refresh_prometheus_metrics(self):
        self.tprs = self.refresh_metric_values()
        for key in self.metrics:
            self.metrics[key].refresh([tpr.values[key] for tpr in self.tprs])
            self.metrics[key].populate_prometheus_metric()
        for key in self.throughput_metrics:
            self.throughput_metrics[key].refresh(None)

        # The specific metrics below must be calculated usigng
        self.info_metrics['estimated_date_from_open_to_closed'].refresh({'date': calc_days_from_now_using_working_hours(self.metrics['lead_time'].avg())})
        self.info_metrics['estimated_date_from_open_to_committed'].refresh({'date': calc_days_from_now_using_working_hours(self.metrics['formation_time'].avg())})
        self.info_metrics['estimated_date_from_committed_to_closed'].refresh({'date': calc_days_from_now_using_working_hours(self.metrics['cycle_time'].avg())})

