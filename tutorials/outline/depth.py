import bpy
import math
import os
from pathlib import Path


def get_desktop_dir():
    """获取桌面目录，兼容 macOS/Windows；找不到桌面时回退到用户目录。"""
    if os.name == "nt":
        try:
            import winreg

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            value_names = ("Desktop", "{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}")
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                for value_name in value_names:
                    try:
                        value, _ = winreg.QueryValueEx(key, value_name)
                    except FileNotFoundError:
                        continue

                    desktop = Path(os.path.expandvars(value)).expanduser()
                    if desktop.exists():
                        return str(desktop)
        except OSError:
            pass

    desktop = Path.home() / "Desktop"
    if desktop.exists():
        return str(desktop)

    return str(Path.home())


# =========================
# 可调参数
# =========================

# 1. 执行开关
# True：运行脚本后立即渲染并写出启用的 PNG；False：只配置场景和合成节点。
RENDER_NOW = False

# 2. 输出开关
# 每项可以独立启用。描边、原材质和纯色填充固定使用透明背景 RGBA。
EXPORT_DEPTH = True
EXPORT_OUTLINE = True
EXPORT_MATERIAL = True
EXPORT_OBJECT_FILL = True

# 3. 输出位置和文件名前缀
OUTPUT_DIR = get_desktop_dir()
DEPTH_OUTPUT_NAME = "blender_depth"
OUTLINE_OUTPUT_NAME = "blender_outline"
MATERIAL_OUTPUT_NAME = "blender_material"
OBJECT_FILL_OUTPUT_NAME = "blender_object_fill"

# 脚本内部使用的输出视图层名称，通常无需修改。
MATERIAL_VIEW_LAYER_NAME = "StereogramOriginalMaterial"
OBJECT_FILL_VIEW_LAYER_NAME = "StereogramObjectFill"

# 4. 渲染分辨率
RESOLUTION_X = 1920
RESOLUTION_Y = 1080
RESOLUTION_PERCENTAGE = 100

# 5. 描边设置
# 描边图始终只包含线条；抗锯齿通过 Alpha 从描边色过渡到透明。
OUTLINE_COLOR = (0.0, 0.0, 0.0)  # Freestyle 边线颜色，RGB，范围 0.0 - 1.0。
OUTLINE_THICKNESS = 2.0
OUTLINE_THICKNESS_POSITION = "INSIDE"  # INSIDE：内描边，避免轮廓超出深度图覆盖范围。

# 6. 纯色填充设置
OBJECT_FILL_COLOR = (1.0, 1.0, 1.0, 1.0)  # RGBA；背景始终透明。

# 7. 环境和相机设置
# World 背景仍参与照明，但不会画进描边、原材质或纯色填充图。
WORLD_BACKGROUND_COLOR = (1.0, 1.0, 1.0, 1.0)

# 投影模式：
# ORTHO：正交投影；
# PERSP：普通透视；
# HALF_PERSP：0.5 透视，保持大致同样构图，但把镜头和相机距离同时放大，减弱透视变形。
PROJECTION_MODE = "HALF_PERSP"
ORTHO_SCALE = 3.0
CAMERA_DISTANCE = 4.0
PERSP_LENS = 45.0
HALF_PERSP_FACTOR = 0.5


def make_emission_material(name, color):
    """创建或更新一个发射材质，用于需要纯色填充时覆盖物体材质。"""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)

    if mat.node_tree is None:
        mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    emission_node = nodes.new(type="ShaderNodeEmission")
    emission_node.inputs["Color"].default_value = color

    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    mat.node_tree.links.new(emission_node.outputs["Emission"], output_node.inputs["Surface"])
    return mat


def sync_layer_collection_settings(source, target):
    """同步视图层集合的可见性设置，让原材质图与主视图层包含相同物体。"""
    for attribute in ("exclude", "holdout", "indirect_only", "hide_viewport"):
        if hasattr(source, attribute) and hasattr(target, attribute):
            setattr(target, attribute, getattr(source, attribute))

    target_children = {child.name: child for child in target.children}
    for source_child in source.children:
        target_child = target_children.get(source_child.name)
        if target_child is not None:
            sync_layer_collection_settings(source_child, target_child)


def configure_output_view_layer(
    scene,
    source_view_layer,
    view_layer_name,
    material_override,
):
    """配置一个同步主视图层可见性、不带 Freestyle 的输出视图层。"""
    view_layer = scene.view_layers.get(view_layer_name)
    if view_layer is None:
        view_layer = scene.view_layers.new(view_layer_name)

    if hasattr(view_layer, "use"):
        view_layer.use = True
    view_layer.material_override = material_override
    if hasattr(view_layer, "use_freestyle"):
        view_layer.use_freestyle = False

    sync_layer_collection_settings(
        source_view_layer.layer_collection,
        view_layer.layer_collection,
    )
    return view_layer


def configure_camera(camera):
    """根据 PROJECTION_MODE 配置正交、普通透视或 0.5 透视相机。"""
    if camera is None:
        raise RuntimeError("找不到场景中的 Camera")

    mode = PROJECTION_MODE.upper()
    camera.rotation_euler = (math.radians(90), 0.0, 0.0)
    camera.data.clip_start = 0.1
    camera.data.clip_end = 100.0

    if mode == "ORTHO":
        camera.location = (0.0, -CAMERA_DISTANCE, 0.0)
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = ORTHO_SCALE
    elif mode == "PERSP":
        camera.location = (0.0, -CAMERA_DISTANCE, 0.0)
        camera.data.type = "PERSP"
        camera.data.lens = PERSP_LENS
    elif mode in {"HALF_PERSP", "PERSP_0_5", "0.5_PERSP"}:
        if HALF_PERSP_FACTOR <= 0.0:
            raise ValueError("HALF_PERSP_FACTOR 必须大于 0")

        # Blender 没有真正的“半透视”相机类型。
        # 这里把焦距和相机距离按同一倍率放大：画面大小基本不变，但透视感约减半。
        camera.location = (0.0, -CAMERA_DISTANCE / HALF_PERSP_FACTOR, 0.0)
        camera.data.type = "PERSP"
        camera.data.lens = PERSP_LENS / HALF_PERSP_FACTOR
    else:
        raise ValueError("PROJECTION_MODE 只能是 ORTHO、PERSP 或 HALF_PERSP")


def configure_freestyle(scene, view_layer):
    """启用 Freestyle，并设置为内描边和自定义颜色。"""
    scene.render.use_freestyle = True

    if hasattr(view_layer, "use_freestyle"):
        view_layer.use_freestyle = True

    freestyle_settings = view_layer.freestyle_settings
    if len(freestyle_settings.linesets) == 0:
        freestyle_settings.linesets.new("LineSet")

    line_set = freestyle_settings.linesets.get("LineSet") or freestyle_settings.linesets[0]
    line_style = line_set.linestyle
    line_style.thickness = OUTLINE_THICKNESS
    line_style.color = OUTLINE_COLOR

    if hasattr(line_style, "thickness_position"):
        line_style.thickness_position = OUTLINE_THICKNESS_POSITION
    else:
        print("当前 Blender 版本不支持 Freestyle 内/外描边位置设置，已保留默认居中描边。")


def disable_freestyle(scene, view_layer):
    """关闭不需要的 Freestyle，避免关闭描边输出后仍额外渲染线条。"""
    scene.render.use_freestyle = False
    if hasattr(view_layer, "use_freestyle"):
        view_layer.use_freestyle = False


def first_available_output(node, names):
    """按候选名称取 Render Layers 输出口，兼容不同 Blender 版本的 socket 名称。"""
    for name in names:
        socket = node.outputs.get(name)
        if socket is not None:
            return socket
    raise RuntimeError(f"Render Layers 节点找不到输出口：{names}")


def extract_outline_from_combined_image(tree, render_layers, image_socket):
    """从 Combined Image 提取线条 Alpha，并用纯色 RGB 避免白色边缘。"""
    rgb_to_bw = tree.nodes.new(type="CompositorNodeRGBToBW")
    invert = tree.nodes.new(type="CompositorNodeInvert")
    try:
        multiply_alpha = tree.nodes.new(type="CompositorNodeMath")
    except RuntimeError:
        # Blender 5.2 起合成器使用统一的 Shader Math 节点类型。
        multiply_alpha = tree.nodes.new(type="ShaderNodeMath")
    multiply_alpha.operation = "MULTIPLY"
    set_alpha = tree.nodes.new(type="CompositorNodeSetAlpha")

    tree.links.new(image_socket, rgb_to_bw.inputs["Image"])
    tree.links.new(rgb_to_bw.outputs["Val"], invert.inputs["Color"])
    tree.links.new(invert.outputs["Color"], multiply_alpha.inputs[0])
    tree.links.new(
        first_available_output(render_layers, ["Alpha"]),
        multiply_alpha.inputs[1],
    )
    # 不复用 Combined Image 的灰度抗锯齿 RGB；否则半透明边缘会带白色。
    # 输出像素始终使用描边色，只让 Alpha 从不透明平滑过渡到透明。
    set_alpha.inputs["Image"].default_value = (*OUTLINE_COLOR, 1.0)
    tree.links.new(multiply_alpha.outputs[0], set_alpha.inputs["Alpha"])
    return set_alpha.outputs["Image"]


def set_first_supported_enum(target, attribute, candidates):
    """依次设置候选枚举值，兼容 Blender/OCIO 配置间的命名差异。"""
    for value in candidates:
        try:
            setattr(target, attribute, value)
            return value
        except TypeError:
            continue

    raise RuntimeError(f"{attribute} 不支持任何候选值：{candidates}")


def get_compositor_tree(scene):
    """获取或创建合成节点树，兼容 Blender 4.x 及 5.x。"""
    if hasattr(scene, "compositing_node_group"):
        tree = scene.compositing_node_group
        if tree is None:
            tree = bpy.data.node_groups.new(
                name=f"{scene.name} Depth Compositor",
                type="CompositorNodeTree",
            )
            scene.compositing_node_group = tree
        return tree

    scene.use_nodes = True
    return scene.node_tree


def create_file_output(tree, output_name, color_mode):
    """创建文件输出节点，兼容 Blender 4.x 及 5.x 的路径和输入接口。"""
    node = tree.nodes.new(type="CompositorNodeOutputFile")

    if hasattr(node, "base_path"):
        node.base_path = OUTPUT_DIR
        node.file_slots[0].path = output_name
    else:
        node.directory = OUTPUT_DIR
        node.file_name = output_name
        node.file_output_items.clear()
        node.file_output_items.new("RGBA", "Image")

    if hasattr(node.format, "media_type"):
        node.format.media_type = "IMAGE"
    node.format.file_format = "PNG"
    node.format.color_depth = "16"
    node.format.color_mode = color_mode
    return node


# =========================
# 场景基础设置
# =========================

bpy.context.scene.render.resolution_x = RESOLUTION_X
bpy.context.scene.render.resolution_y = RESOLUTION_Y
bpy.context.scene.render.resolution_percentage = RESOLUTION_PERCENTAGE

# 设置颜色管理，避免深度图被视图变换改色。
# Blender/OCIO 版本不同，可用枚举名称也会不同，因此按语义相近的名称回退。
set_first_supported_enum(
    bpy.context.scene.display_settings,
    "display_device",
    ("sRGB", "Display P3", "Rec.1886"),
)
bpy.context.scene.view_settings.view_transform = "Standard"
set_first_supported_enum(
    bpy.context.scene.sequencer_colorspace_settings,
    "name",
    ("Non-Color", "Raw", "scene_linear"),
)

scene = bpy.context.scene
main_view_layer = scene.view_layers["ViewLayer"]

# World 仍参与照明；RGBA 输出启用时，背景固定输出为透明。
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = WORLD_BACKGROUND_COLOR

# 设置渲染引擎为 Cycles，以便使用节点和深度通道。
scene.render.engine = "CYCLES"
scene.render.film_transparent = (
    EXPORT_OUTLINE or EXPORT_MATERIAL or EXPORT_OBJECT_FILL
)

# 每次运行都先清除旧的主视图层材质覆盖，避免开关变化后残留上次配置。
main_view_layer.material_override = None
main_view_layer.use_pass_z = EXPORT_DEPTH
if EXPORT_OUTLINE:
    configure_freestyle(scene, main_view_layer)
else:
    disable_freestyle(scene, main_view_layer)

camera = bpy.data.objects.get("Camera")
configure_camera(camera)
scene.camera = camera


# =========================
# 合成节点：按输出开关创建
# =========================

tree = get_compositor_tree(scene)
tree.nodes.clear()
links = tree.links

# 深度图和描边图共用主视图层。
if EXPORT_DEPTH or EXPORT_OUTLINE:
    main_render_layers = tree.nodes.new(type="CompositorNodeRLayers")
    main_render_layers.location = (0, 0)

if EXPORT_DEPTH:
    # Depth -> Normalize -> Invert。
    normalize_node = tree.nodes.new(type="CompositorNodeNormalize")
    invert_depth_node = tree.nodes.new(type="CompositorNodeInvert")
    depth_viewer = tree.nodes.new(type="CompositorNodeViewer")
    depth_file_output = create_file_output(tree, DEPTH_OUTPUT_NAME, "BW")

    links.new(
        first_available_output(main_render_layers, ["Depth", "Z"]),
        normalize_node.inputs[0],
    )
    links.new(normalize_node.outputs[0], invert_depth_node.inputs["Color"])
    links.new(invert_depth_node.outputs[0], depth_viewer.inputs["Image"])
    links.new(invert_depth_node.outputs[0], depth_file_output.inputs[0])

    normalize_node.location = (250, -300)
    invert_depth_node.location = (450, -300)
    depth_viewer.location = (650, -400)
    depth_file_output.location = (650, -200)

if EXPORT_OUTLINE:
    # 优先使用独立 Freestyle pass；没有该输出口时，从 Combined Image 提取线条。
    outline_socket = main_render_layers.outputs.get("Freestyle")
    if outline_socket is None:
        print("Render Layers 没有 Freestyle 输出口，描边图将从 Image 通道提取。")
        outline_socket = first_available_output(main_render_layers, ["Image"])
        hidden_fill_mat = make_emission_material(
            "DepthHiddenFillMaterial",
            (1.0, 1.0, 1.0, 1.0),
        )
        main_view_layer.material_override = hidden_fill_mat
        outline_socket = extract_outline_from_combined_image(
            tree,
            main_render_layers,
            outline_socket,
        )

    outline_viewer = tree.nodes.new(type="CompositorNodeViewer")
    outline_file_output = create_file_output(tree, OUTLINE_OUTPUT_NAME, "RGBA")
    links.new(outline_socket, outline_viewer.inputs["Image"])
    links.new(outline_socket, outline_file_output.inputs[0])

    outline_viewer.location = (650, 100)
    outline_file_output.location = (650, 300)

# 原材质图始终使用独立视图层，避免 Freestyle 和白色材质覆盖混入结果。
material_view_layer = scene.view_layers.get(MATERIAL_VIEW_LAYER_NAME)
if EXPORT_MATERIAL:
    material_view_layer = configure_output_view_layer(
        scene,
        main_view_layer,
        MATERIAL_VIEW_LAYER_NAME,
        None,
    )
    material_render_layers = tree.nodes.new(type="CompositorNodeRLayers")
    material_render_layers.layer = material_view_layer.name
    material_file_output = create_file_output(tree, MATERIAL_OUTPUT_NAME, "RGBA")

    links.new(
        first_available_output(material_render_layers, ["Image"]),
        material_file_output.inputs[0],
    )

    material_render_layers.location = (0, 600)
    material_file_output.location = (250, 600)
elif material_view_layer is not None and hasattr(material_view_layer, "use"):
    # 关闭输出后也关闭脚本创建的视图层，避免它继续消耗渲染时间。
    material_view_layer.use = False

# 纯色填充图使用另一个独立视图层：固定 OBJECT_FILL_COLOR，无描边、透明背景。
object_fill_view_layer = scene.view_layers.get(OBJECT_FILL_VIEW_LAYER_NAME)
if EXPORT_OBJECT_FILL:
    object_fill_material = make_emission_material(
        "StereogramObjectFillMaterial",
        OBJECT_FILL_COLOR,
    )
    object_fill_view_layer = configure_output_view_layer(
        scene,
        main_view_layer,
        OBJECT_FILL_VIEW_LAYER_NAME,
        object_fill_material,
    )
    object_fill_render_layers = tree.nodes.new(type="CompositorNodeRLayers")
    object_fill_render_layers.layer = object_fill_view_layer.name
    object_fill_file_output = create_file_output(
        tree,
        OBJECT_FILL_OUTPUT_NAME,
        "RGBA",
    )

    links.new(
        first_available_output(object_fill_render_layers, ["Image"]),
        object_fill_file_output.inputs[0],
    )

    object_fill_render_layers.location = (0, 900)
    object_fill_file_output.location = (250, 900)
elif object_fill_view_layer is not None and hasattr(object_fill_view_layer, "use"):
    object_fill_view_layer.use = False

# 只渲染实际参与输出的视图层。
if hasattr(main_view_layer, "use"):
    main_view_layer.use = (
        EXPORT_DEPTH
        or EXPORT_OUTLINE
        or not (EXPORT_MATERIAL or EXPORT_OBJECT_FILL)
    )


# =========================
# 执行渲染
# =========================

if RENDER_NOW:
    # Compositor 节点只定义输出流程；真正写出 PNG 需要触发一次渲染。
    bpy.ops.render.render(write_still=True)
