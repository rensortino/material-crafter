# from PIL import Image
from diffusers import DiffusionPipeline, EulerDiscreteScheduler, DDIMScheduler
import fire
from pathlib import Path
import torch
from PIL import Image


class SDInterfaceCommands(object):
    def generate(self,
                name: str,
                prompt_type: str,
                prompt: str,
                save_path: Path,
                model_path: str,
                precision: str,
                device: str,
                **kwargs
                ):
        save_dir = Path(save_path) / name
        save_dir.mkdir(exist_ok=True, parents=True)
        
        if prompt_type == "text":
            prompt = prompt
        elif prompt_type == "image":
            assert Path(prompt).exists(), f"Image prompt path not found at {prompt}"
            prompt = Image.open(prompt).resize((512,512))

        if precision == "fp32":
            torch_dtype = torch.float32
        elif precision == "fp16":
            torch_dtype = torch.float16
        else:
            raise ValueError(f"Unrecognized precision value {precision}")

        pipe = DiffusionPipeline.from_pretrained(
            model_path,
            trust_remote_code=True,
            low_cpu_mem_usage=False, 
            device_map=None,
            torch_dtype=torch_dtype,
        )
        
        # Enable memory optimization
        pipe.enable_vae_tiling()
        pipe.enable_freeu(s1=0.9, s2=0.2, b1=1.1, b2=1.2)
        pipe.to(device)
        pipe.enable_xformers_memory_efficient_attention() 
        
        scheduler = kwargs.pop("scheduler", "ddim")
        if scheduler == "ddim":
            pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)
        elif scheduler == "euler":
            pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
        else:
            raise NotImplementedError(f"Scheduler {scheduler} not supported")
        
        with torch.inference_mode():
            image = pipe(
                prompt,
                **kwargs
            ).images[0]
            
        image.basecolor.save(save_dir / "basecolor.png")
        image.normal.save(save_dir / "normal.png")
        image.height.save(save_dir / "height.png")
        image.roughness.save(save_dir / "roughness.png")
        image.metallic.save(save_dir / "metallic.png")
    
if __name__ == '__main__':
    fire.Fire(SDInterfaceCommands)