def check_short_desc(mapper, connection, target):
    if len(target.short_description) > 20:
        target.short_description = target.short_description[:20]

def delete_empty_desc(mapper, connection, target):
    if target.short_description and target.short_description.isspace():
        target.short_description = ""
    if target.long_description and target.long_description.isspace():
        target.long_description = ""
