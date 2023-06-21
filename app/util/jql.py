from enum import Enum

class StrValueEnum(Enum):
    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)

class IssueType(StrValueEnum):
    STORY = 'Story'
    BUG = 'Bug'
    DEVELOPMENT_TASK = 'Development Task'
    THROUGHPUT_REQUEST = 'Throughput Request'

class TimeValue(StrValueEnum):
    MINUS_1_WEEK = '-1w'
    MINUS_1_MONTH = '-4w'

class Project(StrValueEnum):
    EIQ = 'EIQ'
    ET = 'ET'
    LPT = 'LPT'

class Status(StrValueEnum):
    OPEN = 'Open'
    PREPARATION = 'Preparation'
    RETURNED = 'Returned'
    READY = 'Ready'
    ANALYSIS = 'Analysis'
    IN_PROGRESS = 'In Progress'
    REOPENED = 'Reopened'
    DONE = 'Done'
    ACCEPTANCE = 'Acceptance'
    RELEASE = 'Release'
    CLOSED = 'Closed'
    REVIEW = 'Review'
    TRIAGE = 'Triage'
    READY_FOR_TRIAGE = 'Ready For Triage'
    READY_TO_PULL = 'Ready To Pull'
    COMMITTED = 'Committed'

class CustomFieldNames(StrValueEnum):
    REOPEN_REASON = 'Reopen Reason'
    PAUSE_PREPARATION_REASON = 'Pause Preparation Reason'
    PAUSE_WORK_REASON = 'Pause Work Reason'
    REVISION_REASON = 'Revision Reason'
    ORIGIN = 'Origin'

class JQLs(StrValueEnum):
    JQL_PBI = "project = '{}' AND issuetype = '{}' AND status = '{}' AND resolution = 'Done' AND status changed to '{}' after {}"
    JQL_TPR = "project = '{}' AND issuetype = '{}' AND status = '{}' AND resolution = 'Done' AND status changed to '{}' after {}"
    JQL_THROUGHPUT = "project = '{}' AND issuetype = '{}' AND status = '{}' AND resolution = 'Done' AND status changed to '{}' after {}"
    JQL_CANCELLED = "project = '{}' AND issuetype = '{}' AND status = '{}' AND resolution = 'Cancelled' AND status changed to '{}' after {}"
