# -*- coding: utf-8 -*-
"""gcdt-plugin to handle datadog notifications."""
from __future__ import unicode_literals, print_function
import logging

import datadog

from gcdt import gcdt_signals


log = logging.getLogger(__name__)


def _datadog_event(api_key, title, tags, text=''):
    """Sent counter metrics to datadog

    :param metric: metrics like 'gcdt.kumo.deploy'
    :param text: message text
    :param tags: tags like ['version:1', 'application:web']
    """
    datadog.initialize(api_key=api_key)
    datadog.api.Event.create(title=title, tags=tags, text=text)


def _datadog_event_detail(api_key, context, message):
    """This is a temporary means to add events without changing the structure
    of the gcdt tools.

    :param context:
    :param message:
    """
    metric = 'gcdt.%s' % context['tool']
    tags = _datadog_get_tags(context)
    _datadog_event(api_key, metric, tags, text=message)


def _datadog_metric(api_key, metric, tags):
    """Sent counter metrics to datadog

    :param metric: metrics like 'gcdt.kumo.deploy'
    :param text: message text
    :param tags: tags like ['version:1', 'application:web']
    """
    datadog.initialize(api_key=api_key)
    datadog.api.Metric.send(metric=metric, points=1, tags=tags, type='counter')


def _datadog_get_tags(context):
    tags = ['%s:%s' % (k, v) for k,v in context.iteritems() if not k.startswith('_')]
    return tags


def datadog_notification(params):
    """Send a datadog notification.
    If we do not have a api_key we do not send out notifications.
    :param params: context, config (context - the _awsclient, etc..
                   config - The stack details, etc..)
    """
    context, config = params
    tool = context['tool']
    if 'plugins' not in config or 'gcdt_datadog_integration' not in config['plugins']:
        return
    api_key = config['plugins']['gcdt_datadog_integration'].get('datadog_api_key', None)
    if api_key.startswith('lookup'):
        return
    metric = 'gcdt.%s' % context['tool']
    tags = _datadog_get_tags(context)

    _datadog_metric(api_key, metric, tags)

    if context['tool'] == 'kumo':
        if context['command'] in ['deploy', 'delete']:
            event = '%s bot: %s complete for stack \'%s\'' % (
                context['tool'],
                context['command'],
                config[tool]['cloudformation'].get('StackName'))
            _datadog_event_detail(api_key, context, event)
    elif context['tool'] == 'tenkai':
        if context['command'] in ['deploy']:
            event = '%s bot: deployed deployment group \'%s\'' % (
                context['tool'],
                config[tool]['codedeploy'].get('deploymentGroupName'))
            _datadog_event_detail(api_key, context, event)
    elif context['tool'] == 'ramuda':
        if context['command'] in ['deploy', 'delete']:
            event = '%s bot: %s complete for lambda function \'%s\'' % (
                context['tool'],
                context['command'],
                config[tool]['lambda'].get('name'))
            _datadog_event_detail(api_key, context, event)
        if context['command'] in ['wiring', 'unwire']:
            event = '%s bot: %s lambda function \'%s\' with alias \'ACTIVE\'' % (
                context['tool'],
                context['command'],
                config[tool]['lambda'].get('name'))
            _datadog_event_detail(api_key, context, event)
        elif context['command'] in ['rollback']:
            if '<version>' in context['_arguments'] and context['_arguments']['<version>']:
                message = '%s bot: rolled back lambda function \'%s\' to version \'%s\'' % (
                    context['tool'],
                    config[tool]['lambda'].get('name'),
                    context['_arguments']['<version>']
                )
            else:
                message = '%s bot: rolled back lambda function \'%s\' to previous version' % (
                    context['tool'],
                    config[tool]['lambda'].get('name')
                )
            _datadog_event_detail(api_key, context, event)
    elif context['tool'] == 'yugen':
        if context['command'] in ['deploy', 'delete']:
            event = '%s bot: %s complete for api \'%s\'' % (
                context['tool'],
                context['command'],
                config[tool]['api'].get('name'))
            _datadog_event_detail(api_key, context, event)


def datadog_error(params):
    """Send a datadog error.
    :param params: context, config (context - the _awsclient, etc..
                   config - The stack details, etc..)
    """
    context, config = params
    if 'plugins' not in config or 'gcdt_datadog_integration' not in config['plugins']:
        return
    api_key = config['plugins']['gcdt_datadog_integration'].get('datadog_api_key', None)
    if api_key.startswith('lookup'):
        return
    tags = _datadog_get_tags(context)
    # note: 'error' is a tag in context
    _datadog_metric(api_key, 'gcdt.error', tags)


def register():
    """Please be very specific about when your plugin needs to run and why.
    E.g. run the sample stuff after at the very beginning of the lifecycle
    """
    gcdt_signals.command_finalized.connect(datadog_notification)
    gcdt_signals.error.connect(datadog_error)


def deregister():
    gcdt_signals.command_finalized.disconnect(datadog_notification)
    gcdt_signals.error.disconnect(datadog_error)
