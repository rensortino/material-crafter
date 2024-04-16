# from PIL import Image
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler
from torch import autocast
import torch


def progress(step, timestep, latents):
    print(step, timestep, latents[0][0][0][0])


def text2img(prompt: str,
            save_path: str,
            texture_format: str,
            model_path: str,
            device: str):
    # img = Image.open(img_path)
    pipe = StableDiffusionPipeline.from_pretrained(model_path, low_cpu_mem_usage=True)  # Specify model path
    pipe = pipe.to(device)  # Specify render device
    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)

    with autocast(device):
        with torch.inference_mode():
            image = pipe(prompt, num_inference_steps=2, callback=progress)["sample"][0]

    image.save(save_path)