import functools

from spaceone.api.notification.v1 import user_channel_pb2
from spaceone.core.pygrpc.message_type import *
from spaceone.core import utils
from spaceone.notification.model.user_channel_model import UserChannel

__all__ = ['UserChannelInfo', 'UserChannelsInfo']


def ScheduleInfo(schedule_info):
    info = {
        'day_of_week': schedule_info.day_of_week,
        'start_hour': schedule_info.start_hour,
        'end_hour': schedule_info.end_hour
    }
    return user_channel_pb2.UserChannelSchedule(**info)


def UserChannelInfo(user_channel_vo: UserChannel, minimal=False):
    info = {
        'user_channel_id': user_channel_vo.user_channel_id,
        'name': user_channel_vo.name,
        'state': user_channel_vo.state
    }

    if not minimal:
        info.update({
            'schema': user_channel_vo.schema,
            'data': change_struct_type(user_channel_vo.data),
            'secret_id': user_channel_vo.secret_id,
            'subscriptions': change_list_value_type(user_channel_vo.subscriptions),
            'schedule': ScheduleInfo(user_channel_vo.schedule),
            'protocol_id': user_channel_vo.protocol_id,
            'user_id': user_channel_vo.user_id,
            'created_at': utils.datetime_to_iso8601(user_channel_vo.created_at),
            'tags': change_struct_type(utils.tags_to_dict(user_channel_vo.tags)),
            'domain_id': user_channel_vo.domain_id
        })

    return user_channel_pb2.UserChannelInfo(**info)


def UserChannelsInfo(user_channel_vos, total_count, **kwargs):
    results = list(map(functools.partial(UserChannelInfo, **kwargs), user_channel_vos))

    return user_channel_pb2.UserChannelsInfo(results=results, total_count=total_count)
