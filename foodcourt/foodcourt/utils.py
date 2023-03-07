import string, random
from django.utils.text import slugify
from enum import Enum

# To create slug url
def slug_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)

def random_string_generator(size = 10, chars = string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def unique_slug_generator(instance, new_slug = None):
    if new_slug is not None:
        slug = new_slug
    else:
        slug = "slug" + str(random.randint(0,10000)) + random_string_generator(size = 4)

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(slug = slug).exists()

    if qs_exists:
        new_slug = "{slug}-{randstr}".format(
            slug = slug, randstr = random_string_generator(size = 4))
        return unique_slug_generator(instance, new_slug = new_slug)
    return slug