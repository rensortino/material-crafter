# from PIL import Image
from diffusers import DiffusionPipeline, EulerDiscreteScheduler
import fire
from pathlib import Path
import torch


class SDInterfaceCommands(object):
    def text2img(self,
                name: str,
                prompt: str,
                save_path: Path,
                model_path: str,
                fp16: bool,
                device: str,
                **kwargs
                ):
        # img = Image.open(img_path)
        save_dir = Path(save_path) / name
        save_dir.mkdir(exist_ok=True, parents=True)
        pipe = DiffusionPipeline.from_pretrained(
            model_path,
            trust_remote_code=True,
            low_cpu_mem_usage=False, 
            device_map=None,
            torch_dtype=torch.float16 if fp16 else torch.float32,
        )
        
        # Enable memory optimization
        pipe.enable_vae_tiling()
        pipe.enable_freeu(s1=0.9, s2=0.2, b1=1.1, b2=1.2)
        pipe.to(device)
        pipe.enable_xformers_memory_efficient_attention() 
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)

        with torch.inference_mode():
            #TODO Parameterize all SD parameters
            image = pipe(
                prompt,
                **kwargs
                # guidance_scale=6.0,
                # height=256,
                # width=256,
                # num_inference_steps=25,
            ).images[0]
            
        image.basecolor.save(save_dir / "basecolor.png")
        image.normal.save(save_dir / "normal.png")
        image.height.save(save_dir / "height.png")
        image.roughness.save(save_dir / "roughness.png")
        image.metallic.save(save_dir / "metallic.png")
    
if __name__ == '__main__':
    fire.Fire(SDInterfaceCommands)