from copy import deepcopy
from lxml.html import fromstring, tostring
from lxml.html.clean import Cleaner
from lxml.html.defs import safe_attrs
from core.exception import AlertException

class BaseSanitizer:

    common_allowed_tags_dict = {
        'text': {'span', 'strong', 'p'}
    }

    common_allowed_attrs_dict = {
        '*': {'style'},
    }

    def __init__(self, is_with_library_attrs=False):
        self.base_allowed_tags_dict = deepcopy(self.common_allowed_tags_dict)
        self.base_allowed_attrs_dict = deepcopy(self.common_allowed_attrs_dict)
        if is_with_library_attrs:
            self.base_allowed_attrs_dict['library'] = safe_attrs
        self.base_allowed_attrs_dict['library'] = safe_attrs

    def get_combined_filter_dict(self, base_allowed_dict, private_allowed_dict):
        for key, tags in private_allowed_dict.items():
            base_allowed_dict[key] = base_allowed_dict.get(key, set()).union(tags)
        return base_allowed_dict

    def get_cleaned_data(self, html_content):
        cleaned_html = self.cleaner.clean_html(html_content)
        parsed_tree = fromstring(cleaned_html)
        
        if parsed_tree.tag not in self.cleaner.allow_tags:
            cleaned_html = ''.join(tostring(child, encoding='unicode', method='html') for child in parsed_tree)
        if not cleaned_html:
            cleaned_html = parsed_tree.text
        return cleaned_html

    def get_uniformed_cleaned_data(self, cleaned_html, cleaning_count=5):
        count = 1
        try:
            for _ in range(cleaning_count):
                count += 1
                print("count:", count)
                double_cleaned_html = self.cleaner.clean_html(cleaned_html)
                parsed_tree = fromstring(double_cleaned_html)

                if parsed_tree.tag not in self.cleaner.allow_tags:
                    double_cleaned_html = ''.join(tostring(child, encoding='unicode', method='html') for child in parsed_tree)

                if not double_cleaned_html:
                    double_cleaned_html = parsed_tree.text

                if double_cleaned_html == cleaned_html:
                    break

                cleaned_html = double_cleaned_html

            return cleaned_html
        except:
            raise AlertException(f"해당 게시판에서 허용되지 않는 HTML 태그나 속성, 잘못된 형식 등의 이유로 등록할 수 없습니다. 내용을 정리해서 다시 등록해주세요.", 400)


class SubjectSanitizer(BaseSanitizer):

    private_allowed_tags_dict = dict()
    private_allowed_attrs_dict = dict()

    def __init__(self, is_with_library_attrs=False):
        super().__init__(is_with_library_attrs)
        self.cleaner = Cleaner(safe_attrs_only=True, remove_unknown_tags=False)
        combined_tags = self.get_combined_filter_dict(self.base_allowed_tags_dict, self.private_allowed_tags_dict)
        combined_attrs = self.get_combined_filter_dict(self.base_allowed_attrs_dict, self.private_allowed_attrs_dict)
        self.cleaner.allow_tags = {tag for tags in combined_tags.values() for tag in tags}
        self.cleaner.safe_attrs = {attr for attrs in combined_attrs.values() for attr in attrs}


class ContentSanitizer(BaseSanitizer):

    private_allowed_tags_dict = {
        'text': {'em', 'i', 'b', 'u', 'small', 'mark', 'del', 'ins', 'sub', 'sup'},
        'h_tags': {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'},
        'list': {'ul', 'ol', 'li', 'dl', 'dt', 'dd'},
        'table': {'table', 'th', 'tr', 'td', 'thead', 'tbody', 'tfoot', 'caption', 'col', 'colgroup'},
        'block': {'main', 'section', 'article', 'aside', 'nav'},
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

    def __init__(self, is_with_library_attrs=False):
        super().__init__(is_with_library_attrs)
        self.cleaner = Cleaner(safe_attrs_only=True, remove_unknown_tags=False)
        combined_tags = self.get_combined_filter_dict(self.base_allowed_tags_dict, self.private_allowed_tags_dict)
        combined_attrs = self.get_combined_filter_dict(self.base_allowed_attrs_dict, self.private_allowed_attrs_dict)
        self.cleaner.allow_tags = {tag for tags in combined_tags.values() for tag in tags}
        self.cleaner.safe_attrs = {attr for attrs in combined_attrs.values() for attr in attrs}