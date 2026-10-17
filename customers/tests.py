from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class CustomerRegistrationTests(APITestCase):
    def setUp(self):
        self.registration_url = reverse('register')
        self.valid_data = {
            'username': 'new_customer',
            'email': 'newcustomer@example.com',
            'password': 'StrongPass123!Secure',
            'first_name': 'New',
            'last_name': 'Customer',
        }

    def test_customer_can_register(self):
        response = self.client.post(
            self.registration_url,
            self.valid_data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            User.objects.filter(username='new_customer').exists()
        )

        user = User.objects.get(username='new_customer')
        self.assertTrue(
            user.check_password('StrongPass123!Secure')
        )
        self.assertNotIn('password', response.data)

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(
            username='new_customer',
            email='existing@example.com',
            password='ExistingPass123!Secure',
        )

        response = self.client.post(
            self.registration_url,
            self.valid_data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username='existing_customer',
            email='newcustomer@example.com',
            password='ExistingPass123!Secure',
        )

        response = self.client.post(
            self.registration_url,
            self.valid_data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_short_password_is_rejected(self):
        data = self.valid_data.copy()
        data['password'] = 'short'

        response = self.client.post(
            self.registration_url,
            data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )


class CustomerLoginTests(APITestCase):
    def setUp(self):
        self.login_url = reverse('login')
        self.password = 'StrongPass123!Secure'

        self.user = User.objects.create_user(
            username='login_customer',
            email='login@example.com',
            password=self.password,
        )

    def test_customer_can_log_in(self):
        response = self.client.post(
            self.login_url,
            {
                'username': self.user.username,
                'password': self.password,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn('token', response.data)
        self.assertEqual(
            response.data['user']['username'],
            self.user.username,
        )

    def test_login_rejects_incorrect_password(self):
        response = self.client.post(
            self.login_url,
            {
                'username': self.user.username,
                'password': 'WrongPassword123!',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )


class CustomerProfileTests(APITestCase):
    def setUp(self):
        self.profile_url = reverse('profile')

        self.user = User.objects.create_user(
            username='profile_customer',
            email='profile@example.com',
            password='StrongPass123!Secure',
            first_name='Profile',
            last_name='Customer',
        )

        self.other_user = User.objects.create_user(
            username='other_customer',
            email='other@example.com',
            password='OtherPass123!Secure',
        )

    def test_profile_requires_authentication(self):
        response = self.client.get(self.profile_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_customer_can_view_own_profile(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.profile_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data['username'],
            self.user.username,
        )
        self.assertEqual(
            response.data['email'],
            self.user.email,
        )

    def test_customer_can_update_own_profile(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            self.profile_url,
            {
                'first_name': 'Updated',
                'last_name': 'Name',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')

    def test_customer_cannot_change_username(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            self.profile_url,
            {'username': self.other_user.username},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()
        self.assertEqual(
            self.user.username,
            'profile_customer',
        )

    def test_profile_rejects_another_users_email(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            self.profile_url,
            {'email': self.other_user.email},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
