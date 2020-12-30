'''
Created on 26-Nov-2020

@author: root
'''


''' attribute names'''

ATTR_CHUNK_COLLECTOR = "chunk_collector"

ATTR_CONTENT = "content"

ATTR_NAME = "name"

ATTR_LOG_NAME = "log_name"



''' topic names'''

TOPIC_ANY = "*"

TOPIC_LOG_ACTIONS = "/log/actions"

TOPIC_LOGMONITORING = "/logging"

TOPIC_SYSMONITORING = "/stats"

TOPIC_PING = "/ping"

TOPIC_EVENTS = "/events"

TOPIC_SCRIPTS = "/script"



''' Moduile names'''

SYSTEM_MODULE = "sysmon"

FILE_MANAGER_MODULE = "file_manager"

PUBSUBHUB_MODULE = "pubsub"

LOG_MANAGER_MODULE = "log_monitor"

PINGER_MODULE = "pinger"

TARGET_DELEGATE_MODULE = "target_delegate"

RPC_GATEWAY_MODULE = "rpc_gateway"

MQTT_GATEWAY_MODULE = "mqtt_gateway"

SMTP_MAILER_MODULE = "smtp_mailer"

SCRIPT_RUNNER_MODULE = "script_runner"

SCHEDULER_MODULE = "scheduler"

BOT_SERVICE_MODULE = "service_bot"

REACTION_ENGINE_MODULE = "reaction_engine"

ACTION_DISPATCHER_MODULE = "action_dispatcher"



''' client channel names'''

CHANNEL_HTTP_REST = "http_rest_channel"

CHANNEL_WEBSOCKET_RPC = "websocket_rpc_channel"

CHANNEL_SMTP_MAILER = "smtp_mailer_channel"

CHANNEL_RTMP = "rtmp_channel"

CHANNEL_CHAT_BOT = "chat_bot_channel"

CHANNEL_MQTT = "mqtt_channel"



''' client type'''

PROACTIVE_CLIENT_TYPE = "proactive_client_type"

REACTIVE_CLIENT_TYPE = "reactive_client_type"

def built_in_client_types():
    return [PROACTIVE_CLIENT_TYPE, REACTIVE_CLIENT_TYPE]