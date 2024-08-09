def check_short_desc(mapper, connection, target):
    if len(target.short_description) > 20:
        print("Truncating short description (consider using long).")
        target.short_description = target.short_description[0:20]
