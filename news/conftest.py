import pytest

from django.urls import reverse

from news.models import News, Comment

COMMENT_TEXT = 'Текст комментария'
NEW_COMMENT_TEXT = 'Обновлённый комментарий'

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
        text=COMMENT_TEXT
    )
    return comment


@pytest.fixture
def form_data():
    """Фикстура форма."""
    form_data = {'text': COMMENT_TEXT}
    return form_data


@pytest.fixture
def form_data_new():
    """Фикстура новая форма."""
    form_data_new = {'text': NEW_COMMENT_TEXT}
    return form_data_new


@pytest.fixture
def detail_url(news):
    """Фикстура путь к отдельной новости."""
    detail_url = reverse('news:detail', args=(news.pk,))
    return detail_url


@pytest.fixture
def delete_url(comment):
    """Фикстура путь к отдельной странице удаления."""
    delete_url = reverse('news:delete', args=(comment.pk,))
    return delete_url


@pytest.fixture
def edit_url(comment):
    """Фикстура путь к отдельной странице редактирования."""
    edit_url = reverse('news:edit', args=(comment.pk,))
    return edit_url


@pytest.fixture
def url_to_comments(detail_url):
    """Фикстура путь к отдельному комментарию."""
    url_to_comments = detail_url + '#comments'
    return url_to_comments

@pytest.fixture
def detail_url(news):
    """Фикстура пути к отдельной новости."""
    detail_url = reverse('news:detail', args=(news.pk,))
    return detail_url

@pytest.fixture
def comments(news, author):
    for index in range(2):
        comments = Comment.objects.create(
            news=news, author=author, text=f'Tекст {index}',
        )
    return comments
