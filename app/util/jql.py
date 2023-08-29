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

    # Discovery board
    READY_FOR_ANALYSIS = 'Ready for Analysis'
    IN_ANALYSIS = 'In Analysis'
    READY_FOR_UXD = 'Ready for UXD'
    IN_UXD = 'In UXD'
    READY_FOR_TECH_REVIEW = 'Ready for Tech Review'
    IN_TECH_REVIEW = 'In Tech Review'
    READY_FOR_REFINEMENT = 'Ready for Refinement'
    IN_REFINEMENT = 'In Refinement'
    READY_FOR_DELIVERY = "Ready for Delivery"

    # Delivery board
    READY_TO_START = "Ready to Start"
    IN_PROGRESS = "In Progress"
    READY_FOR_CODE_REVIEW = "Ready for Code Review"
    IN_CODE_REVIEW = "In Code Review"
    READY_FOR_TESTING = "Ready for Testing"
    IN_TESTING = "In Testing"
    READY_FOR_SIGN_OFF = "Ready for Sign Off"
    DONE = 'Done'
    CLOSED = 'Closed'

class Filters(StrValueEnum):
    CREATED_DATES_FROM_TO = "AND created >= '{} 00:00' AND created <= '{} 23:59'"
    NOT_CREATED_DATES_FROM_TO = "AND NOT created >= '{} 00:00'"
    RESOLVED_DATES_FROM_TO = "AND resolved >= '{} 00:00' AND resolved <= '{} 23:59'"
    IN_LABEL = "AND labels IN ({})"
    NOT_IN_LABEL = "AND labels NOT IN ({})"
    IN_DEPENDENCY_LABEL = "AND labels IN ('Dependency')"
    NOT_TYPE_EPIC = "AND issuetype NOT IN ('Epic')"
    RELEASED = "AND status IN (Done, Closed) AND Resolution NOT IN (Rejected)"
    REJECTED = "AND status IN (Done, Closed) AND Resolution IN (Rejected)"
    IN_FLIGHT = "AND status NOT IN (Done, Closed)"
    DISCOVERY_IN_FLIGHT = "AND status IN ('Ready for Analysis', 'In Analysis', 'Ready for UXD', 'In UXD'," \
                          "'Ready for Tech Review', 'In Tech Review', 'Ready for Refinement', 'In Refinement')"
    DELIVERY_IN_FLIGHT = "AND status IN ('In Progress', 'Ready for Code Review', 'In Code Review', " \
                         "'Ready for Testing', 'In Testing', 'Ready for Sign Off')"

class JQLs(StrValueEnum):
    JQL_PROJECT = "project = '{}'"


#
# import enum
#
# class JiraStatus(enum.Enum):
#
#     def __new__(cls, *args, **kwds):
#         value = len(cls.__members__) + 1
#         obj = object.__new__(cls)
#         obj._value_ = value
#         return obj
#
#     def __init__(self, status_name, status_wip):
#         self.value = status_name
#         self.wip = status_wip
#
#     BACKLOG = 'Backlog', 0
#
#     # Discovery board
#     READY_FOR_ANALYSIS = 'Ready for Analysis', 0
#     IN_ANALYSIS = 'In Analysis', 0
#     READY_FOR_UXD = 'Ready for UXD', 0
#     IN_UXD = 'In UXD', 0
#     READY_FOR_TECH_REVIEW = 'Ready for Tech Review', 0
#     IN_TECH_REVIEW = 'In Tech Review', 0
#     READY_FOR_REFINEMENT = 'Ready for Refinement', 0
#     IN_REFINEMENT = 'In Refinement', 0
#     READY_FOR_DELIVERY = "Ready for Delivery", 0
#
#     # Delivery board
#     READY_TO_START = "Ready to Start", 0
#     IN_PROGRESS = "In Progress", 0
#     READY_FOR_CODE_REVIEW = "Ready for Code Review", 0
#     IN_CODE_REVIEW = "In Code Review", 0
#     READY_FOR_TESTING = "Ready for Testing", 0
#     IN_TESTING = "In Testing", 0
#     READY_FOR_SIGN_OFF = "Ready for Sign Off", 0
#     DONE = 'Done', 0
#     CLOSED = 'Closed', 0
