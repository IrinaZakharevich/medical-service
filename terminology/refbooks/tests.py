from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from .models import Refbook, RefbookVersion, RefbookItem
from django.utils import timezone

URL_REFBOOKS = 'refbooks-list'
URL_LIST_ITEMS = 'refbook-list-items'
URL_VALIDATE_ITEM = 'refbook-check-item'


class RefbookBaseTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Refbooks
        self.refbook1 = Refbook.objects.create(code="REF1", name="Refbook 1", description="Description 1")
        self.refbook2 = Refbook.objects.create(code="REF2", name="Refbook 2", description="Description 2")
        self.refbook3 = Refbook.objects.create(code="REF3", name="Refbook 3", description="Description 3")

        # Dates
        self.current_date = timezone.now().date()
        self.one_day_ago = self.current_date - timezone.timedelta(days=1)
        self.two_days_ago = self.current_date - timezone.timedelta(days=2)

        # Versions
        self.ref1_version = RefbookVersion.objects.create(
            refbook=self.refbook1,
            version="1.0",
            start_date=self.two_days_ago
        )
        self.ref2_version_old = RefbookVersion.objects.create(
            refbook=self.refbook2,
            version="1.0",
            start_date=self.two_days_ago
        )
        self.ref2_version_new = RefbookVersion.objects.create(
            refbook=self.refbook2,
            version="2.0",
            start_date=self.current_date
        )

        # Items
        self.ref2_item1_old = RefbookItem.objects.create(
            version=self.ref2_version_old,
            code="ITEM1",
            value="Value 1 old"
        )
        self.ref2_item1_new = RefbookItem.objects.create(
            version=self.ref2_version_new,
            code="ITEM1",
            value="Value 1"
        )
        self.ref2_item2_new = RefbookItem.objects.create(
            version=self.ref2_version_new,
            code="ITEM2",
            value="Value 2"
        )


class RefbookListViewTest(RefbookBaseTest):

    def test_no_date_parameter(self):
        """Test that the view returns all refbooks when no date parameter is provided."""
        url = reverse(URL_REFBOOKS)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['refbooks']), 3)

    def test_valid_date_parameter_1(self):
        """Test that the view returns refbooks with versions starting on or before the specified date."""

        url = reverse(URL_REFBOOKS)
        response = self.client.get(url, {'date': self.one_day_ago})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['refbooks']), 2)
        self.assertEqual(response.data['refbooks'][0]['name'], "Refbook 1")

    def test_valid_date_parameter_2(self):
        """Test that the view returns all refbooks when an invalid date parameter is provided."""

        url = reverse(URL_REFBOOKS)
        response = self.client.get(url, {'date': self.current_date})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['refbooks']), 2)


class RefbookItemListViewTest(RefbookBaseTest):
    def test_no_version_parameter(self):
        """Test that the view returns items for the latest version when no version parameter is provided."""
        url = reverse(URL_LIST_ITEMS, kwargs={'id': self.refbook2.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['elements']), 2)
        self.assertSetEqual(
            set(item['code'] for item in response.data['elements']),
            {self.ref2_item1_new.code, self.ref2_item2_new.code}
        )

    def test_with_version_parameter(self):
        """Test that the view returns items for the specified version."""
        url = reverse(URL_LIST_ITEMS, kwargs={'id': self.refbook2.id})
        response = self.client.get(url, {'version': '2.0'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['elements']), 2)
        self.assertSetEqual(
            set(item['code'] for item in response.data['elements']),
            {self.ref2_item1_new.code, self.ref2_item2_new.code}
        )

    def test_invalid_refbook_id(self):
        """Test that the view returns a 404 error for an invalid refbook ID."""
        url = reverse(URL_LIST_ITEMS, kwargs={'id': 999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_invalid_version_parameter(self):
        """Test that the view returns an empty list for an invalid version parameter."""
        url = reverse(URL_LIST_ITEMS, kwargs={'id': self.refbook1.id})
        invalid_version = '1.99'
        response = self.client.get(url, {'version': invalid_version})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"error": f"Version '{invalid_version}' not found for the given refbook."})

    def test_refbook_with_no_version(self):
        """Test that requesting items for a refbook with no versions returns 404."""
        url = reverse(URL_LIST_ITEMS, kwargs={'id': self.refbook3.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"error": f"No valid version found for the refbook ID '{self.refbook3.id}'."})

    def test_invalid_id_refbook(self):
        """Test that requesting items for a refbook with no versions returns 404."""
        invalid_id = 999999
        url = reverse(URL_LIST_ITEMS, kwargs={'id': invalid_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"error": f"Refbook with ID '{invalid_id}' not found."})


class RefbookItemValidationTest(RefbookBaseTest):

    def test_valid_item_no_version(self):
        """ Test taht the view returns True for a valid element."""
        url = reverse(URL_VALIDATE_ITEM, kwargs={'id': self.refbook2.id})
        response = self.client.get(url, {'code': self.ref2_item1_new.code, 'value': self.ref2_item1_new.value})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['valid'], True)

    def test_valid_item_with_version(self):
        """ Test taht the view returns True for a valid element with passed version."""
        url = reverse(URL_VALIDATE_ITEM, kwargs={'id': self.refbook2.id})
        response = self.client.get(url, {
            'code': self.ref2_item1_new.code,
            'value': self.ref2_item1_new.value,
            'version': self.ref2_item1_new.version.version
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['valid'], True)

    def test_valid_item_with_old_version(self):
        """ Test taht the view returns True for a valid element with passed version."""
        url = reverse(URL_VALIDATE_ITEM, kwargs={'id': self.refbook2.id})
        response = self.client.get(url, {
            'code': self.ref2_item1_old.code,
            'value': self.ref2_item1_old.value,
            'version': self.ref2_version_old.version
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['valid'], True)

    def test_invalid_item(self):
        """ Test taht the view returns True for a valid element."""
        url = reverse(URL_VALIDATE_ITEM, kwargs={'id': self.refbook1.id})
        response = self.client.get(url, {'code': self.ref2_item1_old.code, 'value': 'Invalid value'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['valid'], False)

    def test_invalid_refbook_id(self):
        """ Test taht the view returns a 404 error for an invalid refbook ID."""
        invalid_id = 999
        url = reverse(URL_VALIDATE_ITEM, kwargs={'id': invalid_id})
        response = self.client.get(url, {'code': self.ref2_item1_old.code, 'value': self.ref2_item1_old.value})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"error": f"Refbook with ID '{invalid_id}' not found."})

    def test_invalid_version(self):
        """ Test taht the view returns a 404 error for an invalid version."""
        url = reverse(URL_VALIDATE_ITEM, kwargs={'id': self.refbook1.id})
        invalid_version = '1.99'
        response = self.client.get(url, {
            'code': self.ref2_item1_new.code,
            'value': self.ref2_item1_new.value,
            'version': invalid_version
        })

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"error": f"Version '{invalid_version}' not found for the given refbook."})

    def test_bad_request_no_code(self):
        """ Test taht the view returns a 404 error for an invalid version."""
        url = reverse(URL_VALIDATE_ITEM, kwargs={'id': self.refbook2.id})
        response = self.client.get(url, {
            'value': self.ref2_item1_new.value,
            'version': self.ref2_version_new
        })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": "Missing required parameters: code or/and value."})
