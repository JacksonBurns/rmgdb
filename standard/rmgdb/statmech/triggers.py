def check_short_desc(mapper, connection, target):
    if target.short_description is not None and len(target.short_description) > 50:
        print("short description > 50, consider using long.")


def delete_empty_desc(mapper, connection, target):
    if target.short_description is not None and target.short_description.isspace():
        target.short_description = ""
    if target.long_description is not None and target.long_description.isspace():
        target.long_description = ""
