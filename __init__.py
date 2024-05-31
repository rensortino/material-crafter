bl_info = {
    "name": "MatForger",
    "author": "Renato Sortino, Giuseppe Vecchio",
    "version": (1, 0, 0),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > MatForger",
    "description": "Add on for generating texture maps using diffusion models.",
    "support": "COMMUNITY",
    "warning": "Requires installation of dependencies and works best with a GPU",
    "category": "Development",
}

MF_version = bl_info["version"]
LAST_UPDATED = "May 31st 2024"

#TODO Refactor

def set_dependencies_installed(are_installed):
    global dependencies_installed
    dependencies_installed = are_installed
    
# Blender modules:
import bpy

# Python modules:
from pathlib import Path
import sys
import os
import tempfile
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
class MF_PGT_Input_Properties_Pre(bpy.types.PropertyGroup):
    # Install Dependencies panel:
    mf_path: bpy.props.StringProperty(
        name="MatForger Path",
        description="The save path for the virtual environments. If you have already "
        "installed MatForger, or you are using a different version of Blender, you can use your"
        " old Environment Path. Regardless of the method, always initiate your Environment.",
        default=f"{pm.named_paths['matforger'].parent}",
        maxlen=1024,
        subtype="DIR_PATH",
    )

    agree_to_license: bpy.props.BoolProperty(
        name="I agree",
        default=False,
        description="I agree to the MatForger License and the Hugging Face Stable Diffusion License.",
    )


# # ======== Pre-Dependency Operators ======== #
class MFPRE_OT_install_dependencies(bpy.types.Operator):
    bl_idname = "mf.install_dependencies"
    bl_label = "Install dependencies"
    bl_description = (
        "Downloads and installs the required python packages for this add-on. "
        "Internet connection is required. Blender may have to be started with "
        "elevated permissions in order to install the package."
    )
    bl_options = {"REGISTER", "INTERNAL"}
    
    @classmethod
    def poll(cls, context):
        if not bpy.context.scene.input_tool_pre.agree_to_license:
            cls.poll_message_set("Please accept the license before installing")
        return bpy.context.scene.input_tool_pre.agree_to_license

    def execute(self, context):

        matforger_path = (
            Path(bpy.context.scene.input_tool_pre.mf_path) / "MatForger-Add-on"
        )
        
        venv_path = matforger_path / "venv"
        model_id = helpers.model_id

        # Install pip:
        helpers.install_pip()
        self.report({"INFO"}, "PIP installed.")

        # Install Venv:
        if not venv_path.exists():
            subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

        # Importing dependencies
        try:
            pm.update_named_paths(matforger_path, "matforger")
            pm.update_named_paths(venv_path, "venv")
            helpers.install_modules(venv_path=venv_path)

            self.report({"INFO"}, "Python modules installed successfully.")
            
            pm.save_named_paths()
            
        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        # self.report({"INFO"}, "Dependencies installed successfully")

        # try:
        #     from diffusers import StableDiffusionPipeline
        #     import torch

        #     self.report({"INFO"}, "Retrieving model from local cache or hub")
        #     StableDiffusionPipeline.from_pretrained(
        #         model_id, torch_dtype=torch.float16, trust_remote_code=True
        #     )
        #     self.report({"INFO"}, "Stable Diffusion successfully installed.")
        #     pass

        # except Exception as err:
        #     self.report({"ERROR"}, str(err))
        #     return {"CANCELLED"}


        set_dependencies_installed(True)
        
        for mf_cls in classes:
            if not mf_cls.is_registered:
                bpy.utils.register_class(mf_cls)

        bpy.types.Scene.input_tool = bpy.props.PointerProperty(
            type=MF_PGT_Input_Properties
        )

        return {"FINISHED"}


# ======== Pre-Dependency UI Panels ======== #
class MFPRE_PT_warning_panel(bpy.types.Panel):
    bl_label = "MatForger Warning"
    bl_category = "MatForger"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        matforger_path = (
            Path(bpy.context.scene.input_tool_pre.mf_path) / "MatForger-Add-on"
        )
        return not matforger_path.exists()

    def draw(self, context):
        layout = self.layout

        lines = [
            f"Please install the missing dependencies for the \"{bl_info.get('name')}\" add-on.",
            f"1. Open Edit > Preferences > Add-ons.",
            f"2. Search for the \"{bl_info.get('name')}\" add-on.",
            f'3. Under "Preferences" click on the "{MFPRE_OT_install_dependencies.bl_label}"',
            f"   button. This will download and install the missing Python packages,",
            f"   if Blender has the required permissions. If you are experiencing issues,",
            f"   re-open Blender with Administrator privileges.",
        ]

        for line in lines:
            layout.label(text=line)

class MF_PT_model_warning_panel(bpy.types.Panel):
    bl_label = "MatForger Model Warning"
    bl_category = "MatForger"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        if pm.named_paths['model']
        matforger_path = (
            Path(bpy.context.scene.input_tool_pre.mf_path) / "MatForger-Add-on"
        )
        return not matforger_path.exists()

    def draw(self, context):
        layout = self.layout

        lines = [
            f"Please install the missing dependencies for the \"{bl_info.get('name')}\" add-on.",
            f"1. Open Edit > Preferences > Add-ons.",
            f"2. Search for the \"{bl_info.get('name')}\" add-on.",
            f'3. Under "Preferences" click on the "{MFPRE_OT_install_dependencies.bl_label}"',
            f"   button. This will download and install the missing Python packages,",
            f"   if Blender has the required permissions. If you are experiencing issues,",
            f"   re-open Blender with Administrator privileges.",
        ]

        for line in lines:
            layout.label(text=line)


class MFPRE_preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        input_tool_pre = scene.input_tool_pre

        row = layout.row()
        row.prop(input_tool_pre, "mf_path")

        # Hugging Face and MatForger License agreement:

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
            "wm.url_open", text="MatForger License (OpenRAIL)", icon="HELP"
        ).url = "https://huggingface.co/blog/open_rail"

        row_agree_to_license = layout.row()
        row_agree_to_license.alignment = "CENTER"
        row_agree_to_license.prop(input_tool_pre, "agree_to_license")

        # layout.separator()

        row_install_dependencies_button = layout.row()
        row_install_dependencies_button.operator(
            MFPRE_OT_install_dependencies.bl_idname, icon="CONSOLE"
        )

        if dependencies_installed and bpy.context.scene.input_tool_pre.agree_to_license:
            row_agree_to_license.enabled = False
            row_dependencies_installed = layout.row()
            row_dependencies_installed.alignment = "CENTER"
            row_dependencies_installed.label(text="Dependencies already installed", icon="ERROR")
            


pre_dependency_classes = (
    # Property Group Classes:
    MF_PGT_Input_Properties_Pre,
    # Operator Classes:
    MFPRE_OT_install_dependencies,
    # Panel Classes
    MFPRE_preferences,
    MFPRE_PT_warning_panel,
)


# ======== User input Property Group ======== #
class MF_PGT_Input_Properties(bpy.types.PropertyGroup):

    dir_name: bpy.props.StringProperty(
        name="Dir Name", description="Name of the generated texture"
    )

    prompt: bpy.props.StringProperty(
        name="Prompt", description="Text prompt to generate the texture"
    )

    save_path: bpy.props.StringProperty(
        name="Save Path",
        description="Save path",
        default=f"/tmp\\",
        maxlen=1024,
        subtype="DIR_PATH",
    )

    device: bpy.props.EnumProperty(
        name="Device Type",
        description="Select render device for Stable Diffusion.",
        items=[
            ("cuda", "Cuda (GPU)", "Render with Cuda (GPU)"),
            ("cpu", "CPU", "Render with CPU"),
        ],
    )

    fp16: bpy.props.BoolProperty(
        name="Half Precision (FP16)",
        default=True,
        description="Choose whether to run the model with half precision to use less memory.",
    )

    guidance_scale: bpy.props.FloatProperty(
        name="Guidance Scale",
        default=6.0,
        step=0.1,
        max=20.0,
        min=0.0,
        description="Classifier-free Guidance scale factor.",
    )

    height: bpy.props.IntProperty(
        name="Height",
        default=512,
        step=32,
        min=128,
        max=4096,
        description="Height of the generated textures (higher sizes consume more memory).",
    )
    
    width: bpy.props.IntProperty(
        name="Width",
        default=512,
        step=32,
        min=128,
        max=4096,
        description="Width of the generated textures (higher sizes consume more memory).",
    )

    num_steps: bpy.props.IntProperty(
        name="Steps",
        default=25,
        step=5,
        min=0,
        max=1000,
        description="Number of diffusion sampling steps.",
    )


# ======== Operators ======== #
class CreateTextures(bpy.types.Operator):
    bl_idname = "mf.create_textures"
    bl_label = "Create Textures"
    bl_description = "Creates textures with Stable Diffusion by using the Texture Description as text input."
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
    
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
        model_id = helpers.model_id
        venv_path = pm.named_paths['venv']

        user_input = {
            "name": bpy.context.scene.input_tool.dir_name,
            "prompt": bpy.context.scene.input_tool.prompt,
            "save_path": Path(bpy.path.abspath(bpy.context.scene.input_tool.save_path)),
            "model_path": model_id,
            "fp16": bpy.context.scene.input_tool.fp16,
            "device": bpy.context.scene.input_tool.device,
        }
        
        sd_kwargs = {
            "guidance_scale": bpy.context.scene.input_tool.guidance_scale,
            "height": bpy.context.scene.input_tool.height,
            "width": bpy.context.scene.input_tool.width,
            "num_inference_steps": bpy.context.scene.input_tool.num_steps,
            #TODO Add scheduler selection 
        }
 
        if not user_input["save_path"]:
            user_input["save_path"] = tempfile.gettempdir()
        if user_input["save_path"] == "/tmp\\":
            user_input["save_path"] = tempfile.gettempdir()
        
        try:
            helpers.execution_handler(venv_path, "text2img", {**user_input, **sd_kwargs})
            load_texture_maps(Path(user_input['save_path']), user_input['name'])
            self.report({"INFO"}, f"New Material Created!")
        except subprocess.CalledProcessError as e:
            print(e)
            self.report({"ERROR"}, "Running text2img raised an exception:\n {e}")
            return {"CANCELLED"}
        return {"FINISHED"}


# ======== UI Panels ======== #
class MF_PT_Main(bpy.types.Panel):
    bl_label = "MatForger"
    bl_idname = "MF_PT_Main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MatForger"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        input_tool = scene.input_tool

        """
        The Main panel for MatForger.
        """

        row = layout.row()
        row.prop(input_tool, "prompt")

        row = layout.row()
        
        row = layout.row()
        row.prop(input_tool, "fp16")

        row = layout.row()
        row.prop(input_tool, "device")

        layout.separator()

        row = layout.row()
        row.prop(input_tool, "save_path")
        
        row = layout.row()
        row.prop(input_tool, "dir_name")

        layout.separator()
        
        layout.operator(
            "mf.create_textures", icon="DISCLOSURE_TRI_RIGHT", text="Create Textures"
        )
        
        header, body = layout.panel("Diffusion Parameters", default_closed=False)
        
        row = header.row()
        row.label(text="Diffusion Parameters")
        
        row = body.row()
        row.prop(input_tool, "guidance_scale")
        
        row = body.row()
        row.prop(input_tool, "height")

        row = body.row()
        row.prop(input_tool, "width")

        row = body.row()
        row.prop(input_tool, "num_steps")
        


class MF_PT_Help(bpy.types.Panel):
    bl_label = "Help"
    bl_idname = "MF_PT_Help"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MatForger"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        input_tool = scene.input_tool

        row = layout.row()
        row.label(text=f"Looking for help?")

        row = layout.row()

        row = layout.row()
        layout.label(text=f"{MF_version}, {LAST_UPDATED}")


# ======== Blender add-on register/unregister handling ======== #
classes = (
    # Property Group Classes:
    MF_PGT_Input_Properties,
    # Operator Classes:
    CreateTextures,
    # Panel Classes:
    MF_PT_Main,
    MF_PT_Help,
)


def register():

    global dependencies_installed
    dependencies_installed = False
    
    for cls in pre_dependency_classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.input_tool_pre = bpy.props.PointerProperty(
        type=MF_PGT_Input_Properties_Pre
    )
    
    
    if not helpers.dependencies_installed():
        set_dependencies_installed(False)
        return

    if pm.paths_file_exists():
        pm.load_paths_file()        
        set_dependencies_installed(True)
        venv_path = pm.named_paths["venv"]
        

        for cls in classes:
            bpy.utils.register_class(cls)

        bpy.types.Scene.input_tool = bpy.props.PointerProperty(
            type=MF_PGT_Input_Properties
        )

        helpers.import_modules(venv_path)
        return


def unregister():
    for cls in pre_dependency_classes:
        bpy.utils.unregister_class(cls)

    if dependencies_installed:
        for cls in reversed(classes):
            bpy.utils.unregister_class(cls)
        del bpy.types.Scene.input_tool

    del bpy.types.Scene.input_tool_pre