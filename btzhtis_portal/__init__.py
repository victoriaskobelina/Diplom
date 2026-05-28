import pymysql


# django 6 проверяет версию MySQLdb; PyMySQL подменяет этот модуль для проекта
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.__version__ = "2.2.1"
pymysql.install_as_MySQLdb()
