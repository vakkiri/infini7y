from django import template

register = template.Library()

@register.filter
def user_owns_upload(user, uploader):
    return user is not None and uploader is not None and user.id == uploader.user.id

