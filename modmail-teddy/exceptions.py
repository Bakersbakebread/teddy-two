class UserIsBlocked(Exception):
    """
    Raised when user is blocked from sending modmail
    """

    pass


class NoNewCategory(Exception):
    """
    Raised when no "New" category is established on server
    """
