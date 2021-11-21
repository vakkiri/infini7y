from django import template

register = template.Library()


@register.simple_tag
def update_query(request, **kwargs):
    updated = request.GET.copy()

    for k in kwargs:
        updated[k] = kwargs[k]

    return updated.urlencode()


@register.simple_tag
def toggle_query(request, **kwargs):
    updated = request.GET.copy()

    # intended behaviour: we will toggle the query item "off" if it was already equal to
    # the selected value. Otherwise, we update it to that value. This is for things such as
    # filters, where we may want to add and remove a certain filter.
    for k in kwargs:
        if k in updated and kwargs[k] == updated[k]:
            updated.pop(k)
        else:
            updated[k] = kwargs[k]

    return updated.urlencode()
