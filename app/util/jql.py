from enum import Enum

class StrValueEnum(Enum):
    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)

class IssueType(StrValueEnum):
    STORY = 'Story'
    BUG = 'Bug'

class TimeValue(StrValueEnum):
    MINUS_1_WEEK = '-1w'
    MINUS_1_MONTH = '-4w'

class Project(StrValueEnum):
    OGST = 'OGST'

class Status(StrValueEnum):
    BACKLOG = 'Backlog'
    READY_FOR_ANALYSIS = 'Ready for Analysis'
    IN_ANALYSIS = 'In Analysis'
    READY_FOR_UXD = 'Ready for UXD'
    IN_UXD = 'In UXD'
    READY_FOR_TECH_REVIEW = 'Ready for Tech Review'
    IN_TECH_REVIEW = 'In Tech Review'
    READY_FOR_REFINEMENT = 'Ready for Refinement'
    IN_REFINEMENT = 'In Refinement'
    READY_FOR_DELIVERY = "Ready for Delivery"
    READY_TO_START = "Ready to Start"
    IN_PROGRESS = "In Progress"
    READY_FOR_CODE_REVIEW = "Ready for Code Review"
    IN_CODE_REVIEW = "In Code Review"
    READY_FOR_TESTING = "Ready for Testing"
    IN_TESTING = "In Testing"
    READY_FOR_SIGN_OFF = "Ready for Sign Off"
    DONE = 'Done'
    CLOSED = 'Closed'
class CustomFieldNames(StrValueEnum):
    REOPEN_REASON = 'Reopen Reason'
    PAUSE_PREPARATION_REASON = 'Pause Preparation Reason'
    PAUSE_WORK_REASON = 'Pause Work Reason'
    REVISION_REASON = 'Revision Reason'
    ORIGIN = 'Origin'

