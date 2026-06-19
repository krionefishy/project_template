"""
Dishka provider for example_domain use cases.

Copy this file for each new domain. Register every UseCase with provide().
Scope is REQUEST so each HTTP request gets fresh instances.
"""
from dishka import Provider, Scope, provide

from backend.app.example_domain.usecases.create_example_usecase import CreateExampleUseCase
from backend.app.example_domain.usecases.get_example_usecase import GetExampleUseCase
from backend.app.example_domain.usecases.upload_example_file_usecase import UploadExampleFileUseCase


class ExampleDomainProvider(Provider):
    scope = Scope.REQUEST

    get_example = provide(GetExampleUseCase)
    create_example = provide(CreateExampleUseCase)
    upload_example_file = provide(UploadExampleFileUseCase)
