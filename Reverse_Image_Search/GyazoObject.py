from gyazo import Api

class GyazoObj:
    def __init__(self):
        self.client = Api(client_id='e630e741a01b332603d9bd9af5b6134e3b9472e074f8d3126ca1f27011923c9f', client_secret='1c6144875fd0984655b73d99a2ea4f0c26e118d7dedfb8bad9e3e8818bae7dd1', access_token='f72318033aa3099374b0898b0dfd88e42caa11c35e12c26367bff66dae82415e')

    def upload(self, img_file):
        image = ''
        with open(img_file, 'rb') as f:
            image = self.client.upload_image(f)
        return image

    def list_img(self):
        images = self.client.get_image_list()
        for image in images:
            print(str(image))

    def delete_all(self):
        images = self.client.get_image_list()
        for image in images:
            try:
                self.client.delete_image(image.image_id)
            except KeyError:
                pass

