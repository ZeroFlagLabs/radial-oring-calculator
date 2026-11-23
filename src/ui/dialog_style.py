"""Shared, DPI-conscious action-button sizing across the calculator dialogs."""

# Measured with the normal Windows Qt platform (96 logical DPI), not
# QT_QPA_PLATFORM=offscreen: "Use selected size" is ~88 logical pixels wide.
# 12px of padding on each side gives the intended 112px action width.
# The headless offscreen platform reports inflated font metrics, so do not
# derive the visible button width from its QFontMetrics.
ACTION_BUTTON_WIDTH = 112


def standard_action_width(button):
    """Return the uniform, compact dialog action width in Qt logical pixels."""
    return ACTION_BUTTON_WIDTH


def set_standard_action_width(button):
    button.setFixedWidth(standard_action_width(button))
