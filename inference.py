from pathlib import Path
import os
import argparse
from PIL import Image
import torch
from torchvision import transforms
from torchvision.transforms.functional import InterpolationMode

from models.blip import blip_decoder
import LLaMa 
import Vicuna

class Predictor():
    def __init__(self, weights='https://storage.googleapis.com/sfr-vision-language-research/BLIP/models/model_base_capfilt_large.pth', token="", model='llama'):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.model = blip_decoder(pretrained=weights,
                                  image_size=384, vit='base')
        # if model == 'llama':
        self.generator_llama = LLaMa.RecipeGenerator(token=token)
        # elif model == 'vicuna':
        self.generator_vicuna = Vicuna.RecipeGenerator()
        
    def predict_title(self, image):

        im = load_image(image, image_size=384, device=self.device)
        model = self.model
        model.eval()
        model = model.to(self.device)

        with torch.no_grad():
            caption = model.generate(im, sample=True, top_p=0.9, max_length=10, min_length=1)
            return caption[0]
        
    def generate_recipe(self, title):
        recipe_llama = self.generator_llama.generate(title)
        recipe_vicuna = self.generator_vicuna.generate(title)
        return recipe_llama, recipe_vicuna


def load_image(image, image_size, device):
    raw_image = Image.open(str(image)).convert('RGB')

    w,h = raw_image.size
    transform = transforms.Compose([
        transforms.Resize((image_size, image_size), interpolation=InterpolationMode.BICUBIC),
        transforms.ToTensor(),
        transforms.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))
    ])
    image = transform(raw_image).unsqueeze(0).to(device)
    return image

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='./demo.jpg', help='path to image for inference')
    parser.add_argument('--weights', default='./checkpoint_6.pth', help='path to weights for inference')
    parser.add_argument('--output_dir', default='./output')  
    parser.add_argument('--model', default='llama')  
    args = parser.parse_args()

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    predict = Predictor(weights=args.weights, model=args.model)
    title = predict.predict_title(args.input)
    recipe_llama, recipe_vicuna = predict.generate_recipe(title)
    print(title)
    result_path_l = os.path.join(args.output_dir, 'result_recipe_llama.txt')
    result_path_v = os.path.join(args.output_dir, 'result_recipe_vicuna.txt')

    with open(result_path_l, 'w') as f:
        f.write(recipe_llama)
    with open(result_path_v, 'w') as f:
        f.write(recipe_vicuna)