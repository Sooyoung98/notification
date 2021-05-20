from spaceone.core.service import *

from spaceone.notification.manager import UserChannelManager
from spaceone.notification.model import UserChannel


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class UserChannelService(BaseService):

    def __init__(self, metadata):
        super().__init__(metadata)
        self.user_channel_mgr: UserChannelManager = self.locator.get_manager('UserChannelManager')

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['protocol_id', 'name', 'schema', 'data', 'user_id', 'domain_id'])
    def create(self, params):
        """ Create user Channel

        Args:
            params (dict): {
                'protocol_id': 'str',
                'name': 'str',
                'schema': 'str',
                'data': 'dict',
                'subscriptions': 'list',
                'schedule': 'dict',
                'user_id': 'str',
                'tags': 'dict',
                'domain_id': 'str'
            }

        Returns:
            user_channel_vo (object)
        """

        # Create Protocol
        user_channel_vo: UserChannel = self.user_channel_mgr.create_user_channel(params)

        return user_channel_vo

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['user_channel_id', 'domain_id'])
    def update(self, params):
        """ Update user channel

        Args:
            params (dict): {
                'user_channel_id': 'str',
                'name': 'str',
                'data': 'dict',
                'subscriptions': 'list',
                'notification_level': 'str',
                'schedule': 'dict',
                'tags': 'dict',
                'domain_id': 'str'
            }

        Returns:
            user_channel_vo (object)
        """

        return self.user_channel_mgr.update_user_channel(params)

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['user_channel_id', 'domain_id'])
    def delete(self, params):
        """ Delete user channel

        Args:
            params (dict): {
                'user_channel_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            None
        """

        self.user_channel_mgr.delete_user_channel(params['user_channel_id'], params['domain_id'])

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['user_channel_id', 'domain_id'])
    def enable(self, params):
        """ Enable user channel

        Args:
            params (dict): {
                'user_channel_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            user_channel_vo (object)
        """

        return self.user_channel_mgr.enable_user_channel(params['user_channel_id'], params['domain_id'])

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['user_channel_id', 'domain_id'])
    def disable(self, params):
        """ Disable user channel

        Args:
            params (dict): {
                'user_channel_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            user_channel_vo (object)
        """

        return self.user_channel_mgr.disable_user_channel(params['project_channel_id'], params['domain_id'])

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['user_channel_id_id', 'domain_id'])
    def get(self, params):
        """ Get User Channel

        Args:
            params (dict): {
                'domain_id': 'str',
                'only': 'list'
            }

        Returns:
            user_channel_vo (object)
        """

        return self.user_channel_mgr.get_user_channel(params['user_channel_id'], params['domain_id'],
                                                      params.get('only'))

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['domain_id'])
    @append_query_filter(['user_channel_id_id', 'name', 'state', 'schema', 'secret_id', 'protocol_id', 'user_id', 'domain_id'])
    @change_tag_filter('tags')
    @append_keyword_filter(['user_channel_id'])
    def list(self, params):
        """ List User Channels

        Args:
            params (dict): {
                'user_channel_id': 'str',
                'name': 'str',
                'state': 'str',
                'schema': 'str',
                'secret_id': 'str',
                'protocol_id': 'str',
                'user_id': 'str',
                'query': 'dict (spaceone.api.core.v1.Query)',
                'domain_id': 'str'
            }

        Returns:
            results (list): 'list of user_channel_vo'
            total_count (int)
        """

        query = params.get('query', {})
        return self.project_channel_mgr.list_project_channels(query)

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['query', 'domain_id'])
    @append_query_filter(['domain_id'])
    @change_tag_filter('tags')
    @append_keyword_filter(['user_channel_id', 'name'])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)'
            }

        Returns:
            values (list): 'list of statistics data'
            total_count (int)
        """

        query = params.get('query', {})
        return self.user_channel_mgr.stat_user_channels(query)
