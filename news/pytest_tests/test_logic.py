from http.client import OK, NOT_FOUND
import pytest
from pytest_django.asserts import assertRedirects, assertFormError

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from news.models import News, Comment
from news.forms import BAD_WORDS, WARNING

User = get_user_model()
COMMENT_TEXT='COMMENT_TEXT'
NEW_COMMENT_TEXT = 'Обновлённый комментарий'

@pytest.fixture
def user(django_user_model):  
    return django_user_model.objects.create(username='Пользователь')

@pytest.fixture
def user_client(user, client):
    client.force_login(user)
    return client

@pytest.fixture
def author(django_user_model):  
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def author_client(author, client):
    client.force_login(author)
    return client

@pytest.fixture
def news():
    news = News.objects.create(
        title='Заголовок',
        text='Текст заметки'
    )
    return news 

@pytest.fixture
def comment(news, author):
    comment = Comment.objects.create(
        news=news,
        author=author,
        text=COMMENT_TEXT
    )
    return comment

@pytest.fixture
def form_data():
    form_data={'text': COMMENT_TEXT}
    return form_data

@pytest.fixture
def form_data_new():
    form_data_new={'text': NEW_COMMENT_TEXT}
    return form_data_new

@pytest.fixture
def url(news):
    url = reverse('news:detail', args=(news.pk,))
    return url

@pytest.fixture
def delete_url(comment):
    delete_url = reverse('news:delete', args=(comment.pk,))
    return delete_url

@pytest.fixture
def edit_url(comment):
    edit_url = reverse('news:edit', args=(comment.pk,))
    return edit_url

@pytest.fixture
def url_to_comments(url):
    url_to_comments = url + '#comments'
    return url_to_comments

@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(url, client, form_data):
    """Проверка, что анонимный пользователь
    не может отправить комментарий."""
    client.post(url, data=form_data)
    comments_count = Comment.objects.count()
    assert comments_count == 0

@pytest.mark.django_db
def test_user_can_create_comment(author_client, url, form_data, news, author):
    """
    Проверка, что авторизованный пользователь
    может отправить комментарий.
    """
    response = author_client.post(url, data=form_data)
    assertRedirects(response, f'{url}#comments')
    comments_count = Comment.objects.count()
    assert comments_count == 1
    comment = Comment.objects.get()
    assert comment.text == COMMENT_TEXT
    assert comment.news == news
    assert comment.author == author 

def test_user_cant_use_bad_words(author_client, url):
    """
    Если комментарий содержит запрещённые слова,
    он не будет опубликован, а форма вернёт ошибку.
    """
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(url, data=bad_words_data)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    comments_count = Comment.objects.count()
    assert comments_count == 0

# Авторизованный пользователь может редактировать или удалять свои комментарии.

def test_author_can_delete_comment(author_client, delete_url, url_to_comments):
    """Авторизованный пользователь может удалять свои комментарии."""
    response = author_client.delete(delete_url)
    assertRedirects(response, url_to_comments)
    comments_count = Comment.objects.count()
    assert comments_count == 0

def test_author_can_edit_comment(
    author_client, form_data_new, edit_url, url_to_comments, comment
    ):
    """Авторизованный пользователь может редактировать свои комментарии."""
    response = author_client.post(edit_url, data=form_data_new)
    assertRedirects(response, url_to_comments)
    comment.refresh_from_db()
    assert comment.text == NEW_COMMENT_TEXT

def test_user_cant_delete_comment_of_another_user(user_client, delete_url):
    """Авторизованный пользователь не может удалять чужие комментарии."""
    response = user_client.delete(delete_url)
    assert response.status_code == NOT_FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 1

def test_user_cant_edit_comment_of_another_user(user_client, edit_url, form_data_new, comment):
    """Авторизованный пользователь не может редактировать чужие комментарии."""
    response = user_client.post(edit_url, data=form_data_new)
    assert response.status_code == NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == COMMENT_TEXT