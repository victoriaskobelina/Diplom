-- MySQL schema for the BTZhTiS web system
-- Generated from the current Django models in education/models.py
-- Database: btzhtis
-- Charset: utf8mb4

CREATE DATABASE IF NOT EXISTS `btzhtis`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `btzhtis`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `django_content_type` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `app_label` VARCHAR(100) NOT NULL,
    `model` VARCHAR(100) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `django_content_type_app_label_model_uniq` (`app_label`, `model`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `auth_permission` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `content_type_id` BIGINT NOT NULL,
    `codename` VARCHAR(100) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `auth_permission_content_type_codename_uniq` (`content_type_id`, `codename`),
    KEY `auth_permission_content_type_id_idx` (`content_type_id`),
    CONSTRAINT `auth_permission_content_type_id_fk`
        FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `auth_group` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(150) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `auth_group_name_uniq` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `education_academicgroup` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(50) NOT NULL,
    `description` LONGTEXT NOT NULL,
    `curator_id` BIGINT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `education_academicgroup_name_uniq` (`name`),
    KEY `education_academicgroup_curator_id_idx` (`curator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `education_user` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `password` VARCHAR(128) NOT NULL,
    `last_login` DATETIME(6) NULL,
    `is_superuser` TINYINT(1) NOT NULL DEFAULT 0,
    `username` VARCHAR(150) NOT NULL,
    `first_name` VARCHAR(150) NOT NULL DEFAULT '',
    `last_name` VARCHAR(150) NOT NULL DEFAULT '',
    `is_staff` TINYINT(1) NOT NULL DEFAULT 0,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `date_joined` DATETIME(6) NOT NULL,
    `email` VARCHAR(254) NULL,
    `middle_name` VARCHAR(150) NOT NULL DEFAULT '',
    `phone` VARCHAR(32) NOT NULL DEFAULT '',
    `bio` LONGTEXT NOT NULL,
    `role` VARCHAR(20) NOT NULL DEFAULT 'student',
    `academic_group_id` BIGINT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `education_user_username_uniq` (`username`),
    UNIQUE KEY `education_user_email_uniq` (`email`),
    KEY `education_user_academic_group_id_idx` (`academic_group_id`),
    CONSTRAINT `education_user_academic_group_id_fk`
        FOREIGN KEY (`academic_group_id`) REFERENCES `education_academicgroup` (`id`)
        ON DELETE SET NULL,
    CONSTRAINT `education_user_role_chk`
        CHECK (`role` IN ('student', 'teacher', 'administrator'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE `education_academicgroup`
    ADD CONSTRAINT `education_academicgroup_curator_id_fk`
        FOREIGN KEY (`curator_id`) REFERENCES `education_user` (`id`)
        ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS `auth_group_permissions` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `group_id` BIGINT NOT NULL,
    `permission_id` BIGINT NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `auth_group_permissions_group_permission_uniq` (`group_id`, `permission_id`),
    KEY `auth_group_permissions_permission_id_idx` (`permission_id`),
    CONSTRAINT `auth_group_permissions_group_id_fk`
        FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
        ON DELETE CASCADE,
    CONSTRAINT `auth_group_permissions_permission_id_fk`
        FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `education_user_groups` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `group_id` BIGINT NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `education_user_groups_user_group_uniq` (`user_id`, `group_id`),
    KEY `education_user_groups_group_id_idx` (`group_id`),
    CONSTRAINT `education_user_groups_user_id_fk`
        FOREIGN KEY (`user_id`) REFERENCES `education_user` (`id`)
        ON DELETE CASCADE,
    CONSTRAINT `education_user_groups_group_id_fk`
        FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `education_user_user_permissions` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `permission_id` BIGINT NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `education_user_permissions_user_permission_uniq` (`user_id`, `permission_id`),
    KEY `education_user_user_permissions_permission_id_idx` (`permission_id`),
    CONSTRAINT `education_user_user_permissions_user_id_fk`
        FOREIGN KEY (`user_id`) REFERENCES `education_user` (`id`)
        ON DELETE CASCADE,
    CONSTRAINT `education_user_user_permissions_permission_id_fk`
        FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `education_discipline` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(120) NOT NULL,
    `code` VARCHAR(20) NOT NULL DEFAULT '',
    `description` LONGTEXT NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `education_discipline_name_uniq` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `education_discipline_groups` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `discipline_id` BIGINT NOT NULL,
    `academicgroup_id` BIGINT NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `education_discipline_groups_uniq` (`discipline_id`, `academicgroup_id`),
    KEY `education_discipline_groups_academicgroup_id_idx` (`academicgroup_id`),
    CONSTRAINT `education_discipline_groups_discipline_id_fk`
        FOREIGN KEY (`discipline_id`) REFERENCES `education_discipline` (`id`)
        ON DELETE CASCADE,
    CONSTRAINT `education_discipline_groups_academicgroup_id_fk`
        FOREIGN KEY (`academicgroup_id`) REFERENCES `education_academicgroup` (`id`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `education_discipline_teachers` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `discipline_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `education_discipline_teachers_uniq` (`discipline_id`, `user_id`),
    KEY `education_discipline_teachers_user_id_idx` (`user_id`),
    CONSTRAINT `education_discipline_teachers_discipline_id_fk`
        FOREIGN KEY (`discipline_id`) REFERENCES `education_discipline` (`id`)
        ON DELETE CASCADE,
    CONSTRAINT `education_discipline_teachers_user_id_fk`
        FOREIGN KEY (`user_id`) REFERENCES `education_user` (`id`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `education_test` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `title` VARCHAR(200) NOT NULL,
    `description` LONGTEXT NOT NULL,
    `discipline_id` BIGINT NOT NULL,
    `author_id` BIGINT NOT NULL,
    `time_limit_minutes` INT UNSIGNED NOT NULL DEFAULT 30,
    `max_attempts` INT UNSIGNED NOT NULL DEFAULT 1,
    `allow_retake` TINYINT(1) NOT NULL DEFAULT 0,
    `is_published` TINYINT(1) NOT NULL DEFAULT 0,
    `available_from` DATETIME(6) NULL,
    `available_to` DATETIME(6) NULL,
    `created_at` DATETIME(6) NOT NULL,
    `updated_at` DATETIME(6) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `education_test_discipline_id_idx` (`discipline_id`),
    KEY `education_test_author_id_idx` (`author_id`),
    CONSTRAINT `education_test_discipline_id_fk`
        FOREIGN KEY (`discipline_id`) REFERENCES `education_discipline` (`id`)
        ON DELETE CASCADE,
    CONSTRAINT `education_test_author_id_fk`
        FOREIGN KEY (`author_id`) REFERENCES `education_user` (`id`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `education_test_groups` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `test_id` BIGINT NOT NULL,
    `academicgroup_id` BIGINT NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `education_test_groups_uniq` (`test_id`, `academicgroup_id`),
    KEY `education_test_groups_academicgroup_id_idx` (`academicgroup_id`),
    CONSTRAINT `education_test_groups_test_id_fk`
        FOREIGN KEY (`test_id`) REFERENCES `education_test` (`id`)
        ON DELETE CASCADE,
    CONSTRAINT `education_test_groups_academicgroup_id_fk`
        FOREIGN KEY (`academicgroup_id`) REFERENCES `education_academicgroup` (`id`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `education_question` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `test_id` BIGINT NOT NULL,
    `text` LONGTEXT NOT NULL,
    `image` VARCHAR(100) NULL,
    `order` INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (`id`),
    UNIQUE KEY `education_question_test_order_uniq` (`test_id`, `order`),
    KEY `education_question_test_id_idx` (`test_id`),
    CONSTRAINT `education_question_test_id_fk`
        FOREIGN KEY (`test_id`) REFERENCES `education_test` (`id`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `education_answeroption` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `question_id` BIGINT NOT NULL,
    `text` VARCHAR(255) NOT NULL,
    `is_correct` TINYINT(1) NOT NULL DEFAULT 0,
    `order` INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (`id`),
    UNIQUE KEY `education_answeroption_question_order_uniq` (`question_id`, `order`),
    KEY `education_answeroption_question_id_idx` (`question_id`),
    CONSTRAINT `education_answeroption_question_id_fk`
        FOREIGN KEY (`question_id`) REFERENCES `education_question` (`id`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `education_testattempt` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `student_id` BIGINT NOT NULL,
    `test_id` BIGINT NOT NULL,
    `attempt_number` INT UNSIGNED NOT NULL DEFAULT 1,
    `score` INT UNSIGNED NOT NULL DEFAULT 0,
    `max_score` INT UNSIGNED NOT NULL DEFAULT 0,
    `grade` VARCHAR(2) NOT NULL DEFAULT '',
    `started_at` DATETIME(6) NOT NULL,
    `completed_at` DATETIME(6) NULL,
    `is_finished` TINYINT(1) NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `education_testattempt_student_test_attempt_uniq` (`student_id`, `test_id`, `attempt_number`),
    KEY `education_testattempt_test_id_idx` (`test_id`),
    CONSTRAINT `education_testattempt_student_id_fk`
        FOREIGN KEY (`student_id`) REFERENCES `education_user` (`id`)
        ON DELETE CASCADE,
    CONSTRAINT `education_testattempt_test_id_fk`
        FOREIGN KEY (`test_id`) REFERENCES `education_test` (`id`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `education_studentanswer` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `attempt_id` BIGINT NOT NULL,
    `question_id` BIGINT NOT NULL,
    `selected_option_id` BIGINT NULL,
    `is_correct` TINYINT(1) NOT NULL DEFAULT 0,
    `answered_at` DATETIME(6) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `education_studentanswer_attempt_question_uniq` (`attempt_id`, `question_id`),
    KEY `education_studentanswer_question_id_idx` (`question_id`),
    KEY `education_studentanswer_selected_option_id_idx` (`selected_option_id`),
    CONSTRAINT `education_studentanswer_attempt_id_fk`
        FOREIGN KEY (`attempt_id`) REFERENCES `education_testattempt` (`id`)
        ON DELETE CASCADE,
    CONSTRAINT `education_studentanswer_question_id_fk`
        FOREIGN KEY (`question_id`) REFERENCES `education_question` (`id`)
        ON DELETE CASCADE,
    CONSTRAINT `education_studentanswer_selected_option_id_fk`
        FOREIGN KEY (`selected_option_id`) REFERENCES `education_answeroption` (`id`)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `education_activitylog` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NULL,
    `action_type` VARCHAR(20) NOT NULL,
    `description` VARCHAR(255) NOT NULL,
    `details` JSON NULL,
    `ip_address` VARCHAR(39) NULL,
    `created_at` DATETIME(6) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `education_activitylog_user_id_idx` (`user_id`),
    KEY `education_activitylog_created_at_idx` (`created_at`),
    CONSTRAINT `education_activitylog_user_id_fk`
        FOREIGN KEY (`user_id`) REFERENCES `education_user` (`id`)
        ON DELETE SET NULL,
    CONSTRAINT `education_activitylog_action_type_chk`
        CHECK (`action_type` IN ('auth', 'profile', 'test', 'analytics', 'admin'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `django_admin_log` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `action_time` DATETIME(6) NOT NULL,
    `object_id` LONGTEXT NULL,
    `object_repr` VARCHAR(200) NOT NULL,
    `action_flag` SMALLINT UNSIGNED NOT NULL,
    `change_message` LONGTEXT NOT NULL,
    `content_type_id` BIGINT NULL,
    `user_id` BIGINT NOT NULL,
    PRIMARY KEY (`id`),
    KEY `django_admin_log_content_type_id_idx` (`content_type_id`),
    KEY `django_admin_log_user_id_idx` (`user_id`),
    CONSTRAINT `django_admin_log_content_type_id_fk`
        FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
        ON DELETE SET NULL,
    CONSTRAINT `django_admin_log_user_id_fk`
        FOREIGN KEY (`user_id`) REFERENCES `education_user` (`id`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `django_session` (
    `session_key` VARCHAR(40) NOT NULL,
    `session_data` LONGTEXT NOT NULL,
    `expire_date` DATETIME(6) NOT NULL,
    PRIMARY KEY (`session_key`),
    KEY `django_session_expire_date_idx` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `django_migrations` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `app` VARCHAR(255) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `applied` DATETIME(6) NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
