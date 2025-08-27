def check_short_desc(mapper, connection, target):
    """Check and truncate short descriptions if they exceed 20 characters."""
    if len(target.short_description) > 20:
        print("Truncating short description (consider using long).")
        target.short_description = target.short_description[0:20]


def delete_empty_desc(mapper, connection, target):
    """Clean up empty or whitespace-only descriptions."""
    if target.short_description.isspace():
        target.short_description = ""
    if target.long_description.isspace():
        target.long_description = ""

def validate_solvent_parameters(mapper, connection, target):
    """Validate solvent parameters are within reasonable ranges."""

    # Dielectric constant should be positive
    if hasattr(target, 'eps') and target.eps is not None:
        if target.eps <= 0:
            print(f"Warning: Dielectric constant {target.eps} is not positive")


def validate_data_count(mapper, connection, target):
    """Validate data count metrics are reasonable."""
    if hasattr(target, 'dGsolvCount') and target.dGsolvCount is not None:
        if target.dGsolvCount < 0:
            print(f"Warning: dGsolvCount {target.dGsolvCount} is negative")
    
    if hasattr(target, 'dHsolvCount') and target.dHsolvCount is not None:
        if target.dHsolvCount < 0:
            print(f"Warning: dHsolvCount {target.dHsolvCount} is negative")
    
    # MAE values should be positive
    if hasattr(target, 'dGsolvMAE_value') and target.dGsolvMAE_value is not None:
        if target.dGsolvMAE_value < 0:
            print(f"Warning: dGsolvMAE_value {target.dGsolvMAE_value} is negative")
    
    if hasattr(target, 'dHsolvMAE_value') and target.dHsolvMAE_value is not None:
        if target.dHsolvMAE_value < 0:
            print(f"Warning: dHsolvMAE_value {target.dHsolvMAE_value} is negative")
