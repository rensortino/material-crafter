import bpy

def create_node(nodes, type, name, location=(0, 0), hide=True, width=150):
    new_node = nodes.new(type)
    new_node.name = name
    new_node.location = location
    new_node.hide = hide
    new_node.width = width
    return new_node


def load_map_image(node, img_path, name, colorspace="sRGB"):
    node.image = bpy.data.images.load(img_path)
    node.image.colorspace_settings.name = colorspace
    node.image.name = name


def load_texture_maps(mat_dir, mat_name):
    mat_dir = mat_dir / mat_name
    mat_name = f"M_MF_{mat_name}"
    material = bpy.data.materials.new(mat_name)

    # Set node tree editing
    material.use_nodes = True
    bpy.data.materials.new(mat_name)
    nodes = material.node_tree.nodes
    bsdf_node = nodes.get("Principled BSDF")
    output_node = nodes.get("Material Output")

    basecolor_image_path = (mat_dir / "basecolor.png").as_posix()
    normal_image_path = (mat_dir / "normal.png").as_posix()
    roughness_image_path = (mat_dir / "roughness.png").as_posix()
    height_image_path = (mat_dir / "height.png").as_posix()
    metallic_image_path = (mat_dir / "metallic.png").as_posix()

    # Create a new image texture node for the texture maps
    basecolor_map_node = create_node(
        nodes, "ShaderNodeTexImage", "DiffuseNode", location=(-200, 300), hide=True
    )
    metallic_map_node = create_node(
        nodes, "ShaderNodeTexImage", "MetallicNode", location=(-200, 250), hide=True
    )
    roughness_map_node = create_node(
        nodes, "ShaderNodeTexImage", "RoughnessNode", location=(-200, 200), hide=True
    )
    normal_map_node = create_node(
        nodes, "ShaderNodeTexImage", "NormalNode", location=(-250, 100), hide=True
    )
    normal_shader_node = create_node(
        nodes,
        "ShaderNodeNormalMap",
        "NormalShaderNode",
        location=(-200, 150),
        hide=True,
    )
    height_map_node = create_node(
        nodes, "ShaderNodeTexImage", "HeightNode", location=(300, 100), hide=True
    )
    displacement_shader_node = create_node(
        nodes,
        "ShaderNodeDisplacement",
        "DisplacementNode",
        location=(350, 150),
        hide=True,
    )

    # Load the texture images
    load_map_image(
        basecolor_map_node, basecolor_image_path, name="Base Color", colorspace="sRGB"
    )
    load_map_image(
        height_map_node, height_image_path, name="Height", colorspace="Non-Color"
    )
    load_map_image(
        metallic_map_node, metallic_image_path, name="Metallic", colorspace="Non-Color"
    )
    load_map_image(
        roughness_map_node,
        roughness_image_path,
        name="Roughness",
        colorspace="Non-Color",
    )
    load_map_image(
        normal_map_node, normal_image_path, name="Normal", colorspace="Non-Color"
    )

    # Connect the texture nodes to the Principled BSDF inputs
    material.node_tree.links.new(
        basecolor_map_node.outputs["Color"], bsdf_node.inputs["Base Color"]
    )
    material.node_tree.links.new(
        normal_map_node.outputs["Color"], normal_shader_node.inputs["Color"]
    )
    material.node_tree.links.new(
        normal_shader_node.outputs["Normal"], bsdf_node.inputs["Normal"]
    )
    material.node_tree.links.new(
        roughness_map_node.outputs["Color"], bsdf_node.inputs["Roughness"]
    )
    material.node_tree.links.new(
        height_map_node.outputs["Color"], displacement_shader_node.inputs["Height"]
    )
    material.node_tree.links.new(
        metallic_map_node.outputs["Color"], bsdf_node.inputs["Metallic"]
    )

    # Connect the output of the height node to the Material Output displacement node's input
    material.node_tree.links.new(
        displacement_shader_node.outputs["Displacement"],
        output_node.inputs["Displacement"],
    )

    # Add created material to the active object
    bpy.context.active_object.data.materials[0] = material
