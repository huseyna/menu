from django.contrib import admin

from .models import Menu, MenuItem


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = ("title", "parent", "named_url", "url", "order")
    ordering = ("order", "title")
    autocomplete_fields = ("parent",)


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("name", "title")
    search_fields = ("name", "title")
    inlines = (MenuItemInline,)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("title", "menu", "parent", "order")
    list_filter = ("menu",)
    search_fields = ("title", "named_url", "url")
    ordering = ("menu", "parent__id", "order", "title")
    autocomplete_fields = ("menu", "parent")
