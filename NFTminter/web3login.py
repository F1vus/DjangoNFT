import secrets
import names
import string
import shortuuid

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from .models import UserProfile

from eth_account.messages import defunct_hash_message
from web3.auto import w3


def auth_web3(request):
    public_address = request.POST["accountAddress"]
    signature = request.POST["signature"]
    csrf_token = request.POST["csrfmiddlewaretoken"]

    original_message = f"Sign to auth {csrf_token}"
    message_hash = defunct_hash_message(text=original_message)
    signer = w3.eth.account._recover_hash(message_hash, signature=signature)
    short_uuid = shortuuid.uuid()

    if signer == public_address:

        user_profile = UserProfile.objects.filter(eth_account_address=public_address).first()
        if user_profile:
            try:
                user = user_profile.user
            except:
                messages.add_message(request, messages.WARNING, ("User is not found!"))
                return HttpResponseRedirect(reverse("index",))

            user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user)
            return HttpResponseRedirect(reverse("index"))

        else:
            alphabet = string.ascii_letters + string.digits
            password = "".join(secrets.choice(alphabet) for _ in range(20))

            first_name = names.get_first_name()
            last_name = names.get_last_name()
            email = f"{short_uuid}@gmail.com"

            user = User.objects.create_user(email=email, username=short_uuid, first_name=first_name,
                                            last_name=last_name, password=password)

            user_profile = UserProfile()
            user_profile.user = user
            user_profile.eth_account_address = public_address
            user_profile.save()

            user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user)

            messages.success(request, ("Success register!."))
            return HttpResponseRedirect(reverse("index"))

    else:
        messages.add_message(request, messages.WARNING, ("Refresh the page!"))
        return HttpResponseRedirect(
            reverse("index",))