"""Output accumulator — collects HTML fragments written by W()."""

H = []


def W(s):
    H.append(s)


def reset_output():
    """Clear the output accumulator (called between patches)."""
    H.clear()


def get_output():
    """Return the accumulated HTML as a single string."""
    return ''.join(H)
