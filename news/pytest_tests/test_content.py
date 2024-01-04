import pytest
from datetime import timedelta

from django.utils import timezone
from django.urls import reverse
from django.conf import settings

from news.models import News


@pytest.mark.django_db
def test_count_news(client):
    """Проверка, что количество новостей на главной странице — не более 10."""
    all_news = [
        News(title=f'Новость {index}', text='Просто текст.')
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    News.objects.bulk_create(all_news)
    response = client.get(reverse('news:home'))
    object_list = response.context.get('object_list')
    if object_list is None:
        raise ('Исключение')
    news_count = len(object_list)
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client):
    """
    Проверка на то, что новости отсортированы от самой свежей к самой старой.
    Свежие новости в начале списка.
    """
    response = client.get(reverse('news:home'))
    object_list = response.context.get('object_list')
    if object_list is None:
        raise ('Исключение')
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comments_order(news, client, detail_url, comments):
    """
    Проверка сортировки комментариев на странице отдельной новости:
    старые в начале списка, новые — в конце.
    """
    now = timezone.now()
    comments.created = now + timedelta()
    comments.save()
    response = client.get(detail_url)
    assert 'news' in response.context
    news = response.context.get('news')
    if news is None:
        raise ('Исключение')
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
    form = response.context.get('form')
    if form is None:
        raise ('Исключение')
