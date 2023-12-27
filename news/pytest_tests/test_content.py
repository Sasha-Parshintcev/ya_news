import pytest
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from news.models import News, Comment

User = get_user_model()


@pytest.fixture
def author(django_user_model):
    """Фикстура автор."""
    return django_user_model.objects.create(username='Автор')


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


@pytest.fixture
def detail_url(news):
    """Фикстура пути к отдельной новости."""
    detail_url = reverse('news:detail', args=(news.pk,))
    return detail_url


@pytest.mark.django_db
def test_count_news(client):
    """Проверка, что количество новостей на главной странице — не более 10."""
    all_news = [
        News(title=f'Новость {index}', text='Просто текст.')
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    News.objects.bulk_create(all_news)
    response = client.get(reverse('news:home'))
    object_list = response.context['object_list']
    news_count = len(object_list)
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client):
    """
    Проверка на то, что новости отсортированы от самой свежей к самой старой.
    Свежие новости в начале списка.
    """
    response = client.get(reverse('news:home'))
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comments_order(news, client, author, detail_url):
    """
    Проверка сортировки комментариев на странице отдельной новости:
    старые в начале списка, новые — в конце.
    """
    author = User.objects.create(username='Комментатор')
    now = timezone.now()
    for index in range(2):
        comment = Comment.objects.create(
            news=news, author=author, text=f'Tекст {index}',
        )
        comment.created = now + timedelta(days=index)
        comment.save()
    response = client.get(detail_url)
    assert 'news' in response.context
    news = response.context['news']
    all_comments = news.comment_set.all()
    assert all_comments[0].created < all_comments[1].created


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, detail_url):
    """
    Проверка, что анонимному пользователю недоступна
    форма для отправки комментария.
    """
    response = client.get(detail_url)
    assert 'form' not in response.context


@pytest.mark.django_db
def test_authorized_client_has_form(client, detail_url, author):
    """
    Проверка, что авторизованному пользователю доступна
    форма для отправки комментария.
    """
    client.force_login(author)
    response = client.get(detail_url)
    assert 'form' in response.context
