"""Custom exceptions."""

class CtesiError(Exception):
    """Basic exception for this application."""

class UserNotFoundInLDAP(CtesiError):
    """Raised when a user is not found in AD. This sometimes happens even if the user is in AD, but the server is misbehaving."""

class ExperimentTypeSearchParamsMissing(CtesiError):
    """Raised when search params for an experiment type are not defined."""

class SearchOptionNotCustomizeable(CtesiError):
    """Raised when an attempt to pass a value for a search option that is not meant to be customized."""
