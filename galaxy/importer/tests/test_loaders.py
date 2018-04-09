# (c) 2012-2017, Ansible by Red Hat
#
# This file is part of Ansible Galaxy
#
# Ansible Galaxy is free software: you can redistribute it and/or modify
# it under the terms of the Apache License as published by
# the Apache Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# Ansible Galaxy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# Apache License for more details.
#
# You should have received a copy of the Apache License
# along with Galaxy.  If not, see <http://www.apache.org/licenses/>.

import unittest
import mock
import pytest

from galaxy import constants
from galaxy.importer import models
from galaxy.importer import loaders
from galaxy.importer.loaders import role as role_loader


class TestRoleMetaParser(unittest.TestCase):

    def setUp(self):
        log_mock = mock.patch('galaxy.importer.loaders.role.LOG')
        self.log = log_mock.start()
        self.addCleanup(log_mock.stop)

    def test_parse_tags(self):
        parser = role_loader.RoleMetaParser({
            'galaxy_tags': ['database', 'sql']
        })
        tags = parser.parse_tags()
        assert tags == ['database', 'sql']

    def test_parse_tags_invalid(self):
        parser = role_loader.RoleMetaParser({
            'galaxy_tags': ['database', 's q l']
        })
        tags = parser.parse_tags()

        assert tags == ['database']
        self.log.warning.assert_called_once_with(
            '"s q l" is not a valid tag. Skipping.')

    def test_parse_categories(self):
        parser = role_loader.RoleMetaParser({
            'categories': ['database', 'sql'],
        })
        tags = parser.parse_tags()

        assert tags == ['database', 'sql']
        self.log.warning.assert_called_once_with(
            'Found "categories" in metadata. Update the metadata '
            'to use "galaxy_tags" rather than categories.')

    def test_parse_platforms(self):
        parser = role_loader.RoleMetaParser({
            'platforms': [
                {'name': 'Ubuntu', 'versions': ['trusty', 'xenial']},
                {'name': 'RHEL', 'versions': ['all']}
            ]
        })
        platforms = parser.parse_platforms()

        assert platforms == [
            models.PlatformInfo('Ubuntu', ['trusty', 'xenial']),
            models.PlatformInfo('RHEL', ['all']),
        ]

    def test_parse_cloud_platforms(self):
        parser = role_loader.RoleMetaParser({
            'cloud_platforms': ['AWX', 'OpenStack']
        })
        platforms = parser.parse_cloud_platforms()

        assert platforms == ['AWX', 'OpenStack']

    def test_parse_dependencies(self):
        pytest.xfail('Not implemented')

    def test_parse_videos(self):
        parser = role_loader.RoleMetaParser({
            'video_links': [{
                'title': 'Google Drive Video',
                'url': 'https://drive.google.com/file/d/gxH17k3EzzJP3g/browse'
            }, {
                'title': 'Vimeo Video',
                'url': 'https://vimeo.com/1733124',
            }, {
                'title': 'Youtube Video',
                'url': 'https://youtu.be/TxHPpfkGms9eDQ'
            }]
        })

        videos = parser.parse_videos()

        assert videos == [
            models.VideoLink(
                'https://drive.google.com/file/d/gxH17k3EzzJP3g/preview',
                'Google Drive Video'),
            models.VideoLink(
                'https://player.vimeo.com/video/1733124',
                'Vimeo Video'),
            models.VideoLink(
                'https://www.youtube.com/embed/TxHPpfkGms9eDQ',
                'Youtube Video'),
        ]


class TestRoleLoader(unittest.TestCase):
    @mock.patch.object(loaders.RoleLoader, '_load_metadata')
    @mock.patch.object(loaders.RoleLoader, '_load_container_yml')
    def test_load_role(self, load_container_yml_mock, load_metadata_mock):
        load_metadata_mock.return_value = {
            'description': 'A test role',
            'author': 'John Smith',
            'min_ansible_version': '2.4.0',
        }
        load_container_yml_mock.return_value = (None, None)

        loader = loaders.RoleLoader(
            constants.ContentType.ROLE, 'roles/test_role', '/tmp/repo',
            metadata_path='meta.yaml')
        role = loader.load()
        role_meta = role.role_meta

        assert role.name == 'test_role'
        assert role.description == 'A test role'
        assert role_meta['role_type'] == constants.RoleType.ANSIBLE
        assert role_meta['author'] == 'John Smith'
        assert role_meta['min_ansible_version'] == '2.4.0'
        assert role_meta['min_ansible_container_version'] is None
