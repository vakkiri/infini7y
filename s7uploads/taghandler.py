from .models import Tag, Upload


def add_tag(tagline, upload):
    tags = tagline.split("#")

    for tag in tags:
        tag = tag.strip()
        if len(tag) > 0:
            tag_obj = Tag.objects.filter(name=tag)

            if len(tag_obj) == 0:
                tag_obj = Tag(name=tag)
                tag_obj.save()
                print("new tag: ", tag)
            elif len(tag_obj) > 1:
                raise AttributeError(
                    f"ERROR: More than one tag object returned for name {tag}"
                )
            else:
                tag_obj = tag_obj[0]

            tag_obj.uploads.add(upload)
