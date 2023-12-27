from http.client import OK, NOT_FOUND
import pytest
from pytest_django.asserts import assertRedirects

from django.contrib.auth import get_user_model
from django.urls import reverse

from news.models import News, Comment

User = get_user_model()


@pytest.fixture
def user(django_user_model):
    """Фикстура пользователь."""
    return django_user_model.objects.create(username='Пользователь')


@pytest.fixture
def user_client(user, client):
    """Фикстура аутентифицированный пользователь."""
    client.force_login(user)
    return client


@pytest.fixture
def author(django_user_model):
    """Фикстура автор."""
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def author_client(author, client):
    """Фикстура аутентифицированный автор."""
    client.force_login(author)
    return client


@pytest.fixture
def news():
    """Фикстура новость."""
    news = News.objects.create(
        title='Заголовок',
        text='Текст заметки'
    )
    return news


@pytest.fixture
def comment(news, author):
    """Фикстура комментарий."""
    comment = Comment.objects.create(
        news=news,
        author=author,
        text='Текст комментария'
    )
    return comment


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name',
    ('news:home', 'users:login', 'users:logout', 'users:signup')
)
def test_pages_availability_for_anonymous_user(client, name):
    """
    Главная страница, страницы регистрации пользователей, входа в учётную
    запись и выхода из неё доступны анонимным пользователям.
    """
    url = reverse(name)
    response = client.get(url)
    assert response.status_code == OK


@pytest.mark.django_db
def test_pages_availability_for_author(client, news):
    """
    Страница отдельной новости доступна анонимному пользователю, а
    авторизованный пользователь не может зайти на страницы редактирования
    или удаления чужих комментариев.
    """
    url = reverse('news:detail', args=(news.pk,))
    response = client.get(url)
    assert response.status_code == OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    (
        (pytest.lazy_fixture('user_client'), NOT_FOUND),
        (pytest.lazy_fixture('author_client'), OK)
    ),
)
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete'),
)
def test_pages_availability_for_author(
    parametrized_client, name, comment, expected_status
):
    """
    Страницы удаления и редактирования комментария
    доступны автору комментария.
    """
    url = reverse(name, args=(comment.pk,))
    response = parametrized_client.get(url)
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, note_object',
    (
        ('news:edit', pytest.lazy_fixture('comment')),
        ('news:delete', pytest.lazy_fixture('comment')),
    ),
)
def test_redirects(client, name, note_object):
    """
    При попытке перейти на страницу редактирования или удаления комментария
    анонимный пользователь перенаправляется на страницу авторизации.
    """
    login_url = reverse('users:login')
    if note_object is not None:
        url = reverse(name, args=(note_object.pk,))
    else:
        url = reverse(name)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
