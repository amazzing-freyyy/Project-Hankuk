from rest_framework import serializers
from django.core.files.base import ContentFile
from urllib.request import urlopen
from urllib.parse import urlparse
import os

class AvatarField(serializers.ImageField):
    def to_internal_value(self, data):
        # If it's a URL, download and convert to a file-like object
        if isinstance(data, str) and data.startswith(('http://', 'https://')):
            parsed_url = urlparse(data)
            filename = os.path.basename(parsed_url.path)
            content = urlopen(data).read()
            return ContentFile(content, name=filename)
        # Otherwise, fallback to normal ImageField handling
        return super().to_internal_value(data)
