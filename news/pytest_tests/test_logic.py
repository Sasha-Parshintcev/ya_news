import pytest
from http.client import NOT_FOUND
from pytest_django.asserts import assertRedirects, assertFormError

from news.models import Comment
from news.forms import BAD_WORDS, WARNING

COMMENT_TEXT = 'Текст комментария'
NEW_COMMENT_TEXT = 'Обновлённый комментарий'

pytestmark = pytest.mark.django_db


def test_anonymous_user_cant_create_comment(detail_url, client, form_data):
    """
    Проверка, что анонимный пользователь
    не может отправить комментарий.
    """
    comments_count = Comment.objects.count()
    client.post(detail_url, data=form_data)
    assert comments_count == Comment.objects.count()


@pytest.mark.django_db
def test_user_can_create_comment(author_client, detail_url,
                                 form_data, news, author):
    """
    Проверка, что авторизованный пользователь
    может отправить комментарий.
    """
    comments_count = Comment.objects.count()
    response = author_client.post(detail_url, data=form_data)
    assertRedirects(response, f'{detail_url}#comments')
    assert comments_count + 1 == Comment.objects.count()
    comment = Comment.objects.order_by('pk').last()
    assert comment.text == COMMENT_TEXT
    assert comment.news == news
    assert comment.author == author


@pytest.mark.django_db
def test_user_cant_use_bad_words(author_client, detail_url):
    """
    Если комментарий содержит запрещённые слова,
    он не будет опубликован, а форма вернёт ошибку.
    """
    comments_count = Comment.objects.count()
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(detail_url, data=bad_words_data)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    assert comments_count == Comment.objects.count()


@pytest.mark.django_db
def test_author_can_delete_comment(author_client, delete_url, url_to_comments):
    """Авторизованный пользователь может удалять свои комментарии."""
    comments_count = Comment.objects.count()
    response = author_client.delete(delete_url)
    assertRedirects(response, url_to_comments)
    assert comments_count - 1 == Comment.objects.count()


@pytest.mark.django_db
def test_author_can_edit_comment(
    author_client, form_data_new, edit_url,
    url_to_comments, comment, news, author
):
    """Авторизованный пользователь может редактировать свои комментарии."""
    comments_count = Comment.objects.count()
    response = author_client.post(edit_url, data=form_data_new)
    assertRedirects(response, url_to_comments)
    comment.refresh_from_db()
    assert comments_count == Comment.objects.count()
    assert comment.text == NEW_COMMENT_TEXT
    assert comment.news == news
    assert comment.author == author


def test_user_cant_delete_comment_of_another_user(user_client, delete_url):
    """Авторизованный пользователь не может удалять чужие комментарии."""
    comments_count = Comment.objects.count()
    response = user_client.delete(delete_url)
    assert response.status_code == NOT_FOUND
    assert comments_count == Comment.objects.count()


def test_user_cant_edit_comment_of_another_user(
        user_client, edit_url, news, form_data_new, comment, author
):
    """Авторизованный пользователь не может редактировать чужие комментарии."""
    comments_count = Comment.objects.count()
    response = user_client.post(edit_url, data=form_data_new)
    assert response.status_code == NOT_FOUND
    comment.refresh_from_db()
    assert comments_count == Comment.objects.count()
    assert comment.text == COMMENT_TEXT
    assert comment.news == news
    assert comment.author == author
