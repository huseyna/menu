from django.shortcuts import render


def dynamic_page(request, slug: str):
    """Simple demo page that renders the requested slug."""
    title = slug.replace("-", " ").strip().title() or "Страница"
    return render(
        request,
        "pages/page.html",
        {
            "page_title": title,
        },
    )
