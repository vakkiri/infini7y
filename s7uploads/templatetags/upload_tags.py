from django import template

register = template.Library()


@register.filter
def user_owns_upload(user, uploader):
    return user is not None and uploader is not None and user == uploader.user


@register.filter
def user_owns_review(user, review):
    return user is not None and review is not None and user == review.user.user
