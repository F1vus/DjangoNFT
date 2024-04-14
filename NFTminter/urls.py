from django.urls import path

from . import views
from . import web3login
from . import mintNft

urlpatterns = [
    path("", views.index, name="index"),
    path("web", web3login.auth_web3, name="web3login"),
    path("mint", mintNft.mintNft, name="mintNft")
]