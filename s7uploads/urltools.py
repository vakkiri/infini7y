import re

def strip_get_tags(get_str):
    get_str = re.sub(r'tags=[^&]*?$', '', get_str)
    get_str = re.sub(r'&+?', '&', get_str)
    return get_str


def condense_url_get(get):
    # only keep the last order_by
    order_by = get.get('order_by')
    print("order by: ", order_by)

    # keep *all* filters and condense them
    filter_slugs = get.getlist('filter')
    filter_slugs = [slug for slug in filter_slugs if filter_slugs.count(slug) % 2 == 1]
    filter_url = '#'.join(filter_slugs)
    print("filter: ", filter_url)

    # only keep last search
    search_by = get.get('search_by')
    print("search: ", search_by)

    condensed_get = ''
    if order_by is not None:
        condensed_get = condensed_get + 'order_by=' + order_by
    if len(filter_slugs) > 0:
        if len(condensed_get) > 0:
            condensed_get = condensed_get + '&'
        condensed_get = condensed_get + 'filter=' + filter_url
    if search_by is not None:
        if len(condensed_get) > 0:
            condensed_get = condensed_get + '&'
        condensed_get = condensed_get + 'tags=' + search_by
    if len(condensed_get) > 0:
        condensed_get = '?' + condensed_get

    print("New get: ", condensed_get)

    return order_by, filter_slugs, search_by, condensed_get
