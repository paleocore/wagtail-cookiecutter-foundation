from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page
from wagtail.images.models import Image


IMAGE_ORDER_TYPES = (
    (1, 'Image title'),
    (2, 'Newest image first'),
)


class GalleryIndex(Page):
    intro = RichTextField(
        blank=True,
        verbose_name=_('Intro text'),
        help_text=_('Optional text to go with the intro text.')
    )
    collection = models.ForeignKey(
        'wagtailcore.Collection',
        verbose_name=_('Collection'),
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text=_('Show images in this collection in the gallery view.')
    )
    images_per_page = models.IntegerField(
        default=8,
        verbose_name=_('Images per page'),
        help_text=_('How many images there should be on one page.')
    )
    order_images_by = models.IntegerField(choices=IMAGE_ORDER_TYPES, default=1)

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname='full title'),
        FieldPanel('collection'),
        FieldPanel('images_per_page', classname='full title'),
        FieldPanel('order_images_by'),
    ]

    @property
    def images(self):
        return get_gallery_images(self.collection.name, self)

    def get_context(self, request):
        images = self.images
        page = request.GET.get('page')
        paginator = Paginator(images, self.images_per_page)
        try:
            images = paginator.page(page)
        except PageNotAnInteger:
            images = paginator.page(1)
        except EmptyPage:
            images = paginator.page(paginator.num_pages)
        context = super(GalleryIndex, self).get_context(request)
        context['gallery_images'] = images
        return context

    class Meta:
        verbose_name = _('Photo Gallery')
        verbose_name_plural = _('Photo Galleries')

    template = getattr(settings, 'GALLERY_TEMPLATE', 'gallery/gallery_index.html')


def get_gallery_images(collection, page=None, tags=None):
    images = None
    try:
        images = Image.objects.filter(collection__name=collection)
        if page:
            if page.order_images_by == 0:
                images = images.order_by('title')
            elif page.order_images_by == 1:
                images = images.order_by('-created_at')
    except Exception as e:
        pass
    if images and tags:
        images = images.filter(tags__name__in=tags).distinct()
    return images
