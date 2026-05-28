from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import LoginForm, ProfileForm, SignUpForm
from .models import ActivityLog
from .utils import dashboard_url_for, log_activity


# тексты юридических страниц хранятся в коде и выводятся одним общим шаблоном
LEGAL_DOCUMENTS = {
    "privacy_policy": {
        "title": "Политика конфиденциальности",
        "subtitle": "Порядок обработки и защиты персональных данных пользователей веб-системы контроля учебного процесса БТЖТиС.",
        "sections": [
            {
                "title": "1. Общие положения",
                "paragraphs": [
                    "Настоящая Политика конфиденциальности определяет порядок обработки, хранения и защиты персональных данных пользователей веб-системы контроля учебного процесса БТЖТиС.",
                    "Использование системы означает ознакомление пользователя с настоящей Политикой и согласие с её условиями в части, относящейся к обработке персональных данных.",
                ],
            },
            {
                "title": "2. Какие данные обрабатываются",
                "paragraphs": [
                    "Система может обрабатывать следующие данные: имя пользователя, фамилию, имя, отчество, учебную группу, адрес электронной почты, номер телефона, сведения о прохождении тестов, результатах обучения и действиях в системе.",
                    "Электронная почта и телефон используются только в объёме, который пользователь указывает самостоятельно при регистрации или редактировании профиля.",
                    "Для работы авторизации, пользовательской сессии и защиты форм от CSRF-атак система использует технические cookie. Они не применяются для рекламы, сторонней аналитики или отслеживания пользователей за пределами системы.",
                ],
            },
            {
                "title": "3. Цели обработки данных",
                "paragraphs": [
                    "Персональные данные обрабатываются для регистрации и идентификации пользователей, организации доступа к учебным материалам, проведения тестирования, хранения результатов, анализа успеваемости и обеспечения информационной безопасности системы.",
                    "Также данные могут использоваться для администрирования учебных групп, дисциплин и прав доступа внутри образовательной платформы.",
                ],
            },
            {
                "title": "4. Порядок обработки и хранения",
                "paragraphs": [
                    "Обработка персональных данных осуществляется с использованием средств автоматизации и без их использования, если это необходимо для работы системы.",
                    "Доступ к персональным данным предоставляется только уполномоченным пользователям системы в пределах их роли: студенту, преподавателю или администратору.",
                    "Персональные данные хранятся не дольше, чем этого требуют цели их обработки, либо до момента удаления учётной записи и связанных с ней данных в установленном порядке.",
                ],
            },
            {
                "title": "5. Права пользователя",
                "paragraphs": [
                    "Пользователь вправе уточнять свои персональные данные, изменять их в профиле, а также обращаться к ответственным лицам образовательной организации по вопросам обработки и защиты персональных данных.",
                    "Пользователь вправе запросить прекращение обработки персональных данных, если это не противоречит требованиям законодательства и задачам образовательного процесса.",
                ],
            },
            {
                "title": "6. Заключительные положения",
                "paragraphs": [
                    "Администрация системы принимает необходимые организационные и технические меры для защиты персональных данных от неправомерного доступа, изменения, раскрытия или уничтожения.",
                    "Актуальная редакция настоящей Политики размещается в системе и применяется с момента публикации.",
                ],
            },
        ],
    },
    "personal_data_consent": {
        "title": "Согласие на обработку персональных данных",
        "subtitle": "Документ определяет объём и цели обработки персональных данных пользователя при работе с веб-системой БТЖТиС.",
        "sections": [
            {
                "title": "1. Предмет согласия",
                "paragraphs": [
                    "Пользователь, проходящий регистрацию в веб-системе контроля учебного процесса БТЖТиС, выражает согласие на обработку своих персональных данных в объёме, необходимом для функционирования системы.",
                ],
            },
            {
                "title": "2. Перечень персональных данных",
                "paragraphs": [
                    "К персональным данным относятся: имя пользователя, фамилия, имя, отчество, учебная группа, адрес электронной почты, номер телефона, сведения о результатах тестирования, а также технические и служебные записи о действиях в системе.",
                ],
            },
            {
                "title": "3. Цели обработки",
                "paragraphs": [
                    "Обработка персональных данных осуществляется в целях регистрации пользователя, предоставления доступа к учебному контенту, организации тестирования, фиксации результатов, анализа успеваемости и администрирования платформы.",
                ],
            },
            {
                "title": "4. Действия с персональными данными",
                "paragraphs": [
                    "Пользователь даёт согласие на сбор, запись, систематизацию, накопление, хранение, уточнение, использование, передачу в пределах образовательной организации, обезличивание, блокирование и удаление персональных данных в рамках целей, указанных в настоящем документе.",
                ],
            },
            {
                "title": "5. Срок действия согласия",
                "paragraphs": [
                    "Согласие действует с момента подтверждения при регистрации и сохраняет силу на период использования учётной записи, а также в течение срока, необходимого для выполнения целей обработки данных и требований законодательства.",
                ],
            },
            {
                "title": "6. Отзыв согласия",
                "paragraphs": [
                    "Пользователь вправе отозвать согласие на обработку персональных данных путём обращения к администрации образовательной организации. Отзыв согласия может повлечь ограничение или прекращение доступа к системе, если обработка данных необходима для её работы.",
                ],
            },
        ],
    },
}


# главная страница одновременно показывает публичный экран и форму входа
def home(request):
    if request.user.is_authenticated:
        return redirect(dashboard_url_for(request.user))

    login_form = None
    next_url = request.POST.get("next") or request.GET.get("next")
    if request.method == "POST":
        login_form = LoginForm(request, data=request.POST)
        if login_form.is_valid():
            user = login_form.get_user()
            login(request, user)
            log_activity(
                request,
                user,
                ActivityLog.ActionType.AUTH,
                "Пользователь вошёл в систему",
            )
            messages.success(request, "Вход выполнен успешно.")
            if not url_has_allowed_host_and_scheme(
                next_url or "",
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                next_url = None
            return redirect(next_url or dashboard_url_for(user))
    else:
        login_form = LoginForm(request)

    return render(request, "education/home.html", {"login_form": login_form, "next_url": next_url})


# простые публичные страницы: восстановление пароля и юридические документы
def password_reset_info(request):
    return render(request, "registration/password_reset_form.html")


def privacy_policy(request):
    return render(request, "education/legal_document.html", LEGAL_DOCUMENTS["privacy_policy"])


def personal_data_consent(request):
    return render(request, "education/legal_document.html", LEGAL_DOCUMENTS["personal_data_consent"])


# регистрация создает студенческую учетную запись и сразу авторизует пользователя
def register(request):
    if request.user.is_authenticated:
        return redirect(dashboard_url_for(request.user))

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            log_activity(
                request,
                user,
                ActivityLog.ActionType.AUTH,
                "Новая регистрация в системе",
            )
            messages.success(request, "Регистрация выполнена успешно.")
            return redirect(dashboard_url_for(user))
    else:
        form = SignUpForm()

    return render(
        request,
        "education/form_page.html",
        {
            "title": "Регистрация",
            "subtitle": "Создание учетной записи в системе контроля учебного процесса.",
            "form": form,
            "submit_label": "Зарегистрироваться",
            "cancel_url": "education:home",
            "cancel_label": "Отменить",
            "single_column_form": True,
        },
    )


# после входа пользователь попадает в кабинет, соответствующий его роли
@login_required
def dashboard(request):
    return redirect(dashboard_url_for(request.user))


# профиль позволяет обновить личные данные без изменения роли и прав доступа
@login_required
def profile_edit(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            log_activity(
                request,
                request.user,
                ActivityLog.ActionType.PROFILE,
                "Пользователь обновил профиль",
            )
            messages.success(request, "Профиль обновлён.")
            return redirect(dashboard_url_for(request.user))
    else:
        form = ProfileForm(instance=request.user)

    return render(
        request,
        "education/form_page.html",
        {
            "title": "Профиль",
            "subtitle": "Редактирование персональных данных.",
            "form": form,
            "submit_label": "Сохранить изменения",
            "cancel_url": dashboard_url_for(request.user),
            "show_password_change": True,
        },
    )
