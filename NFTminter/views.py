from django.http import HttpResponse
from django.shortcuts import render
from django.core.handlers.wsgi import WSGIRequest
from .models import UserProfile

import os
from dotenv import load_dotenv
import requests

load_dotenv()


def index(request: WSGIRequest) -> HttpResponse:
    shortWalletVersion = ''
    if request.user.is_authenticated:
        user_profile = UserProfile.objects.filter(user=request.user).first()
        eth = user_profile.eth_account_address
        shortWalletVersion = eth[0:7] + '...'

    if request.method == "GET":
        context = {'ethAdress': shortWalletVersion}
        return render(request, "NFTminter/index.html", context)
    elif request.method == "POST":
        if request.POST['prompt']:
            imageBase64 = generate_image(request.POST['prompt'])

            context = {'ethAdress': shortWalletVersion,
                       'imageNft': 'data:image/png;base64,'+imageBase64,
                       'minted': False}
            response = render(request, "NFTminter/index.html", context)
            response.set_cookie('nameNFT', request.POST['prompt'])
            response.set_cookie('shortWalletVersion', shortWalletVersion)
            return response
        else:
            return render(request, "NFTminter/index.html")


def generate_image(prompt: str) -> str:
    engine_id = "stable-diffusion-v1-6"
    api_key = os.environ.get('STABILITY_API_KEY')

    response = requests.post(
        f"https://api.stability.ai/v1/generation/{engine_id}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "text_prompts": [
                {
                    "text": prompt
                }
            ],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        },
    )

    if response.status_code != 200:
        pass

    data = response.json()

    image_base64 = data["artifacts"][0]['base64']
    return image_base64
