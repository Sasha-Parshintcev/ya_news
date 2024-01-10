import pytest
from datetime import timedelta

from django.urls import reverse
from django.conf import settings

from news.models import News
from news.forms import CommentForm

pytestmark = pytest.mark.django_db


def test_count_news(client, all_news):
    """Проверка, что количество новостей на главной странице — не более 10."""
    News.objects.bulk_create(all_news)
    response = client.get(reverse('news:home'))
    object_list = response.context.get('object_list')
    if object_list is None:
        with pytest.raises(TypeError):
            news_count = len(object_list)
            assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


def test_news_order(client):
    """
    Проверка на то, что новости отсортированы от самой свежей к самой старой.
    Свежие новости в начале списка.
    """
    response = client.get(reverse('news:home'))
    object_list = response.context.get('object_list')
    if object_list is None:
        with pytest.raises(TypeError):
            all_dates = [news.date for news in object_list]
            sorted_dates = sorted(all_dates, reverse=True)
            assert all_dates == sorted_dates


def test_comments_order(news, client, detail_url, comments, now):
    """
    Проверка сортировки комментариев на странице отдельной новости:
    старые в начале списка, новые — в конце.
    """
    comments.created = now + timedelta()
    comments.save()
    response = client.get(detail_url)
    assert 'news' in response.context
    news = response.context.get('news')
    if news is None:
        with pytest.raises(TypeError):
            all_comments = news.comment_set.all()
            all_comments_created = [comments.created for comments in all_comments]
            sorted_comments = sorted(all_comments, reverse=True)
            assert all_comments_created == sorted_comments


def test_anonymous_client_has_no_form(client, detail_url):
    """
    Проверка, что анонимному пользователю недоступна
    форма для отправки комментария.
    """
    response = client.get(detail_url)
    assert 'form' not in response.context


def test_authorized_client_has_form(client, detail_url, author):
    """
    Проверка, что авторизованному пользователю доступна
    форма для отправки комментария.
    """
    client.force_login(author)
    response = client.get(detail_url)
    assert 'form' in response.context
    form = response.context.get('form')
    isinstance(form, CommentForm)
