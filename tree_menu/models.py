from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import NoReverseMatch, reverse


class Menu(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Internal name used in the draw_menu template tag.",
    )
    title = models.CharField(
        max_length=150,
        blank=True,
        help_text="Optional human-readable title shown in admin.",
    )

    class Meta:
        verbose_name = "Menu"
        verbose_name_plural = "Menus"
        ordering = ("name",)

    def __str__(self):
        return self.title or self.name


class MenuItem(models.Model):
    menu = models.ForeignKey(
        Menu,
        related_name="items",
        on_delete=models.CASCADE,
    )
    parent = models.ForeignKey(
        "self",
        related_name="children",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=200)
    named_url = models.CharField(
        max_length=200,
        blank=True,
        help_text="Named URL pattern to use for this item.",
    )
    url = models.CharField(
        max_length=500,
        blank=True,
        help_text="Direct URL for this item.",
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Ordering of siblings inside the same parent.",
    )

    class Meta:
        verbose_name = "Menu item"
        verbose_name_plural = "Menu items"
        ordering = ("menu", "parent__id", "order", "id")

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()

        if self.parent and self.parent.menu != self.menu:
            raise ValidationError("Parent item must belong to the same menu.")

        resolved_url = self._resolve_url()
        self._check_for_duplicate_urls(resolved_url)

        self._resolved_url = resolved_url

    def _resolve_url(self):
        if self.named_url:
            try:
                return reverse(self.named_url)
            except NoReverseMatch as exc:
                raise ValidationError(
                    {"named_url": f"Could not find named URL '{self.named_url}': {exc}"}
                ) from exc
        elif self.url:
            return self._normalize_direct_url(self.url)
        else:
            raise ValidationError("Specify either a named URL or a direct URL.")

    def _check_for_duplicate_urls(self, resolved_url):
        if resolved_url:
            duplicate_filter = MenuItem.objects.filter(menu=self.menu).exclude(pk=self.pk)
            url_filter = Q(url=resolved_url)
            if self.named_url:
                url_filter |= Q(named_url=self.named_url)
            if duplicate_filter.filter(url_filter).exists():
                raise ValidationError(
                    {"url": f"This URL already exists in the selected menu '{resolved_url}'."}
                )

    def get_url(self):
        if hasattr(self, "_resolved_url"):
            return self._resolved_url
        if self.named_url:
            try:
                return reverse(self.named_url)
            except NoReverseMatch:
                return ""
        return self.url or ""

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @staticmethod
    def _normalize_direct_url(raw_url):
        url = raw_url.strip()
        if not url:
            return ""
        if url.startswith(("http://", "https://")):
            return url
        return f"/{url.lstrip('/')}"
