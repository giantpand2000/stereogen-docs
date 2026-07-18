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

# 输出目录和文件名前缀。
OUTPUT_DIR = get_desktop_dir()
DEPTH_OUTPUT_NAME = "blender_depth"
OUTLINE_OUTPUT_NAME = "blender_outline"

# True：脚本最后直接渲染并写出 File Output 节点；False：只建立节点和设置场景。
RENDER_NOW = False

# 渲染分辨率。
RESOLUTION_X = 1920
RESOLUTION_Y = 1080
RESOLUTION_PERCENTAGE = 100

# 描边设置。
OUTLINE_ONLY = True  # True：只输出 Freestyle 边线，不输出物体填充。
OUTLINE_COLOR = (0.0, 0.0, 0.0)  # Freestyle 边线颜色，RGB，范围 0.0 - 1.0。
OUTLINE_THICKNESS = 2.0
OUTLINE_THICKNESS_POSITION = "INSIDE"  # INSIDE：内描边，避免轮廓超出深度图覆盖范围。

# 如果你需要“彩色填充+线”的普通渲染图，把 OUTLINE_ONLY 改成 False，
# 再打开 RENDER_OBJECT_FILL 并调整 OBJECT_FILL_COLOR。脚本会用视图层材质覆盖，
# 不会直接改掉物体自身的材质槽。
RENDER_OBJECT_FILL = False
OBJECT_FILL_COLOR = (1.0, 1.0, 1.0, 1.0)  # 物体填充色，RGBA，只有 RENDER_OBJECT_FILL=True 时使用。
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


def set_view_layer_material_override(mat):
    """用视图层材质覆盖渲染颜色，避免直接修改物体原材质。"""
    view_layer = bpy.context.scene.view_layers["ViewLayer"]
    view_layer.material_override = mat


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


def configure_freestyle():
    """启用 Freestyle，并设置为内描边和自定义颜色。"""
    bpy.context.scene.render.use_freestyle = True

    view_layer = bpy.context.scene.view_layers["ViewLayer"]
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


def first_available_output(node, names):
    """按候选名称取 Render Layers 输出口，兼容不同 Blender 版本的 socket 名称。"""
    for name in names:
        socket = node.outputs.get(name)
        if socket is not None:
            return socket
    raise RuntimeError(f"Render Layers 节点找不到输出口：{names}")


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

# 设置渲染背景色。
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = WORLD_BACKGROUND_COLOR

# 设置渲染引擎为 Cycles，以便使用节点和深度通道。
bpy.context.scene.render.engine = "CYCLES"
bpy.context.scene.render.film_transparent = OUTLINE_ONLY

configure_freestyle()

camera = bpy.data.objects.get("Camera")
configure_camera(camera)
bpy.context.scene.camera = camera


# =========================
# 合成节点：深度图和描边图
# =========================

tree = get_compositor_tree(bpy.context.scene)
tree.nodes.clear()

# 节点间距，仅用于把 Blender 节点排得更容易读。
spacing = 50

render_layers = tree.nodes.new(type="CompositorNodeRLayers")
bpy.context.scene.view_layers["ViewLayer"].use_pass_z = True

normalize_node = tree.nodes.new(type="CompositorNodeNormalize")
color_invert_node = tree.nodes.new(type="CompositorNodeInvert")

view_node = tree.nodes.new(type="CompositorNodeViewer")
view_node2 = tree.nodes.new(type="CompositorNodeViewer")

file_output = create_file_output(tree, DEPTH_OUTPUT_NAME, "BW")
file_output2 = create_file_output(
    tree,
    OUTLINE_OUTPUT_NAME,
    "RGBA" if OUTLINE_ONLY else "RGB",
)

links = tree.links

# 深度图：Depth -> Normalize -> Invert，保持原有“近处更亮/更暗”的方向。
links.new(first_available_output(render_layers, ["Depth", "Z"]), normalize_node.inputs[0])
links.new(normalize_node.outputs[0], color_invert_node.inputs["Color"])
links.new(color_invert_node.outputs[0], view_node.inputs["Image"])
links.new(color_invert_node.outputs[0], file_output.inputs[0])

# 描边图：
# OUTLINE_ONLY=True 时使用独立 Freestyle 通道，只输出边线和透明背景，不输出物体内容。
# 如果当前 Blender 没有 Freestyle socket，则退回 Image 通道，并把填充覆盖为背景色。
outline_socket = None
if OUTLINE_ONLY:
    outline_socket = render_layers.outputs.get("Freestyle")
    if outline_socket is None:
        print("Render Layers 没有 Freestyle 输出口，描边图将退回 Image 通道，并隐藏物体填充。")

if outline_socket is None:
    outline_socket = first_available_output(render_layers, ["Image"])

if OUTLINE_ONLY and outline_socket.name == "Image":
    # Blender 3.2 等版本没有独立 Freestyle 合成输出。
    # 退回 Image 通道时，把物体渲染成背景色，视觉上只留下 Freestyle 线条。
    hidden_fill_mat = make_emission_material("DepthHiddenFillMaterial", WORLD_BACKGROUND_COLOR)
    set_view_layer_material_override(hidden_fill_mat)
    bpy.context.scene.render.film_transparent = False
    file_output2.format.color_mode = "RGB"
elif RENDER_OBJECT_FILL:
    # 普通填充图模式：用可配置颜色覆盖视图层材质，不直接改物体材质。
    fill_mat = make_emission_material("DepthFillEmissionMaterial", OBJECT_FILL_COLOR)
    set_view_layer_material_override(fill_mat)

links.new(outline_socket, view_node2.inputs["Image"])
links.new(outline_socket, file_output2.inputs[0])


# =========================
# 节点布局
# =========================

normalize_node.location = (
    render_layers.location.x + render_layers.width + spacing,
    render_layers.location.y - 4 * normalize_node.height,
)
color_invert_node.location = (
    normalize_node.location.x + normalize_node.width + spacing,
    normalize_node.location.y,
)
view_node.location = (
    color_invert_node.location.x + color_invert_node.width + spacing,
    normalize_node.location.y,
)
file_output.location = (
    view_node.location.x,
    view_node.location.y + file_output.height + spacing,
)
view_node2.location = (
    view_node.location.x,
    file_output.location.y + view_node2.height + spacing,
)
file_output2.location = (
    view_node.location.x,
    view_node2.location.y + file_output2.height + spacing,
)


# =========================
# 执行渲染
# =========================

if RENDER_NOW:
    # Compositor 节点只定义输出流程；真正写出 PNG 需要触发一次渲染。
    bpy.ops.render.render(write_still=True)
