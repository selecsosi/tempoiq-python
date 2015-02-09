import operator
from rule import Rule, Condition, Trigger, Filter, Webhook, Email
from device import Device
from sensor import Sensor
from log import RuleLog, RuleUsage, RuleUsageMetric
from query.selection import Selection, ScalarSelector, AndClause, OrClause
from tempoiq.temporal.validate import convert_iso_stamp


def decode_attributes_selector(selector, selection_type='devices'):
    return ScalarSelector(selection_type, 'attributes', selector['attributes'])


def decode_key_selector(selector, selection_type='devices'):
    return ScalarSelector(selection_type, 'key', selector['key'])


def decode_scalar_selector(selector, selection_type='devices'):
    key = selector.keys()[0]
    if key == 'attributes':
        return decode_attributes_selector(selector, selection_type)
    else:
        return decode_key_selector(selector, selection_type)


def decode_compound_clause(selectors, selection_type='devices', t='and'):
    if t == 'and':
        clause = AndClause()
    else:
        clause = OrClause()

    for s in selectors:
        subt = s.keys()[0]
        if subt in ['and', 'or']:
            subclause = decode_compound_clause(s[subt], selection_type, subt)
            clause.add(subclause)
        else:
            parsed = decode_scalar_selector(s, selection_type)
            clause.add(parsed)

    return clause


def decode_selection(selection, selection_type='devices'):
    s = Selection()
    if selection == 'all':
        return s
    for k in selection:
        if k in ['and', 'or']:
            selector = decode_compound_clause(selection[k], selection_type, k)
        else:
            selector = decode_scalar_selector(selection, selection_type)
        s.add(selector)
    return s


def merge_metrics(metrics):
    tstamp_to_metric = {}
    for m in metrics:
        if tstamp_to_metric.get(m.timestamp) is not None:
            tstamp_to_metric[m.timestamp].add_metric(
                m.metric_name,
                m.metric_value)
        else:
            merged = RuleUsage(m.timestamp)
            merged.add_metric(m.metric_name, m.metric_value)
            tstamp_to_metric[m.timestamp] = merged
    return [v for v in
            sorted(tstamp_to_metric.itervalues(),
                   key=operator.attrgetter('timestamp'))]


class DeviceDecoder(object):
    def __init__(self):
        pass

    def __call__(self, dct):
        if dct.get('sensors'):  # Main device object
            return self.decode_device(dct)
        return dct

    def decode_device(self, dct):
        key = dct['key']
        attributes = dct['attributes']
        name = dct['name']
        sensors = []
        for s in dct['sensors']:
            _sensor = Sensor(s['key'], name=s['name'],
                             attributes=s['attributes'])
            sensors.append(_sensor)

        return Device(key, name=name, attributes=attributes, sensors=sensors)


class TempoIQDecoder(object):
    def __init__(self):
        self.decoder = self.decode

    def __call__(self, dct):
        return self.decoder(dct)

    def decode(self, dct):
        if dct.get('rule'):
            return self.decode_rule(dct)
        return dct

    def decode_rule(self, rule):
        name = rule['rule']['name']
        alert_by = rule['alerts']
        key = rule['rule']['key']

        selection = {
            'devices': decode_selection(rule['search']['filters']['devices'],
                                        selection_type='devices'),
            'sensors': decode_selection(rule['search']['filters']['sensors'],
                                        selection_type='sensors'),
            }

        conditions = []
        for c in rule['rule']['conditions']:
            trigger = Trigger(c['trigger']['name'],
                              c['trigger']['arguments'])
            filters = []
            for f in c['filter']['and']:
                _filter = Filter(f['operation'], f['type'], f['arguments'])
                filters.append(_filter)
            condition = Condition(filters, trigger)
            conditions.append(condition)

        action_json = rule['rule']['actions'][0]
        if action_json.get('url'):
            action = Webhook(action_json['url'])
        else:
            action = Email(action_json['address'])

        status = rule['rule'].get('status')

        return Rule(name, alert_by=alert_by, key=key, conditions=conditions,
                    action=action, selection=selection, status=status)

    def decode_rule_list(self, dct):
        rules = []
        for key, name in dct.iteritems():
            rules.append(Rule(name, key=key))
        return rules

    def decode_rule_logs(self, dct):
        if dct.get('data') is not None:
            return dct['data']
        else:
            return RuleLog(dct['logId'], dct['event'],
                           convert_iso_stamp(dct['createdAt']))

    def decode_rule_usage(self, dct):
        if dct.get('data') is not None:
            return merge_metrics(dct['data'])
        else:
            return RuleUsageMetric(convert_iso_stamp(dct['timestamp']),
                                   dct['metricType'], dct['count'])

    def decode_selection(self, dct):
        pass
