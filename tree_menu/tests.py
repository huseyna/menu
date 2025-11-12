from django.core.exceptions import ValidationError
from django.template import Context, Template
from django.test import RequestFactory, TestCase
from django.urls import reverse

from tree_menu.models import Menu, MenuItem


class DrawMenuTagTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.menu = Menu.objects.create(name="main_menu", title="Main menu")
        MenuItem.objects.create(
            menu=self.menu,
            title="Home",
            named_url="home",
            order=0,
        )
        catalog = MenuItem.objects.create(
            menu=self.menu,
            title="Catalog",
            named_url="catalog",
            order=1,
        )
        MenuItem.objects.create(
            menu=self.menu,
            parent=catalog,
            title="Item 1",
            url="/catalog/item-1/",
            order=0,
        )

    def test_draw_menu_uses_single_query(self) -> None:
        template = Template("{% load tree_menu_tags %}{% draw_menu 'main_menu' %}")
        request = self.factory.get(reverse("catalog"))
        with self.assertNumQueries(1):
            template.render(Context({"request": request}))

    def test_active_branch_is_expanded(self) -> None:
        template = Template("{% load tree_menu_tags %}{% draw_menu 'main_menu' %}")
        request = self.factory.get("/catalog/item-1/")
        rendered = template.render(Context({"request": request}))
        self.assertIn("tree-menu__item--active", rendered)
        self.assertIn("tree-menu__children", rendered)

    def test_named_url_must_resolve(self) -> None:
        item = MenuItem(menu=self.menu, title="Broken link", named_url="unknown")
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_requires_at_least_one_url(self) -> None:
        item = MenuItem(menu=self.menu, title="No URL provided")
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_duplicate_urls_not_allowed(self) -> None:
        with self.assertRaises(ValidationError):
            MenuItem.objects.create(
                menu=self.menu,
                title="Duplicate home",
                named_url="home",
                order=5,
            )

    def test_direct_url_without_leading_slash_is_normalized(self) -> None:
        item = MenuItem.objects.create(
            menu=self.menu,
            title="Custom link",
            url="catalog/custom/",
            order=10,
        )
        self.assertEqual(item.url, "/catalog/custom/")
        self.assertEqual(item.get_url(), "/catalog/custom/")
