from django.templatetags.static import static


DEFAULT_META = {
    "title": "БТЖТиС",
    "description": (
        "Веб-система контроля учебного процесса БТЖТиС для тестирования студентов, "
        "аналитики успеваемости и управления учебными данными."
    ),
    "keywords": (
        "БТЖТиС, тестирование, успеваемость, образовательная платформа, "
        "учебный процесс, студент, преподаватель, администрирование"
    ),
    "type": "website",
    "image_alt": "БТЖТиС — веб-система контроля учебного процесса",
}


ROUTE_META = {
    "education:home": {
        "title": "Главная — БТЖТиС",
        "description": (
            "Главная страница цифровой образовательной среды БТЖТиС с авторизацией, "
            "регистрацией и входом в систему контроля учебного процесса."
        ),
    },
    "login": {
        "title": "Вход в систему — БТЖТиС",
        "description": "Авторизация в веб-системе контроля учебного процесса БТЖТиС.",
    },
    "education:register": {
        "title": "Регистрация — БТЖТиС",
        "description": "Регистрация студента в веб-системе контроля учебного процесса БТЖТиС.",
    },
    "password_reset": {
        "title": "Восстановление доступа — БТЖТиС",
        "description": "Информация о восстановлении доступа к учётной записи в системе БТЖТиС.",
    },
    "password_change": {
        "title": "Смена пароля — БТЖТиС",
        "description": "Изменение пароля пользователя в веб-системе БТЖТиС.",
    },
    "education:privacy_policy": {
        "title": "Политика конфиденциальности — БТЖТиС",
        "description": "Политика конфиденциальности веб-системы контроля учебного процесса БТЖТиС.",
    },
    "education:personal_data_consent": {
        "title": "Согласие на обработку персональных данных — БТЖТиС",
        "description": "Согласие на обработку персональных данных для пользователей системы БТЖТиС.",
    },
    "education:dashboard": {
        "title": "Личный кабинет — БТЖТиС",
        "description": "Личный кабинет пользователя в веб-системе контроля учебного процесса БТЖТиС.",
        "type": "profile",
    },
    "education:profile_edit": {
        "title": "Профиль — БТЖТиС",
        "description": "Редактирование профиля пользователя в системе БТЖТиС.",
        "type": "profile",
    },
    "education:student_dashboard": {
        "title": "Кабинет студента — БТЖТиС",
        "description": "Кабинет студента с доступными тестами, результатами и историей прохождений.",
        "type": "profile",
    },
    "education:teacher_dashboard": {
        "title": "Кабинет преподавателя — БТЖТиС",
        "description": "Кабинет преподавателя для управления тестами и анализа результатов студентов.",
        "type": "profile",
    },
    "education:test_create": {
        "title": "Новый тест — БТЖТиС",
        "description": "Создание нового теста в кабинете преподавателя БТЖТиС.",
        "type": "article",
    },
    "education:test_preview": {
        "title": "Просмотр теста — БТЖТиС",
        "description": "Просмотр структуры теста, вопросов и параметров публикации.",
        "type": "article",
    },
    "education:test_update": {
        "title": "Редактирование теста — БТЖТиС",
        "description": "Редактирование параметров теста в веб-системе БТЖТиС.",
        "type": "article",
    },
    "education:question_create": {
        "title": "Новый вопрос — БТЖТиС",
        "description": "Добавление нового вопроса в тест преподавателя.",
        "type": "article",
    },
    "education:question_update": {
        "title": "Редактирование вопроса — БТЖТиС",
        "description": "Редактирование вопроса и вариантов ответа в тесте.",
        "type": "article",
    },
    "education:report_detail": {
        "title": "Аналитика по тесту — БТЖТиС",
        "description": "Аналитика результатов, вопросов и прохождений теста студентами.",
        "type": "article",
    },
    "education:start_test": {
        "title": "Начало тестирования — БТЖТиС",
        "description": "Страница запуска теста для студента в системе БТЖТиС.",
        "type": "article",
    },
    "education:take_test": {
        "title": "Прохождение теста — БТЖТиС",
        "description": "Прохождение теста с последовательным ответом на вопросы.",
        "type": "article",
    },
    "education:attempt_result": {
        "title": "Результат теста — БТЖТиС",
        "description": "Результаты прохождения теста и разбор ответов студента.",
        "type": "article",
    },
    "education:admin_dashboard": {
        "title": "Администрирование — БТЖТиС",
        "description": "Панель администратора для управления пользователями, группами и дисциплинами.",
        "type": "profile",
    },
    "education:admin_user_list": {
        "title": "Пользователи — БТЖТиС",
        "description": "Управление пользователями веб-системы БТЖТиС.",
        "type": "profile",
    },
    "education:admin_user_create": {
        "title": "Новый пользователь — БТЖТиС",
        "description": "Создание нового пользователя в административной панели БТЖТиС.",
        "type": "profile",
    },
    "education:admin_user_edit": {
        "title": "Редактирование пользователя — БТЖТиС",
        "description": "Редактирование данных пользователя в административной панели БТЖТиС.",
        "type": "profile",
    },
    "education:group_list": {
        "title": "Учебные группы — БТЖТиС",
        "description": "Список и управление учебными группами в системе БТЖТиС.",
        "type": "profile",
    },
    "education:group_create": {
        "title": "Новая учебная группа — БТЖТиС",
        "description": "Создание новой учебной группы в административной панели БТЖТиС.",
        "type": "profile",
    },
    "education:group_edit": {
        "title": "Редактирование учебной группы — БТЖТиС",
        "description": "Редактирование параметров учебной группы в системе БТЖТиС.",
        "type": "profile",
    },
    "education:discipline_list": {
        "title": "Дисциплины — БТЖТиС",
        "description": "Список и управление дисциплинами в веб-системе БТЖТиС.",
        "type": "profile",
    },
    "education:discipline_create": {
        "title": "Новая дисциплина — БТЖТиС",
        "description": "Создание новой дисциплины в административной панели БТЖТиС.",
        "type": "profile",
    },
    "education:discipline_edit": {
        "title": "Редактирование дисциплины — БТЖТиС",
        "description": "Редактирование дисциплины в системе БТЖТиС.",
        "type": "profile",
    },
    "education:activity_logs": {
        "title": "Журнал действий — БТЖТиС",
        "description": "Журнал действий пользователей и административный мониторинг в системе БТЖТиС.",
        "type": "profile",
    },
}


def site_meta(request):
    view_name = getattr(getattr(request, "resolver_match", None), "view_name", "")
    meta = DEFAULT_META | ROUTE_META.get(view_name, {})
    meta["url"] = request.build_absolute_uri()
    meta["image"] = request.build_absolute_uri(static("education/img/og-cover.svg"))
    meta["og_title"] = meta["title"]
    return {
        "site_meta": meta,
        "current_view_name": view_name,
    }
