bl_info = {
    "name": "Material Crafter",
    "author": "Renato Sortino, Giuseppe Vecchio",
    "version": (1, 0, 0),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > Material Crafter",
    "description": "Add on for generating texture maps using diffusion models.",
    "support": "COMMUNITY",
    "warning": "Requires installation of dependencies and works best with a GPU",
    "category": "Development",
}



MC_version = bl_info["version"]
LAST_UPDATED = "Jun 13rd 2024"

global installing
installing = False

#TODO Refactor

def progress_bar(self, context):
    row = self.layout.row()
    row.progress(
        factor=context.window_manager.progress,
        type="BAR",
        text=context.window_manager.progress_text #if context.window_manager.progress < 1 else "Installation Finished !"
    )
    row.scale_x = 2

def set_dependencies_installed(are_installed):
    global dependencies_installed
    dependencies_installed = are_installed
    
# Blender modules:
import bpy

# Python modules:
from pathlib import Path
import sys
import importlib
import subprocess

# Local modules:
sys.path.append(Path(__file__).parent)

from .src import helpers
from .src.textures import load_texture_maps

# Refresh Locals for development:
if "bpy" in locals():
    modules = {
        "helpers": helpers,
    }

    for i in modules:
        if i in locals():
            importlib.reload(modules[i])

pm = helpers.PathManager()

# ======== Pre Dependency =================== #
class MC_PGT_Input_Properties_Pre(bpy.types.PropertyGroup):
    # Install Dependencies panel:
    mc_path: bpy.props.StringProperty(
        name="Material Crafter Path",
        description="The save path for the virtual environments. If you have already "
        "installed Material Crafter, or you are using a different version of Blender, you can use your"
        " old Environment Path. Regardless of the method, always initiate your Environment.",
        default=f"{pm.named_paths['material_crafter'].parent}",
        maxlen=1024,
        subtype="DIR_PATH",
    )

    agree_to_license: bpy.props.BoolProperty(
        name="I agree",
        default=False,
        description="I agree to the Material Crafter License and the Hugging Face Stable Diffusion License.",
    )


# # ======== Pre-Dependency Operators ======== #
class MCPRE_OT_install_dependencies(bpy.types.Operator):
    bl_idname = "mc.install_dependencies"
    bl_label = "Install dependencies"
    bl_description = (
        "Downloads and installs the required python packages for this add-on. "
        "Internet connection is required. Blender may have to be started with "
        "elevated permissions in order to install the package."
    )
    bl_options = {"REGISTER", "INTERNAL"}
    
    def invoke(self, context, event):
        msg = "This will install python packages. It will take several minutes, depending on your connection speed."
        if dependencies_installed:
            msg = "Dependencies are already installed. Are you sure you want to reinstall all packages?"
        return context.window_manager.invoke_confirm(self, event, message=msg)
        
    @classmethod
    def poll(cls, context):
        if not bpy.context.scene.input_tool_pre.agree_to_license:
            cls.poll_message_set("Please accept the license before installing")
        return bpy.context.scene.input_tool_pre.agree_to_license

    def execute(self, context):
        
        global installing
        installing = True
        
        mc_path = (
            Path(bpy.context.scene.input_tool_pre.mc_path) / "Material-Crafter-Add-on"
        )
        
        venv_path = mc_path / "venv"

        # Install pip:
        helpers.install_pip()
        self.report({"INFO"}, "PIP installed.")

        # Install Venv:
        if not venv_path.exists():
            subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

        # Importing dependencies
        try:
            pm.update_named_paths(mc_path, "material_crafter")
            pm.update_named_paths(venv_path, "venv")
            helpers.install_modules(venv_path=venv_path, context=context)

            self.report({"INFO"}, "Python modules installed successfully.")
            
            pm.save_named_paths()
            
        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        set_dependencies_installed(True)
        
        for mc_cls in classes:
            if not mc_cls.is_registered:
                bpy.utils.register_class(mc_cls)

        bpy.types.Scene.input_tool = bpy.props.PointerProperty(
            type=MC_PGT_Input_Properties
        )
        
        installing = False

        return {"FINISHED"}


# ======== Pre-Dependency UI Panels ======== #
class MCPRE_PT_warning_panel(bpy.types.Panel):
    bl_label = "Material Crafter Warning"
    bl_category = "Material Crafter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        mc_path = (
            Path(bpy.context.scene.input_tool_pre.mc_path) / "Material-Crafter-Add-on"
        )
        return not mc_path.exists()

    def draw(self, context):
        layout = self.layout

        lines = [
            f"Please install the missing dependencies for the \"{bl_info.get('name')}\" add-on.",
            f"1. Open Edit > Preferences > Add-ons.",
            f"2. Search for the \"{bl_info.get('name')}\" add-on.",
            f'3. Under "Preferences" click on the "{MCPRE_OT_install_dependencies.bl_label}"',
            f"   button. This will download and install the missing Python packages,",
            f"   if Blender has the required permissions. If you are experiencing issues,",
            f"   re-open Blender with Administrator privileges.",
        ]

        for line in lines:
            layout.label(text=line)


class MCPRE_preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        input_tool_pre = scene.input_tool_pre

        row = layout.row()
        row.prop(input_tool_pre, "mc_path")

        # Hugging Face and Material Crafter License agreement:

        # This line represents the character space readable in Blender's UI system:
        #         |=======================================================================|
        lines = [
            f"Please read the two following License Agreements. You must accept the terms ",
            f"of the License Agreement before continuing with the installation.",
        ]

        for line in lines:
            layout.alignment = "CENTER"
            layout.label(text=line)

        row = layout.row()
        row.operator(
            "wm.url_open", text="Stable Diffusion License", icon="HELP"
        ).url = "https://huggingface.co/spaces/CompVis/stable-diffusion-license"

        row = layout.row()
        row.operator(
            "wm.url_open", text="Material Crafter License (OpenRAIL)", icon="HELP"
        ).url = "https://huggingface.co/blog/open_rail"

        row_agree_to_license = layout.row()
        row_agree_to_license.alignment = "CENTER"
        row_agree_to_license.prop(input_tool_pre, "agree_to_license")

        row_install_dependencies_button = layout.row()
        row_install_dependencies_button.operator(
            MCPRE_OT_install_dependencies.bl_idname, icon="CONSOLE"
        )
        
        if installing:
            progress_bar(self, context)
        
        if dependencies_installed and bpy.context.scene.input_tool_pre.agree_to_license:
            row_agree_to_license.enabled = False
            row_dependencies_installed = layout.row()
            row_dependencies_installed.alignment = "CENTER"
            row_dependencies_installed.label(text="Dependencies already installed", icon="ERROR")
            


pre_dependency_classes = (
    # Property Group Classes:
    MC_PGT_Input_Properties_Pre,
    # Operator Classes:
    MCPRE_OT_install_dependencies,
    # Panel Classes
    MCPRE_preferences,
    MCPRE_PT_warning_panel,
)


# ======== User input Property Group ======== #
class MC_PGT_Input_Properties(bpy.types.PropertyGroup):

    dir_name: bpy.props.StringProperty(
        name="Name", description="Name of the generated texture"
    )

    prompt: bpy.props.StringProperty(
        name="Prompt", description="Text prompt to generate the texture"
    )
    
    image_prompt: bpy.props.StringProperty(
        name="Image Prompt", description="Image prompt to generate the texture",
        subtype="FILE_PATH",
    )
    
    prompt_type: bpy.props.EnumProperty(
        name="Prompt Type", description="Either prompt text or image for generation",
        default="text",
        items=[
            ("text", "Text", "Text input"),
            ("image", "Image", "Image input"),
        ]
    )

    save_path: bpy.props.StringProperty(
        name="Save Path",
        description="Save path",
        default=pm.named_paths['texture_output'].as_posix(),
        maxlen=1024,
        subtype="DIR_PATH",
    )

    model_id: bpy.props.EnumProperty(
        name="Model ID",
        description="Select main model for generation",
        items=[
            ("gvecchio/MatForger", "gvecchio/MatForger", "MatForger"),
        ],
    )

    device: bpy.props.EnumProperty(
        name="Device Type",
        description="Select render device for Stable Diffusion",
        items=[
            ("cuda", "Cuda (GPU)", "Render with Cuda (GPU)"),
            ("cpu", "CPU", "Render with CPU"),
        ],
    )

    precision: bpy.props.EnumProperty(
        name="Precision",
        description="Floating Point Precision. This affects memory usage",
        default="fp16",
        items=[
            ("fp32", "FP32 (Full)", "Full Precision"),
            ("fp16", "FP16 (Half)", "Half Precision"),
        ],
    )

    scheduler: bpy.props.EnumProperty(
        name="Scheduler",
        default="ddim",
        description="Diffusion Scheduler.",
        items=[
            ("ddim", "DDIM", "DDIM Scheduler"),
            ("euler", "Euler Discrete", "Euler Discrete"),
        ],
    )
    
    guidance_scale: bpy.props.FloatProperty(
        name="Guidance Scale",
        default=6.0,
        step=0.1,
        max=20.0,
        min=0.0,
        description="Classifier-free Guidance scale factor",
    )
    
    tileable: bpy.props.BoolProperty(
        name="Tileable",
        default=True,
        description="Generate a tileable material",
    )
    
    patched: bpy.props.BoolProperty(
        name="Patched",
        default=True,
        description="Enables patched diffusion. Reduces memory consumption when working with high resolutions but can affect quality",
    )
    
    free_u: bpy.props.BoolProperty(
        name="Free U",
        default=False,
        description="Enables FreeU in diffusers. This may impair the image quality and the map consistency",
    )

    height: bpy.props.IntProperty(
        name="Height",
        default=512,
        step=32,
        min=128,
        max=4096,
        description="Height of the generated textures (higher sizes consume more memory)",
    )
    
    width: bpy.props.IntProperty(
        name="Width",
        default=512,
        step=32,
        min=128,
        max=4096,
        description="Width of the generated textures (higher sizes consume more memory)",
    )

    num_steps: bpy.props.IntProperty(
        name="Steps",
        default=50,
        step=5,
        min=0,
        max=1000,
        description="Number of diffusion sampling steps",
    )


# ======== Operators ======== #
class CreateTextures(bpy.types.Operator):
    bl_idname = "mc.create_textures"
    bl_label = "Create Textures"
    bl_description = "Creates textures with Stable Diffusion by using the Texture Description as text input."
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event, message="This operation may require several minutes. Make sure to open the Window console before running to keep track of the progress.")
    
    @classmethod
    def poll(cls, context):
        r'''
        Allows material creation only if an element accepting materials is selected
        '''
        has_materials = hasattr(bpy.context.active_object.data, "materials")
        if not has_materials:
            cls.poll_message_set("Please select an object that supports materials")
        return has_materials

    def execute(self, context):
        venv_path = pm.named_paths['venv']
        
        if bpy.context.scene.input_tool.prompt_type == "text":
            prompt = bpy.context.scene.input_tool.prompt
        elif bpy.context.scene.input_tool.prompt_type == "image":
            prompt = bpy.context.scene.input_tool.image_prompt
            assert Path(prompt).exists(), f"Image prompt path not found at {prompt}"
            

        user_input = {
            "name": bpy.context.scene.input_tool.dir_name,
            "prompt": prompt,
            "prompt_type": bpy.context.scene.input_tool.prompt_type,
            "save_path": Path(bpy.path.abspath(bpy.context.scene.input_tool.save_path)),
            "model_path": bpy.context.scene.input_tool.model_id,
            "precision": bpy.context.scene.input_tool.precision,
            "device": bpy.context.scene.input_tool.device,
        }
        
        sd_kwargs = {
            "guidance_scale": bpy.context.scene.input_tool.guidance_scale,
            "height": bpy.context.scene.input_tool.height,
            "width": bpy.context.scene.input_tool.width,
            "num_inference_steps": bpy.context.scene.input_tool.num_steps,
            "scheduler": bpy.context.scene.input_tool.scheduler,
            "tileable": bpy.context.scene.input_tool.tileable,
            "patched": bpy.context.scene.input_tool.patched,
            "free_u": bpy.context.scene.input_tool.free_u,
        }
 
        try:
            helpers.execution_handler(venv_path, "generate", {**user_input, **sd_kwargs})
            load_texture_maps(Path(user_input['save_path']), user_input['name'])
            pm.update_named_paths(user_input["save_path"], "texture_output")
            self.report({"INFO"}, f"New Material Created!")
            
        except subprocess.CalledProcessError as e:
            print(e)
            self.report({"ERROR"}, "Running text2img raised an exception:\n {e}")
            return {"CANCELLED"}
        return {"FINISHED"}


# ======== UI Panels ======== #
class MC_PT_Main(bpy.types.Panel):
    bl_label = "Material Crafter"
    bl_idname = "MC_PT_Main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Material Crafter"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        input_tool = scene.input_tool

        """
        The Main panel for Material Crafter.
        """

        row = layout.row()
        row.prop(input_tool, "prompt_type")
        
        if input_tool.prompt_type == "text":
            row = layout.row()
            row.prop(input_tool, "prompt")
        elif input_tool.prompt_type == "image":
            row = layout.row()
            row.prop(input_tool, "image_prompt")

        row = layout.row()
        
        row = layout.row()
        row.prop(input_tool, "model_id")
        
        row = layout.row()
        row.prop(input_tool, "precision")

        row = layout.row()
        row.prop(input_tool, "device")

        layout.separator()

        row = layout.row()
        row.prop(input_tool, "save_path")
        
        row = layout.row()
        row.prop(input_tool, "dir_name")
        
        row = layout.row()
        row.prop(input_tool, "tileable")

        layout.separator()
        
        layout.operator(
            "mc.create_textures", icon="DISCLOSURE_TRI_RIGHT", text="Create Textures"
        )
        
        header, body = layout.panel("Diffusion Parameters", default_closed=False)
        
        row = header.row()
        row.label(text="Diffusion Parameters")
        
        row = body.row()
        row.prop(input_tool, "scheduler")
        
        row = body.row()
        row.prop(input_tool, "guidance_scale")
        
        row = body.row()
        row.prop(input_tool, "height")

        row = body.row()
        row.prop(input_tool, "width")

        row = body.row()
        row.prop(input_tool, "num_steps")
        
        row = body.row()
        row.prop(input_tool, "patched")
        
        row = body.row()
        row.prop(input_tool, "free_u")
    
class MC_PT_Model_Warning(bpy.types.Panel):
    bl_label = "Material Crafter Warning"
    bl_category = "Material Crafter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        model_dir_name = f"models--{bpy.context.scene.input_tool.model_id.replace('/', '--')}"
        model_dir = pm.named_paths['model'] / "hub" / model_dir_name
        return not model_dir.exists()

    def draw(self, context):
        layout = self.layout
        model_dir_name = pm.named_models['model'] / "hub" / f"models--{bpy.context.scene.input_tool.model_id.replace('/', '--')}"

        lines = [
            f"Weights for {bpy.context.scene.input_tool.model_id} model not found in cache at {model_dir_name}",
            f"The weights will be donwloaded from Huggingface hub, which may take several minutes, depending on your connection speed."
        ]

        for line in lines:
            layout.label(text=line)

class MC_PT_Help(bpy.types.Panel):
    bl_label = "Help"
    bl_idname = "MC_PT_Help"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Material Crafter"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        input_tool = scene.input_tool

        row = layout.row()
        row.label(text=f"Looking for help?")

        row = layout.row()

        row = layout.row()
        layout.label(text=f"{MC_version}, {LAST_UPDATED}")


# ======== Blender add-on register/unregister handling ======== #
classes = (
    # Property Group Classes:
    MC_PGT_Input_Properties,
    # Operator Classes:
    CreateTextures,
    # Panel Classes:
    MC_PT_Model_Warning,
    MC_PT_Main,
    MC_PT_Help,
)


def register():

    global dependencies_installed
    dependencies_installed = False
    
    # Setup progress variables
    bpy.types.WindowManager.progress = bpy.props.FloatProperty()
    bpy.types.WindowManager.progress_text = bpy.props.StringProperty()
    
    for cls in pre_dependency_classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.input_tool_pre = bpy.props.PointerProperty(
        type=MC_PGT_Input_Properties_Pre
    )

    if pm.paths_file_exists():
        pm.load_paths_file()
        
    if pm.named_paths['venv'].exists():
        set_dependencies_installed(True)
        
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.input_tool = bpy.props.PointerProperty(
        type=MC_PGT_Input_Properties
    )
    return


def unregister():
    for cls in pre_dependency_classes:
        bpy.utils.unregister_class(cls)

    if dependencies_installed:
        for cls in reversed(classes):
            bpy.utils.unregister_class(cls)
        del bpy.types.Scene.input_tool

    del bpy.types.Scene.input_tool_pre