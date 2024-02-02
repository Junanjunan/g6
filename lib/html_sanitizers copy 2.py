import abc
import bleach
from bleach.css_sanitizer import CSSSanitizer, ALLOWED_CSS_PROPERTIES


class BaseSanitizer(metaclass=abc.ABCMeta):

    common_allowed_tags_dict = {
        'text': {'span', 'p', 'strong'}
    }

    common_allowed_attrs_dict = {
        '*': {'style', 'title'},
    }

    def __init__(self):
        self.css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_CSS_PROPERTIES)
    
    def combine_filter_dict(self, common_allowed_dict, private_allowed_dict):
        combined_filter_dict = common_allowed_dict.copy()
        for key, tags in private_allowed_dict.items():
            combined_filter_dict[key] = combined_filter_dict.get(key, set()).union(tags)
        return combined_filter_dict

    @abc.abstractmethod
    def clean(self, text):
        pass


class SubjectSanitizer(BaseSanitizer):
    private_allowed_tags_dict = dict()
    private_allowed_attrs_dict = dict()

    def __init__(self):
        super().__init__()
        self.allowed_tags_dict = self.combine_filter_dict(self.common_allowed_tags_dict, self.private_allowed_tags_dict)
        self.allowed_attrs_dict = self.combine_filter_dict(self.common_allowed_attrs_dict, self.private_allowed_attrs_dict)

    def clean(self, subject):
        return bleach.clean(subject, tags=self.allowed_tags['text'], attributes=self.allowed_attrs_dict, css_sanitizer=self.css_sanitizer)

    


class ContentSanitizer(BaseSanitizer):


    private_allowed_tags_dict = {
        'text': {'em', 'i', 'b', 'u', 'small', 'mark', 'del', 'ins', 'sub', 'sup'},
        'h_tags': {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'},
        'list': {'ul', 'ol', 'li', 'dl', 'dt', 'dd'},
        'table': {'table', 'th', 'tr', 'td', 'thead', 'tbody', 'tfoot', 'caption', 'col', 'colgroup'},
        'block': {'div', 'main', 'section', 'article', 'aside', 'nav'},
        'formatting': {'blockquote', 'hr', 'br'},
        'media': {'img', 'audio', 'video', 'source', 'track'},
        'link': {'a'},
    }

    private_allowed_attrs_dict = {
        'a': {'href', 'title', 'accesskey', 'class', 'dir', 'id', 'lang', 'name', 'rel', 'tabindex', 'type', 'target'},
        'table': {'border', 'cellspacing', 'cellpadding', 'align', 'bgcolor', 'summary'},
        'th': {'scope'},
        'img': {'src', 'alt', 'title', 'width', 'height', 'align'},
    }

    def __init__(self):
        super().__init__()
        self.allowed_tags_dict = self.combine_filter_dict(self.common_allowed_tags_dict, self.private_allowed_tags_dict)
        self.allowed_attrs_dict = self.combine_filter_dict(self.common_allowed_attrs_dict, self.private_allowed_attrs_dict)

    def clean(self, subject):
        return bleach.clean(subject, tags=self.allowed_tags['text'], attributes=self.allowed_attrs_dict, css_sanitizer=self.css_sanitizer)



atd_0 = {
    'text': ['span', 'p', 'strong']
}

atd_1 = {
    'text': ['h1']
}

atd_2 = {
    'text': ['h2', 'h3']
}

allowed_title_tags_dict = {
    'text': ['span', 'p', 'strong']
}
allowed_tags_dict = {
    'text': ['em', 'i', 'b', 'u', 'small', 'mark', 'del', 'ins', 'sub', 'sup'],
    'h_tags': ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
    'list': ['ul', 'ol', 'li', 'dl', 'dt', 'dd'],
    'table': ['table', 'th', 'tr', 'td', 'thead', 'tbody', 'tfoot', 'caption', 'col', 'colgroup'],
    'block': ['div', 'main', 'section', 'article', 'aside', 'nav'],
    'formatting': ['blockquote', 'hr', 'br'],
    'media': ['img', 'audio', 'video', 'source', 'track'],
    'link': ['a'],
}
allowed_title_tags = [tag for tags in allowed_title_tags_dict.values() for tag in tags]
allowed_tags = [tag for tags in allowed_tags_dict.values() for tag in tags]
allowed_attrs = {
    '*': ['style', 'class', 'id', 'title'],
    'a': ['href', 'title', 'accesskey', 'class', 'dir', 'id', 'lang', 'name', 'rel', 'tabindex', 'type', 'target'],
    'table': ['border', 'cellspacing', 'cellpadding', 'align', 'bgcolor', 'summary'],
    'th': ['scope'],
    'img': ['src', 'alt', 'title', 'width', 'height', 'align'],
}
allowed_css_properties = ALLOWED_CSS_PROPERTIES
allowed_css_sanitizer = CSSSanitizer(allowed_css_properties=allowed_css_properties)

subject = bleach.clean(wr_subject, tags=allowed_title_tags, attributes=allowed_attrs, css_sanitizer=allowed_css_sanitizer)
content = bleach.clean(wr_content, tags=allowed_tags, attributes=allowed_attrs, css_sanitizer=allowed_css_sanitizer)