from util.toolkit import jql_results_amount, get_unique_keys_from_list_of_dicts, switch_string_to_var_name
from numpy import min, max, mean
import logging
log = logging.getLogger('root')
from prometheus_client import Gauge, Info
from util.debug_toolkit import debug
import ipdb

class Metric(object):
    def refresh(self, new_value):
        """Refresh metric values"""
        pass

    def register_prometheus_metric(self):
        """Register a prometheus metric"""
        pass

    def populate_prometheus_metric(self):
        """Populate a prometheus metric"""
        pass


class AggregatedMetric(Metric):
    label = ""

    # Aggregate Values
    min_value = 0
    avg_value = 0
    max_value = 0

    # Prometheus Gauge
    min_gauge = None
    avg_gauge = None
    max_gauge = None

    # @debug
    def __init__(self, label, metric_list):
        self.label = label
        self.metric_list = metric_list
        self.refresh(self.metric_list)


    def avg(self, rounded=False):
        return self.avg_value if not rounded else round(self.avg_value, 2)

    def max(self, rounded=False):
        return self.max_value if not rounded else round(self.max_value, 2)

    def min(self, rounded=False):
        return self.min_value if not rounded else round(self.min_value, 2)

    def refresh(self, new_value):
        self.metric_list = new_value

        if self.metric_list:
            self.avg_value = mean(self.metric_list)
            self.max_value = max(self.metric_list)
            self.min_value = min(self.metric_list)

    def register_prometheus_metric(self):
        m_name = self.label
        _min = '_min'
        _avg = '_avg'
        _max = '_max'

        # Register min, max, avg Gauges on prometheus
        self.min_gauge = Gauge(m_name + _min, '')
        self.avg_gauge = Gauge(m_name + _avg, '')
        self.max_gauge = Gauge(m_name + _max, '')

    def populate_prometheus_metric(self):
        # Populate min, max, avg Gauges on prometheus
        self.min_gauge.set(self.min())
        self.avg_gauge.set(self.avg())
        self.max_gauge.set(self.max())


class CompositeAggregatedMetric(Metric):
    label = ""
    composite_metric_list = list()
    am_instances = dict()

    def __init__(self, label, composite_metric_list):
        self.label = label
        self.composite_metric_list = composite_metric_list
        self.am_instances = dict()

        # Create AggregatedMetrics one by one
        reasons = get_unique_keys_from_list_of_dicts(self.composite_metric_list)
        for reason in reasons:
            r_var = switch_string_to_var_name(reason)
            self.am_instances[self.label.format(r_var)] = AggregatedMetric(self.label.format(r_var),
                                                                           [r.get(reason, 0) for r in self.composite_metric_list])

    def refresh(self, new_value):
        self.composite_metric_list = new_value
        reasons = get_unique_keys_from_list_of_dicts(self.composite_metric_list)
        for reason in reasons:
            r_var = switch_string_to_var_name(reason)
            if self.am_instances[self.label.format(r_var)]:
                self.am_instances[self.label.format(r_var)].refresh([r.get(reason, 0) for r in self.composite_metric_list])
            else:
                # If this is a new reason then add it and register/populate to prometheus
                self.am_instances[self.label.format(r_var)] = AggregatedMetric(self.label.format(r_var), [r.get(reason, 0) for r in self.composite_metric_list])
                self.am_instances[self.label.format(r_var)].register_prometheus_metric()
                self.am_instances[self.label.format(r_var)].populate_prometheus_metric()


    def register_prometheus_metric(self):
        for k,v in self.am_instances.items():
            v.register_prometheus_metric()

    def populate_prometheus_metric(self):
        for k,v in self.am_instances.items():
            v.populate_prometheus_metric()

class ThroughputMetric(Metric):
    label = ""
    jql_throughput = ""
    jira = None

    # Throughput Value
    throughput = 0

    # Prometheus Gauge
    throughput_gauge = None

    def __init__(self, label, jira, jql_throughput):
        self.label = label
        self.jira = jira
        self.jql_throughput = jql_throughput
        # self.throughput = self.calculate_metric()

    def calculate_metric(self):
        return jql_results_amount(self.jira, self.jql_throughput)

    def refresh(self, new_value):
        # CAUTION HACK: Throughput metric doesnt need an external value to update itself.
        #               Despite this it uses the same interface as other metrics that require updated values
        #               Sometime later I'll find a better way .......
        self.populate_prometheus_metric()

    def register_prometheus_metric(self):
        # Register Gauge
        self.throughput_gauge = Gauge(self.label, '')

    def populate_prometheus_metric(self):
        # Populate Gauges
        self.throughput = self.calculate_metric()
        self.throughput_gauge.set(self.throughput)


class PercentileMetric(Metric):
    label = ""

    # Metric Value
    percentage = 0

    # Prometheus Gauge
    percentage_gauge = None

    def __init__(self, label, x, y):
        self.label = label
        self.refresh([x, y])

    def refresh(self, new_value):
        self.percentage = (new_value[0] / new_value[1]) * 100

    def register_prometheus_metric(self):
        # Register Gauge
        self.percentage_gauge = Gauge(self.label, '')

    def populate_prometheus_metric(self):
        # Populate Gauges
        self.percentage_gauge.set(self.percentage)


class CancellationMetric(Metric):
    label = ""
    jql_cancellation = ""
    jira = None

    # Throughput Value
    throughput = 0

    # Prometheus Gauge
    throughput_gauge = None

    def __init__(self, label, jira, jql_cancellation):
        self.label = label
        self.jira = jira
        self.jql_cancellation = jql_cancellation
        # self.throughput = self.calculate_metric()

    def calculate_metric(self):
        return jql_results_amount(self.jira, self.jql_cancellation)

    def refresh(self, new_value):
        # CAUTION HACK: Throughput metric doesnt need an external value to update itself.
        #               Despite this it uses the same interface as other metrics that require updated values
        #               Sometime later I'll find a better way .......
        self.populate_prometheus_metric()

    def register_prometheus_metric(self):
        # Register Gauge
        self.throughput_gauge = Gauge(self.label, '')

    def populate_prometheus_metric(self):
        # Populate Gauges
        self.throughput = self.calculate_metric()
        self.throughput_gauge.set(self.throughput)

# class ReasonMetrics(object):
#     def __init__(self, reason_list):
#         log.debug("")


class InfoMetric(Metric):
    label = ""

    # Metric Value dict
    values = {}

    # Prometheus Gauge
    info_metric = None

    def __init__(self, label, value_dict):
        self.label = label
        self.values = value_dict
        # self.refresh(value_dict)

    def refresh(self, new_value):
        self.values = new_value
        self.populate_prometheus_metric()

    def register_prometheus_metric(self):
        # Register Info
        self.info_metric = Info(self.label, '')

    def populate_prometheus_metric(self):
        # Populate Info
        self.info_metric.info(self.values)
