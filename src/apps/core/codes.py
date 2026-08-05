import re


def next_code(queryset, prefix, field='code', width=3):
    pattern = re.compile(rf'^{re.escape(prefix)}-(\d+)$')
    highest = 0

    for value in queryset.values_list(field, flat=True):
        if not value:
            continue

        match = pattern.match(str(value))
        if match:
            highest = max(highest, int(match.group(1)))

    return f'{prefix}-{highest + 1:0{width}d}'
