from rest_framework.routers import DefaultRouter


class CustomRouter(DefaultRouter):
    """Custom DRF router that doesn't apply format_suffix_patterns."""
    def get_urls(self):
        """Override to prevent format_suffix_patterns."""
        urls = super().get_urls()
        # Don't apply format suffix patterns
        return urls
