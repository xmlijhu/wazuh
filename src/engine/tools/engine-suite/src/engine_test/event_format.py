from enum import Enum
from engine_test.parser import Parser

class Formats(Enum):
    AUDIT = { "name": "audit", "queue": 49 }
    COMMAND = { "name": "command", "queue": 49 }
    DJB_MULTILOG = "djb-multilog"
    EVENTCHANNEL = { "name": "eventchannel", "origin": "EventChannel", "queue": 102 }
    EVENTLOG = "eventlog"
    FULL_COMMAND = { "name": "full_command", "queue": 49 }
    IIS = "iis"
    JSON = { "name": "json", "queue": 49 }
    MACOS = { "name": "macos", "origin": "macos", "queue": 49 }
    MULTI_LINE_REGEX = "multi-line-regex"
    MULTI_LINE = { "name": "multi-line", "queue": 49 }
    MYSQL_LOG = "mysql_log"
    NMAPG = "nmapg"
    SYSLOG = { "name": "syslog", "queue": 49 }
    REMOTE_SYSLOG = { "name": "remote-syslog", "queue": 50 }

class EventFormat:
    def __init__(self, integration, args):
        self.config = self.update_args(integration, args)

    def parse_events(self, events, config):
        events_parsed = []
        for event in events:
            events_parsed.append(self.parse_event(event, config))
        return events_parsed

    def get_full_location(self, args):
        return Parser.get_full_location(args['agent_id'], args['agent_name'], args['agent_ip'], args['origin'])

    def parse_event(self, event, config):
        return Parser.get_event_ossec_format(event, self.config)

    def update_args(self, integration, args):
        if args['origin'] == None and 'origin' in integration:
            args['origin'] = integration['origin']
        return args

    def format_event(self, event):
        return event

    def get_events(self, events):
        return events
