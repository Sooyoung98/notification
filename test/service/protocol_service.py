import unittest
from unittest.mock import patch
from mongoengine import connect, disconnect

from spaceone.core.unittest.result import print_data
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.model.mongo_model import MongoModel
from spaceone.core.transaction import Transaction
from spaceone.notification.error import *
from spaceone.notification.service.protocol_service import ProtocolService
from spaceone.notification.model.protocol_model import Protocol
from spaceone.notification.connector.notification_plugin_connector import NotificationPluginConnector
from spaceone.notification.connector.plugin_connector import PluginConnector
from spaceone.notification.connector.repository_connector import RepositoryConnector
from spaceone.notification.connector.secret_connector import SecretConnector
from spaceone.notification.info.protocol_info import *
from spaceone.notification.info.common_info import StatisticsInfo
from test.factory.protocol_factory import ProtocolFactory


class TestProtocolService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(package='spaceone.notification')
        connect('test', host='mongomock://localhost')

        cls.domain_id = utils.generate_id('domain')
        cls.transaction = Transaction({
            'service': 'notificaiton',
            'api_class': 'Protocol'
        })
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        disconnect()

    @patch.object(MongoModel, 'connect', return_value=None)
    def tearDown(self, *args) -> None:
        print()
        print('(tearDown) ==> Delete all protocol')
        protocol_vos = Protocol.objects.filter()
        protocol_vos.delete()

    @patch.object(MongoModel, 'connect', return_value=None)
    @patch.object(RepositoryConnector, '__init__', return_value=None)
    @patch.object(SecretConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, 'get_plugin_endpoint', return_value='grpc://plugin.spaceone.dev:50051')
    @patch.object(NotificationPluginConnector, 'initialize', return_value=None)
    @patch.object(SecretConnector, 'get_secret_data', return_value={'data': {}})
    @patch.object(RepositoryConnector, 'get_plugin_versions', return_value=['1.0', '1.1', '1.2'])
    @patch.object(RepositoryConnector, 'get_plugin')
    @patch.object(SecretConnector, 'list_secrets')
    @patch.object(NotificationPluginConnector, 'init')
    def test_create_protocol(self, mock_plugin_verify, mock_list_secrets, mock_get_plugin, *args):
        secret_id = utils.generate_id('secret')
        plugin_id = utils.generate_id('plugin')
        plugin_version = '1.0'

        mock_plugin_verify.return_value = {
            'metadata': {
                'supported_schema': ['slack_webhook', 'spaceone_user'],
                'data_type': 'PLAIN_TEXT'
            }
        }

        mock_list_secrets.return_value = {
            'results': [{
                'secret_id': secret_id,
                'schema': 'aws_access_key'
            }],
            'total_count': 1
        }

        mock_get_plugin.return_value = {
            'name': 'notification-slack-protocol',
            'service_type': 'notification.Protocol',
            'image': 'pyengine/notification-slack-protocol',
            'capability': {
                'supported_schema': ['slack_webhook', 'spaceone_user'],
                'data_type': 'PLAIN_TEXT'
            },
            'tags': {
                'description': 'Notification Slack Protocol',
                'spaceone:plugin_name': 'notification-slack-protocol'
            }
        }

        params = {
            'name': 'Slack Notification',
            'plugin_info': {
                'plugin_id': plugin_id,
                'version': plugin_version,
                'options': {},
            },
            'tags': {
                utils.random_string(): utils.random_string()
            },
            'domain_id': self.domain_id
        }

        self.transaction.method = 'create'
        protocol_svc = ProtocolService(transaction=self.transaction)
        protocol_vo = protocol_svc.create(params.copy())

        print_data(protocol_vo.to_dict(), 'test_create_protocol')
        ProtocolInfo(protocol_vo)

        self.assertIsInstance(protocol_vo, Protocol)
        self.assertEqual(params['name'], protocol_vo.name)
        self.assertEqual(params['tags'], protocol_vo.tags)
        self.assertEqual(params['domain_id'], protocol_vo.domain_id)

    '''
    @patch.object(MongoModel, 'connect', return_value=None)
    @patch.object(RepositoryConnector, '__init__', return_value=None)
    @patch.object(SecretConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, 'get_plugin_endpoint', return_value='grpc://plugin.spaceone.dev:50051')
    @patch.object(MonitoringPluginConnector, 'initialize', return_value=None)
    @patch.object(SecretConnector, 'get_secret_data', return_value={'data': {}})
    @patch.object(RepositoryConnector, 'get_plugin_versions', return_value=['1.0', '1.1', '1.2'])
    @patch.object(RepositoryConnector, 'get_plugin')
    @patch.object(SecretConnector, 'list_secrets')
    @patch.object(MonitoringPluginConnector, 'init')
    def test_register_metric_data_source_with_provider(self, mock_plugin_init, mock_list_secrets,
                                                       mock_get_plugin, *args):
        plugin_id = utils.generate_id('plugin')
        plugin_version = '1.0'

        mock_plugin_init.return_value = {
            'metadata': {
                'supported_resource_type': ['inventory.Server', 'inventory.CloudService'],
                'supported_stat': ['AVERAGE', 'MAX', 'MIN'],
                'required_keys': ['reference.resource_id']
            }
        }

        mock_list_secrets.return_value = {
            'results': [{
                'secret_id': utils.generate_id('secret'),
                'schema': 'aws_access_key'
            }],
            'total_count': 1
        }

        mock_get_plugin.return_value = {
            'capability': {
                'use_resource_secret': True,
                'supported_schema': ['aws_access_key', 'aws_assume_role'],
                'monitoring_type': 'METRIC'
            },
            'provider': 'aws'
        }

        params = {
            'name': 'AWS CloudWatch',
            'plugin_info': {
                'plugin_id': plugin_id,
                'version': plugin_version,
                'options': {},
                'provider': 'aws'
            },
            'tags': {
                'tag_key': 'tag_value'
            },
            'domain_id': self.domain_id
        }

        self.transaction.method = 'register'
        data_source_svc = DataSourceService(transaction=self.transaction)
        data_source_vo = data_source_svc.register(params.copy())

        print_data(data_source_vo.to_dict(), 'test_register_metric_data_source_with_provider')
        DataSourceInfo(data_source_vo)

        self.assertIsInstance(data_source_vo, DataSource)
        self.assertEqual(params['name'], data_source_vo.name)
        self.assertEqual(params['tags'], utils.tags_to_dict(data_source_vo.tags))
        self.assertEqual(params['domain_id'], data_source_vo.domain_id)
    '''

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_update_protocol(self, *args):
        protocol_vo = ProtocolFactory(domain_id=self.domain_id)
        params = {
            'protocol_id': protocol_vo.protocol_id,
            'name': 'Update New Protocol',
            'tags': {
                'update_key': 'update_value'
            },
            'domain_id': self.domain_id
        }

        self.transaction.method = 'update'
        protocol_svc = ProtocolService(transaction=self.transaction)
        update_protocol_vo = protocol_svc.update(params.copy())

        print_data(update_protocol_vo.to_dict(), 'test_update_protocol')
        ProtocolInfo(update_protocol_vo)

        self.assertIsInstance(update_protocol_vo, Protocol)
        self.assertEqual(update_protocol_vo.protocol_id, protocol_vo.protocol_id)
        self.assertEqual(params['name'], update_protocol_vo.name)
        self.assertEqual(params['tags'], update_protocol_vo.tags)

    @patch.object(MongoModel, 'connect', return_value=None)
    @patch.object(RepositoryConnector, '__init__', return_value=None)
    @patch.object(RepositoryConnector, 'get_plugin_versions', return_value=['1.0', '1.1', '1.2'])
    @patch.object(RepositoryConnector, 'get_plugin')
    @patch.object(SecretConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, 'get_plugin_endpoint', return_value='grpc://plugin.spaceone.dev:50051')
    @patch.object(NotificationPluginConnector, 'initialize', return_value=None)
    @patch.object(SecretConnector, 'get_secret_data', return_value={'data': {}})
    @patch.object(SecretConnector, 'list_secrets')
    @patch.object(NotificationPluginConnector, 'init')
    def test_update_protocol_plugin(self, mock_plugin_init, mock_list_secrets, *args):
        plugin_version = '1.2'
        update_options = {
            'test': 'xxxxx'
        }

        mock_plugin_init.return_value = {
            'metadata': {
                'supported_resource_type': ['inventory.Server'],
                'supported_stat': ['AVERAGE', 'MAX', 'MIN'],
                'required_keys': ['reference.resource_id']
            }
        }

        mock_list_secrets.return_value = {
            'results': [{
                'secret_id': utils.generate_id('secret')
            }],
            'total_count': 1
        }

        protocol_vo = ProtocolFactory(domain_id=self.domain_id)
        params = {
            'protocol_id': protocol_vo.protocol_id,
            'version': plugin_version,
            'options': update_options,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'update_plugin'
        protocol_svc = ProtocolService(transaction=self.transaction)
        new_protocol_vo = protocol_svc.update_plugin(params.copy())

        print_data(new_protocol_vo.to_dict(), 'test_update_protocol_plugin')
        ProtocolInfo(new_protocol_vo)

        self.assertIsInstance(new_protocol_vo, Protocol)
        self.assertEqual(new_protocol_vo.protocol_id, protocol_vo.protocol_id)
        self.assertEqual(params['version'], new_protocol_vo.plugin_info.version)
        self.assertEqual(params['options'], new_protocol_vo.plugin_info.options)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_enable_protocol(self, *args):
        protocol_vo = ProtocolFactory(domain_id=self.domain_id, state='DISABLED')
        params = {
            'protocol_id': protocol_vo.protocol_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'enable'
        protocol_svc = ProtocolService(transaction=self.transaction)
        updated_protocol_vo = protocol_svc.enable(params.copy())

        print_data(updated_protocol_vo.to_dict(), 'test_enable_protocol')
        ProtocolInfo(updated_protocol_vo)

        self.assertIsInstance(updated_protocol_vo, Protocol)
        self.assertEqual(updated_protocol_vo.protocol_id, protocol_vo.protocol_id)
        self.assertEqual('ENABLED', updated_protocol_vo.state)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_disable_protocol(self, *args):
        protocol_vo = ProtocolFactory(domain_id=self.domain_id, state='ENABLED')
        params = {
            'protocol_id': protocol_vo.protocol_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'disable'
        protocol_svc = ProtocolService(transaction=self.transaction)
        updated_protocol_vo = protocol_svc.disable(params.copy())

        print_data(updated_protocol_vo.to_dict(), 'test_disable_protocol')
        ProtocolInfo(updated_protocol_vo)

        self.assertIsInstance(updated_protocol_vo, Protocol)
        self.assertEqual(updated_protocol_vo.protocol_id, protocol_vo.protocol_id)
        self.assertEqual('DISABLED', updated_protocol_vo.state)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_delete_protocol(self, *args):
        protocol_vo = ProtocolFactory(domain_id=self.domain_id)
        params = {
            'protocol_id': protocol_vo.protocol_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'delete'
        protocol_svc = ProtocolService(transaction=self.transaction)
        result = protocol_svc.delete(params)

        self.assertIsNone(result)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_get_protocol(self, *args):
        protocol_vo = ProtocolFactory(domain_id=self.domain_id)
        params = {
            'protocol_id': protocol_vo.protocol_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'get'
        protocol_svc = ProtocolService(transaction=self.transaction)
        protocol_vo = protocol_svc.get(params)

        print_data(protocol_vo.to_dict(), 'test_get_protocol')
        ProtocolInfo(protocol_vo)

        self.assertIsInstance(protocol_vo, Protocol)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_list_protocol_by_protocol_id(self, *args):
        protocol_vos = ProtocolFactory.build_batch(10, domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), protocol_vos))

        params = {
            'protocol_id': protocol_vos[0].protocol_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'list'
        protocol_svc = ProtocolService(transaction=self.transaction)
        protocol_vos, total_count = protocol_svc.list(params)
        ProtocolsInfo(protocol_vos, total_count)

        self.assertEqual(len(protocol_vos), 1)
        self.assertIsInstance(protocol_vos[0], Protocol)
        self.assertEqual(total_count, 1)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_list_protocols_by_name(self, *args):
        protocol_vos = ProtocolFactory.build_batch(10, domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), protocol_vos))

        params = {
            'name': protocol_vos[0].name,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'list'
        protocol_svc = ProtocolService(transaction=self.transaction)
        protocol_vos, total_count = protocol_svc.list(params)
        ProtocolsInfo(protocol_vos, total_count)

        self.assertEqual(len(protocol_vos), 1)
        self.assertIsInstance(protocol_vos[0], Protocol)
        self.assertEqual(total_count, 1)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_list_protocols_by_protocol_type(self, *args):
        internal_protocol_vos = ProtocolFactory.build_batch(5, protocol_type='INTERNAL', domain_id=self.domain_id)
        external_protocol_vos = ProtocolFactory.build_batch(10, protocol_type='EXTERNAL', domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), external_protocol_vos))

        params = {
            'protocol_type': 'EXTERNAL',
            'domain_id': self.domain_id
        }

        self.transaction.method = 'list'
        protocol_svc = ProtocolService(transaction=self.transaction)
        protocol_vos, total_count = protocol_svc.list(params)
        ProtocolsInfo(protocol_vos, total_count)

        self.assertEqual(len(protocol_vos), 10)
        self.assertIsInstance(protocol_vos[0], Protocol)
        self.assertEqual(total_count, 10)

    '''
    @patch.object(MongoModel, 'connect', return_value=None)
    def test_list_protocols_by_tag(self, *args):
        ProtocolFactory(tags={'xxxxx': 'aaaaaa', 'yyyyy': 'bbbbbb'}, domain_id=self.domain_id)
        protocol_vos = ProtocolFactory.build_batch(9, domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), protocol_vos))

        params = {
            'query': {
                'filter': [{
                    'k': 'tags.xxxxx',
                    'v': 'aaaaaa',
                    'o': 'eq'
                }]
            },
            'domain_id': self.domain_id
        }

        for protocol_vo in protocol_vos:
            print(protocol_vo.tags)

        self.transaction.method = 'list'
        protocol_svc = ProtocolService(transaction=self.transaction)
        protocol_vos, total_count = protocol_svc.list(params)
        ProtocolsInfo(protocol_vos, total_count)

        self.assertEqual(len(protocol_vos), 1)
        self.assertIsInstance(protocol_vos[0], Protocol)
        self.assertEqual(total_count, 1)
    '''

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_stat_protocol(self, *args):
        protocol_vos = ProtocolFactory.build_batch(10, domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), protocol_vos))

        params = {
            'domain_id': self.domain_id,
            'query': {
                'aggregate': [{
                    'group': {
                        'keys': [{
                            'key': 'protocol_id',
                            'name': 'Id'
                        }],
                        'fields': [{
                            'operator': 'count',
                            'name': 'Count'
                        }]
                    }
                }, {
                    'sort': {
                        'key': 'Count',
                        'desc': True
                    }
                }]
            }
        }

        self.transaction.method = 'stat'
        protocol_svc = ProtocolService(transaction=self.transaction)
        values = protocol_svc.stat(params)
        StatisticsInfo(values)

        print_data(values, 'test_stat_protocol')

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_stat_protocol_distinct(self, *args):
        protocol_vos = ProtocolFactory.build_batch(10, domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), protocol_vos))

        params = {
            'domain_id': self.domain_id,
            'query': {
                'distinct': 'protocol_id',
                'page': {
                    'start': 2,
                    'limit': 3
                }
            }
        }

        self.transaction.method = 'stat'
        protocol_svc = ProtocolService(transaction=self.transaction)
        values = protocol_svc.stat(params)
        StatisticsInfo(values)

        print_data(values, 'test_stat_protocol_distinct')


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)