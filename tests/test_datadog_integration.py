# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import pytest
import mock

from gcdt_datadog_integration.datadog_notification import datadog_notification,\
    datadog_error, _datadog_get_tags


def test_datadog_notification_invalid_token():
    context = {
        'tool': 'kumo',
        'command': 'deploy',
        'cloudformation.StackName': 'infra-dev-sample-stack'
    }
    config = {
        'kumo': {
            'cloudformation': {
                'StackName': 'infra-dev-test-stack'
            }
        },
        'plugins': {
            'gcdt_datadog_integration': {
                'datadog_api_key': 'xoxp-12345678901-12345678901-12345678901-4e6es20339'
            }
        }
    }
    with pytest.raises(ValueError) as e:
        datadog_notification((context, config))
    assert e.match(r'.*Request forbidden by administrative rules')


@mock.patch('gcdt_datadog_integration.datadog_notification._datadog_event')
@mock.patch('gcdt_datadog_integration.datadog_notification._datadog_metric')
def test_datadog_notification(mocked_datadog_metric, mocked_datadog_event):
    context = {'tool': 'kumo', 'command': 'deploy',
               '_awsclient': 'awsclient-test'}
    config = {
        'kumo': {
            'cloudformation': {
                'StackName': 'infra-dev-test-stack'
            }
        },
        'plugins': {
            'gcdt_datadog_integration': {
                'datadog_api_key': 'foo_bar_1234'
            }
        }
    }
    datadog_notification((context, config))

    mocked_datadog_metric.assert_called_once_with(
        'foo_bar_1234', 'gcdt.kumo', ['tool:kumo', 'command:deploy'])
    mocked_datadog_event.assert_called_once_with(
        'foo_bar_1234', 'gcdt.kumo', ['tool:kumo', 'command:deploy'],
        text='kumo bot: deploy complete for stack \'infra-dev-test-stack\'')


@mock.patch('gcdt_datadog_integration.datadog_notification._datadog_event')
@mock.patch('gcdt_datadog_integration.datadog_notification._datadog_metric')
def test_datadog_notification_tenkai(mocked_datadog_metric, mocked_datadog_event):
    context = {'tool': 'tenkai', 'command': 'deploy',
               '_awsclient': 'awsclient-test'}
    config = {
        'tenkai': {
            'codedeploy': {
                'deploymentGroupName': 'infra-dev-test-stack-deployment-grp'
            }
        },
        'plugins': {
            'gcdt_datadog_integration': {
                'datadog_api_key': 'foo_bar_1234'
            }
        }
    }
    datadog_notification((context, config))

    mocked_datadog_metric.assert_called_once_with(
        'foo_bar_1234', 'gcdt.tenkai', ['tool:tenkai', 'command:deploy'])
    mocked_datadog_event.assert_called_once_with(
        u'foo_bar_1234', u'gcdt.tenkai', ['tool:tenkai', 'command:deploy'],
        text='tenkai bot: deployed deployment group \'infra-dev-test-stack-deployment-grp\'')


@mock.patch('gcdt_datadog_integration.datadog_notification._datadog_metric')
def test_datadog_error(mocked_datadog_metric):
    context = {'tool': 'kumo', 'command': 'deploy',
               '_awsclient': 'awsclient-test',
               'error': 'my error message'}
    config = {
        'tenkai': {
            'codedeploy': {
                'deploymentGroupName': 'infra-dev-test-stack-deployment-grp'
            }
        },
        'plugins': {
            'gcdt_datadog_integration': {
                'datadog_api_key': 'foo_bar_1234'
            }
        }
    }
    datadog_error((context, config))

    mocked_datadog_metric.assert_called_once_with(
        'foo_bar_1234', 'gcdt.error', ['tool:kumo', 'command:deploy',
                                      'error:my error message'])


def test_datadog_get_tags():
    context = {'a': '1', 'b': '2', '_c': '3'}
    actual = _datadog_get_tags(context)
    assert actual == ['a:1', 'b:2']


# for now we send the metrics directly (not statsd)
'''
class FakeSocket(object):
    """ A fake socket for testing datadog statsd. """

    def __init__(self):
        self.payloads = deque()

    def send(self, payload):
        assert type(payload) == six.binary_type
        self.payloads.append(payload)

    def recv(self):
        try:
            return self.payloads.popleft().decode('utf-8')
        except IndexError:
            return None

    def __repr__(self):
        return str(self.payloads)

def test_datadog_notification():
    socket = datadog.statsd.socket = FakeSocket()
    metric = 'gcdt.kumo.deploy'
    tags = ['env:dev', 'stack_name:gcdt-supercars-dev']

    datadog_notification(metric, tags)
    assert_equal(socket.recv(),
                 'gcdt.kumo.deploy:1|c|#env:dev,stack_name:gcdt-supercars-dev')
'''
