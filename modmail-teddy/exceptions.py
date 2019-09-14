class UserIsBlocked(Exception):
    """
    Raised when user is blocked from sending modmail
    """

    pass


class NoNewCategory(Exception):
    """
    Raised when no "New" category is established on server
    """


class WaitingForMessageType(Exception):
    """
    Raised when user hasn't specified what type of message they want to send.
    """
