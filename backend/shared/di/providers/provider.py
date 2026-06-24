"""
Master list of all Dishka providers.

Add a new XxxProvider import and entry in ALL_PROVIDERS when you add a new domain.
"""
from dishka import Provider
from dishka.integrations.fastapi import FastapiProvider

from backend.shared.di.providers.app import AppProvider, SessionProvider
from backend.shared.di.providers.auth import AuthContextProvider, AuthProvider, AuthUsecaseProvider
from backend.shared.di.providers.example_domain import ExampleDomainProvider

ALL_PROVIDERS: list[Provider] = [
    AppProvider(),
    FastapiProvider(),
    AuthProvider(),
    AuthContextProvider(),
    AuthUsecaseProvider(),
    ExampleDomainProvider(),
    SessionProvider(),
]
