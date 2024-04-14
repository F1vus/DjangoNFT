import json

from web3 import Web3
from web3.middleware import geth_poa_middleware

from .models import UserProfile
from django.core.handlers.wsgi import HttpRequest
from django.shortcuts import render
from django.http import HttpResponse

import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()


def mintNft(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        private_key = os.environ.get('PRIVATE_KEY')
        infura_id = os.environ.get('WEB3_INFURA_PROJECT_ID')
        caller = os.environ.get('WALLET_ADRESS')

        imageBase64 = request.POST['base64']

        if not(imageBase64):
            return render(request, "NFTminter/index.html")

        imageBase64 = imageBase64.replace("data:image/png;base64,", "")

        nameNFT = request.COOKIES['nameNFT']

        user_profile = UserProfile.objects.filter(user=request.user).first()
        user_wallet_address = user_profile.eth_account_address

        web3 = Web3(Web3.HTTPProvider(f'https://sepolia.infura.io/v3/{infura_id}'))
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        with open('NFTminter/src/chain-info/contracts/GenNFT.json', 'r') as abi:
            contract_abi = json.load(abi)['abi']

        with open('NFTminter/src/chain-info/deployments/map.json', 'r') as abi:
            contract_address = json.load(abi)['GenNFT'][0]

        Chain_id = web3.eth.chain_id
        nonce = web3.eth.get_transaction_count(caller, 'pending')

        # Create a contract object
        contract = web3.eth.contract(address=contract_address, abi=contract_abi)

        token_uri = create_uri(imageBase64, nameNFT)

        call_func = contract.functions.safeMint(user_wallet_address, token_uri).build_transaction(
            {"chainId": Chain_id,
             "from": caller,
             "gas": 1000000,
             'nonce': nonce}
        )

        signed_tx = web3.eth.account.sign_transaction(call_func, private_key=private_key)
        send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        tx_receipt = web3.eth.wait_for_transaction_receipt(send_tx)
        tokenID = Web3.to_int(tx_receipt['logs'][0]['topics'][3][-64:])

        context = {'imageNft': 'data:image/png;base64,'+imageBase64,
                   'ethAdress': request.COOKIES['shortWalletVersion'],
                   'minted': True,
                   'contractAdress': contract_address,
                   'tokenID': tokenID
                   }
        return render(request, "NFTminter/index.html", context)
    return render(request, "NFTminter/index.html")


def create_uri(img: str, nameNFT: str) -> str:
    api_key = os.environ.get('STORAGE_API_KEY')

    result = create_ipfs_image(img)
    ipfsImage = 'https://'+result['value']['cid']+'.ipfs.nftstorage.link'

    url = "https://api.nft.storage/store"
    body = {
        "name": nameNFT,
        "description": "It's NFT from Fiv_ pet project",
        "image": ipfsImage
    }
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    meta_json = json.dumps(body)
    response = requests.post(url, headers=headers, files={'meta': (None, meta_json)})
    metaData = response.json()
    metaData = 'https://'+metaData['value']['ipnft']+'.ipfs.nftstorage.link/metadata.json'
    print(metaData)

    return metaData


def create_ipfs_image(img: str) -> dict:
    api_key = os.environ.get('STORAGE_API_KEY')

    url = "https://api.nft.storage/upload"
    body = {
        "accept": "application/json",
        "Content-Type": "image/*",
        "Authorization": f"Bearer {api_key}"
    }

    data = base64.b64decode(img)

    response = requests.post(url, headers=body, data=data)

    return response.json()
