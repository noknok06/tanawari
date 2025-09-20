from django import template

register = template.Library()

@register.filter
def range_filter(value):
    """数値をrange()オブジェクトに変換するフィルター"""
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return range(0)

# 後方互換性のため、rangeという名前でも登録
@register.filter(name='range')
def range_alias(value):
    """rangeフィルターのエイリアス"""
    return range_filter(value)