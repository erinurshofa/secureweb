import pymysql

# 1. Install PyMySQL as MySQLdb for Django MySQL backend
pymysql.install_as_MySQLdb()

# 2. Compatibility layer for Django 6.1 on XAMPP MariaDB (10.4.x)
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.mysql.features import DatabaseFeatures

# Bypass minimum MariaDB version check (Django 6.1 normally checks for MariaDB 10.11+)
BaseDatabaseWrapper.check_database_version_supported = lambda self: None

# Disable RETURNING clause on INSERT since MariaDB 10.4 does not support RETURNING
DatabaseFeatures.can_return_columns_from_insert = property(lambda self: False)
DatabaseFeatures.can_return_rows_from_bulk_insert = property(lambda self: False)

# MariaDB 10.4 does not have native UUID datatype (uses char(32) with uuid.hex)
DatabaseFeatures.has_native_uuid_field = property(lambda self: False)
