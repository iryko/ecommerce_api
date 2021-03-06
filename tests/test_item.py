import json
from werkzeug.datastructures import FileStorage
from http.client import CREATED
from http.client import NO_CONTENT
from http.client import NOT_FOUND
from http.client import OK
from http.client import BAD_REQUEST
from models import Item
import hashlib
import uuid
import os

from .base_test import BaseTest


class TestItems(BaseTest):
    def test_get_items__empty(self):
        resp = self.app.get('/items/')
        assert resp.status_code == OK
        assert json.loads(resp.data.decode()) == []

    def test_get_items(self):
        item1 = self.create_item()
        item2 = self.create_item()

        resp = self.app.get('/items/')
        assert resp.status_code == OK
        assert json.loads(resp.data.decode()) == [item1.json(), item2.json()]

    def test_create_item__success(self):
        user = self.create_user()

        new_item_data = {
            'name': 'Item one',
            'price': 15,
            'description': 'desc1',
            'category': 'poligoni',
            'availability': 11
        }

        resp = self.open_with_auth(
            '/items/', 'post', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == CREATED

        item_from_server = json.loads(resp.data.decode())
        item_from_db = Item.get(Item.uuid == item_from_server['uuid']).json()

        assert len(Item.select()) == 1
        assert item_from_db == item_from_server

        item_from_server.pop('uuid')
        assert item_from_server == new_item_data

    def test_create_item__failure_invalid_field_value(self):
        user = self.create_user()
        new_item_data = {
            'name': 'Item one',
            'price': 15,
            'description': 'desc1',
            'category': 'poligoni',
            'availability': -8
        }

        resp = self.open_with_auth(
            '/items/', 'post', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == BAD_REQUEST

    def test_create_item__failure_empty_field(self):
        user = self.create_user()

        new_item_data = {
            'name': '',
            'price': 10,
            'description': 'Description one',
            'category': 'Category one',
            'availability': 11
        }
        resp = self.open_with_auth(
            '/items/', 'post', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == BAD_REQUEST
        assert len(Item.select()) == 0

    def test_create_item__failure_empty_field_only_spaces(self):
        user = self.create_user()

        new_item_data = {
            'name': '    ',
            'price': 5,
            'description': 'desc1',
            'category': 'varie',
            'availability': 11
        }
        resp = self.open_with_auth(
            '/items/', 'post', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == BAD_REQUEST
        assert len(Item.select()) == 0

    def test_create_item__failure_missing_field(self):
        user = self.create_user()

        new_item_data = {
            'name': 'Item one',
            'description': 'Description one'
        }
        resp = self.open_with_auth(
            '/items/', 'post', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == BAD_REQUEST
        assert len(Item.select()) == 0

    def test_create_item__failure_field_wrong_type(self):
        user = self.create_user()

        new_item_data = {
            'name': 'Item one',
            'price': 'Ten',
            'description': 'Description one',
            'category': 'Category one',
            'availability': 11
        }
        resp = self.open_with_auth(
            '/items/', 'post', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == BAD_REQUEST
        assert len(Item.select()) == 0

    def test_get__item(self):
        item1 = self.create_item()

        resp = self.app.get('/items/{}'.format(item1.uuid))
        assert resp.status_code == OK

        item_from_server = json.loads(resp.data.decode())
        assert item_from_server == item1.json()

    def test_get_item__empty(self):
        resp = self.app.get('/items/{}'.format(uuid.uuid4()))
        assert resp.status_code == NOT_FOUND

    def test_get_item__failure_non_existing_item(self):
        Item.create(
            uuid=uuid.uuid4(),
            name='Item one',
            price=5,
            description='Description one',
            category='Category one',
            availability=11
        )

        resp = self.app.get('/items/{}'.format(uuid.uuid4()))
        assert resp.status_code == NOT_FOUND

    def test_delete_item__success(self):
        user = self.create_user()
        item1 = self.create_item()

        resp = self.open_with_auth(
            'items/{}'.format(item1.uuid), 'delete', user.email, 'p4ssw0rd', data='')
        assert resp.status_code == NO_CONTENT
        assert len(Item.select()) == 0
        resp = self.app.get('/items/{}'.format(item1.uuid))
        assert resp.status_code == NOT_FOUND

    def test_delete_item__failure_not_found(self):
        user = self.create_user()
        self.create_item()

        resp = self.open_with_auth(
            'items/{}'.format(uuid.uuid4()), 'delete', user.email, 'p4ssw0rd', data='')
        assert resp.status_code == NOT_FOUND
        assert len(Item.select()) == 1

    def test_delete_item__failure_non_existing_empty_items(self):
        user = self.create_user()

        resp = self.open_with_auth(
            'items/{}'.format(uuid.uuid4()), 'delete', user.email, 'p4ssw0rd', data='')
        assert resp.status_code == NOT_FOUND

    def test_modify_item__success(self):
        user = self.create_user()
        static_id = uuid.uuid4()

        Item.create(
            uuid=static_id,
            name='Item one',
            price=5,
            description='Description one',
            category='Category one',
            availability=11
        )

        new_item_data = {
            'name': 'Item one',
            'price': 10,
            'description': 'Descrizione sensata',
            'category': 'Poligoni',
            'availability': 0
        }

        resp = self.open_with_auth(
            'items/{}'.format(static_id), 'put', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == OK

        item_from_server = json.loads(resp.data.decode())
        item_from_db = Item.get(Item.uuid == item_from_server['uuid']).json()

        assert item_from_db == item_from_server

        item_from_server.pop('uuid')
        assert new_item_data == item_from_server

    def test_modify_item__failure_invalid_field_value(self):
        static_id = uuid.uuid4()
        user = self.create_user()

        Item.create(
            uuid=static_id,
            name='Item one',
            price=5,
            description='Description one',
            category='Category one',
            availability=11
        )

        new_item_data = {
            'name': 'Item one',
            'price': 10,
            'description': 'Descrizione sensata',
            'category': 'Poligoni',
            'availability': -8
        }

        resp = self.open_with_auth(
            '/items/{}'.format(static_id), 'put', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == BAD_REQUEST

    def test_modify_item__failure_empty_field_only_spaces(self):
        user = self.create_user()

        item = Item.create(
            uuid=uuid.uuid4(),
            name='Item one',
            price=5,
            description='Description one',
            category='Category one',
            availability=11
        )

        modified_content = {
            'name': '      ',
            'price': 10,
            'description': 'Description two',
            'category': 'Category two',
            'availability': 11
        }

        resp = self.open_with_auth(
            'items/{}'.format(item.uuid), 'put', user.email, 'p4ssw0rd', data=modified_content)
        item_from_db = Item.get(Item.uuid == item.uuid).json()
        assert item.json() == item_from_db
        assert resp.status_code == BAD_REQUEST

    def test_modify_item__failure_missing_argument(self):
        user = self.create_user()

        item = Item.create(
            uuid=uuid.uuid4(),
            name='Item one',
            price=5,
            description='Description one',
            category='Category one',
            availability=11
        )

        modified_content = {
            'name': 'Item two',
            'price': 10,
            'description': 'Description two'
        }

        resp = self.open_with_auth(
            'items/{}'.format(item.uuid), 'put', user.email, 'p4ssw0rd', data=modified_content)
        item_from_db = Item.get(Item.uuid == item.uuid).json()
        assert item.json() == item_from_db
        assert resp.status_code == BAD_REQUEST

    def test_modify_item__failure_field_wrong_type(self):
        user = self.create_user()
        item = Item.create(
            uuid=uuid.uuid4(),
            name='Item one',
            price=5,
            description='Description one',
            category='Category one',
            availability=11
        )

        modified_content = {
            'name': 'Item one',
            'price': 'Ten',
            'description': 'Description two',
            'category': 'Category two',
            'availability': 6
        }
        resp = self.open_with_auth(
            'items/{}'.format(item.uuid), 'put', user.email, 'p4ssw0rd', data=modified_content)
        assert resp.status_code == BAD_REQUEST

        item_from_db = Item.get(uuid=item.uuid).json()
        assert item.json() == item_from_db

    def test_reload(self):
        item = self.create_item(availability=5)
        assert item.availability == 5

        item.availability = 1
        assert item.availability == 1

        item.update(availability=0).where(Item.uuid == item.uuid).execute()
        assert item.availability == 1

        item = item.reload()
        assert item.availability == 0

        item_old = Item.get(Item.uuid == item.uuid)

        item.availability = 1
        item.save()

        assert item_old.availability == 0
        assert item_old.reload().availability == 1

    def test_create_item_pictures__success(self):
        test_image_path = os.path.join('.', 'tests', 'images', 'test_image.jpg')

        item = self.create_item()

        picture_data = {
            'title': 'Example image',
            'file': FileStorage(open(test_image_path, 'rb')),
        }

        resp = self.app.post('/items/{}/pictures'.format(item.uuid),
                             content_type='multipart/form-data', data=picture_data)

        assert resp.status_code == CREATED

        image_from_server = json.loads(resp.data.decode())
        assert image_from_server['title'] == picture_data['title']
        assert image_from_server['extension'] == 'jpg'

        server_image_path = os.path.join(
            self.temp_dir, 'items', str(item.uuid), '{}.jpg'.format(image_from_server['uuid']))

        test_image_hash = hashlib.sha256(open(test_image_path, 'rb').read()).digest()
        server_image_hash = hashlib.sha256(open(server_image_path, 'rb').read()).digest()
        assert test_image_hash == server_image_hash

    def test_create_item_pictures__failure_empty_title_only_spaces(self):
        test_image_path = os.path.join('.', 'tests', 'images', 'test_image.jpg')

        item = self.create_item()

        picture_data = {
            'title': '  ',
            'file': FileStorage(open(test_image_path, 'rb')),
        }

        resp = self.app.post('/items/{}/pictures'.format(item.uuid),
                             content_type='multipart/form-data', data=picture_data)
        assert resp.status_code == BAD_REQUEST

    def test_create_item_pictures__failure_missing_image(self):
        item = self.create_item()

        picture_data = {
            'title': 'Example image',
            'file': None,
        }

        resp = self.app.post('/items/{}/pictures'.format(item.uuid),
                             content_type='multipart/form-data', data=picture_data)
        assert resp.status_code == BAD_REQUEST

    def test_create_item_pictures__failure_non_existing_item(self):
        test_image_path = os.path.join('.', 'tests', 'images', 'test_image.jpg')

        picture_data = {
            'title': 'Example image',
            'file': FileStorage(open(test_image_path, 'rb')),
        }

        resp = self.app.post('/items/{}/pictures'.format(uuid.uuid4),
                             content_type='multipart/form-data', data=picture_data)
        assert resp.status_code == NOT_FOUND

    def test_create_item_pictures__failure_not_an_image(self):
        test_image_path = os.path.join('.', 'tests', 'images', 'not_an_image.log')

        item = self.create_item()

        picture_data = {
            'title': 'Example image',
            'file': FileStorage(open(test_image_path, 'rb')),
        }

        resp = self.app.post('/items/{}/pictures'.format(item.uuid),
                             content_type='multipart/form-data', data=picture_data)
        assert resp.status_code == BAD_REQUEST

    def test_get_item_pictures__success(self):
        item = self.create_item()

        image1 = self.create_item_picture(item)
        image2 = self.create_item_picture(item)

        resp = self.app.get('/items/{}/pictures'.format(item.uuid))

        assert resp.status_code == OK
        assert json.loads(resp.data.decode()) == [image1.json(), image2.json()]

    def test_get_item_pictures__success_empty_pictures(self):
        item = self.create_item()

        resp = self.app.get('/items/{}/pictures'.format(item.uuid))

        assert resp.status_code == OK
        assert json.loads(resp.data.decode()) == []

    def test_get_item_pictures__failure_non_existing_item(self):
        resp = self.app.get('/items/{}/pictures'.format(uuid.uuid4()))

        assert resp.status_code == NOT_FOUND
