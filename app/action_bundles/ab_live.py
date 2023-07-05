from action_bundles.action_bundle import ActionBundle
import datetime
import ipdb
import logging

log = logging.getLogger('root')


class ABLive(ActionBundle):
    '''
    classdocs.
    '''

    def __init__(self, parser):
        '''
        Constructor
        '''
        self.parser = parser

        log.info(self.__class__.__name__ + " initialized")
