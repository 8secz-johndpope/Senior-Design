from gyazo import Api

client = Api(access_token='114231de676f8b8a376f19964c55919273ff7f754ee280ee619d4b63a86f7a0d')

with open('data/0chain/Nikhaar_Shah_image.jpg', 'rb') as f:
    image = client.upload_image(f)
    print(image.to_json())
