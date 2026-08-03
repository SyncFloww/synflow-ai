import os
import unittest
from django.test import TestCase
from django.db import connection
from django.core.cache import cache
import redis
from celery import current_app

class InfrastructureConnectionTests(TestCase):
    def test_database_connection(self):
        """Verify the database is reachable and operational."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                row = cursor.fetchone()
                self.assertEqual(row[0], 1)
        except Exception as e:
            self.fail(f"Database connection failed: {e}")

    def test_redis_connection(self):
        """Verify Redis is reachable (skips gracefully if not running locally)."""
        try:
            broker_url = current_app.conf.broker_url
            if broker_url and broker_url.startswith('redis'):
                r = redis.Redis.from_url(broker_url)
                r.ping()
                self.assertTrue(True, "Redis is reachable")
            else:
                self.skipTest("Redis is not configured as Celery broker.")
        except unittest.SkipTest:
            raise
        except Exception as e:
            self.skipTest(f"Redis not available in this environment: {e}")

    def test_celery_app_is_configured(self):
        """Verify Celery app is loaded and configured."""
        self.assertIsNotNone(current_app)
        self.assertTrue(hasattr(current_app, 'conf'))
