---
layout: page
title: 带皮肤的三维立体图简易教程
permalink: /tutorials/skinned-stereogram/
lang: zh-CN
---

# 带皮肤的三维立体图简易教程：Blender + StereoGen + Krita

普通的单图立体画只用重复纹理表现深度，模型原本的颜色、眼睛和材质细节都会被隐藏。如果希望观看者在看出三维形状后，还能同时看到模型本来的“皮肤”，可以生成两个严格对齐的立体图层：一个由普通纹理生成，负责提供稳定的立体图底纹；另一个由模型的原色渲染图生成，负责保留模型外观。最后在 Krita 中把两层叠加起来。

这篇教程使用 Blender 输出深度图和原色渲染图，使用 [StereoGen](https://apps.microsoft.com/detail/9N7Q261JQW8C) 分别生成普通立体图与原色映射层，再使用 Krita 完成调色和合成。

最终效果如下：

![带皮肤的三维立体图成品]({{ site.baseurl }}/tutorials/skinned/assets/results/composition.png)

## 先理解整个流程

本教程会得到三张中间或结果图：

1. `mapped-material.png`：用模型原色渲染图生成的透明映射层。
2. `base.png`：用普通重复纹理生成的基础立体图。
3. `composition.png`：在 Krita 中合成并调色后的成品。

成功的关键是**对齐**。Blender 输出的深度图和原色渲染图必须使用完全相同的相机、构图和分辨率；StereoGen 生成两个图层时必须使用同一张深度图，并保持相同的输出尺寸；Krita 合成时也不能缩放或移动任何一层。

## 需要的软件

- [Blender](https://www.blender.org/)：准备三维场景，输出深度图和带透明背景的原色渲染图。
- [StereoGen](https://apps.microsoft.com/detail/9N7Q261JQW8C)：把深度图、原色渲染图和普通纹理转换成立体图层。
- [Krita](https://krita.org/)：叠加两个图层，并调整不透明度与底图色相。也可以使用其他支持透明图层的图像编辑器。

本文沿用带轮廓教程中的 Blender 辅助脚本：[下载 `depth.py`]({{ site.baseurl }}/tutorials/outline/depth.py)。更新后的脚本可以从同一场景输出深度图、描边图、原材质图和纯色填充图，并自动配置相机、渲染分辨率、透明背景、视图层及合成节点。

## 第一步：在 Blender 中输出深度图和原色渲染图

打开 Blender，在脚本工作区载入 `depth.py`。这篇教程需要使用脚本顶部的以下输出开关：

```python
EXPORT_DEPTH = True
EXPORT_OUTLINE = True
EXPORT_MATERIAL = True
EXPORT_OBJECT_FILL = False
```

其中，深度图和原材质图参与后续生成；描边图只作为备用素材保留；纯色填充图在本教程中没有使用，因此可以关闭。还可以在脚本顶部调整输出分辨率和相机投影模式：

```python
RESOLUTION_X = 1920
RESOLUTION_Y = 1080
PROJECTION_MODE = "HALF_PERSP"
```

脚本默认使用 `RENDER_NOW = False`，运行后只配置场景和合成节点，不会立刻渲染。先运行脚本，再导入或摆放模型并完成材质与灯光设置。确定构图以后，不要再移动相机；接下来的所有输出都必须来自这个相机视角。

准备完成后，在 Blender 脚本区执行：

```python
bpy.ops.render.render(write_still=True)
```

也可以在所有场景设置完成以后，把 `RENDER_NOW` 改为 `True`，再次运行脚本并直接渲染。脚本默认把 PNG 写到桌面；按上述开关渲染后会得到：

```text
blender_depth0001.png
blender_outline0001.png
blender_material0001.png
```

下面为了更直观，分别把这三张示例素材命名为 `depth-map.png`、`outline-render.png` 和 `material-render.png`。

脚本输出的第一张素材是灰度深度图。本文中的示例文件为：

```text
depth-map.png
```

深度图用亮度表示模型各部分到相机的距离，背景为黑色：

![Blender 输出的深度图]({{ site.baseurl }}/tutorials/skinned/assets/source/depth-map.png)

原材质图由脚本配置的独立视图层生成，不会混入 Freestyle 描边或其他材质覆盖；脚本会把背景设为透明，并以带 Alpha 通道的 RGBA PNG 输出。本文中的示例文件为：

```text
material-render.png
```

![Blender 输出的原色渲染图]({{ site.baseurl }}/tutorials/skinned/assets/source/material-render.png)

示例图片中的章鱼以外均为透明区域。请确认原色渲染图与深度图的像素尺寸完全相同；本教程的两张图片都是 1920×1080。不要单独裁剪、缩放或重新定位模型。

这次 Blender 还输出了一张轮廓图：

![Blender 输出的备用轮廓图]({{ site.baseurl }}/tutorials/skinned/assets/source/outline-render.png)

`outline-render.png` 不参与本教程的生成和合成，只作为备用源素材保留。如果想把轮廓也做成独立图层，可以继续参考[带轮廓的三维立体图教程]({{ site.baseurl }}/tutorials/outline-stereogram/)。

## 第二步：在 StereoGen 中载入深度图和原色渲染图

打开 StereoGen，在“深度图”标签页点击 **打开深度图…**，选择：

```text
depth-map.png
```

![在 StereoGen 中载入深度图]({{ site.baseurl }}/tutorials/skinned/assets/stereogen/01-load-depth-map.png)

切换到“纹理”标签页，点击 **打开纹理…**，选择 Blender 输出的：

```text
material-render.png
```

透明区域会显示为灰白棋盘格：

![在 StereoGen 中载入原色渲染图]({{ site.baseurl }}/tutorials/skinned/assets/stereogen/02-load-material-render.png)

如果 StereoGen 提示深度图与纹理尺寸不同，请回到 Blender 检查输出分辨率。不要在 StereoGen 外单独拉伸其中一张图片，否则模型皮肤会和三维形状错位。

## 第三步：生成原色渲染图的纹理映射层

切换到“立体图”标签页，打开 **选项**，把 **渲染算法**设置为“映射纹理”。本教程示例使用以下设置：

- **观看模式**：发散。
- **纹理布局**：拉伸。
- **视差**：225 / 1920 像素。
- **深度系数**：35%。
- **背景色**：勾选“无颜色”，保留透明背景。
- **自动填满画布**：启用。

这些数值适合本教程的素材，不是所有模型的固定答案。更换模型或分辨率后，可以从较小的视差和深度系数开始逐步调整。

点击 **生成**：

![使用映射纹理算法生成原色映射层]({{ site.baseurl }}/tutorials/skinned/assets/stereogen/03-generate-mapped-material.png)

点击 **另存为…**，以支持透明通道的 PNG 保存为：

```text
mapped-material.png
```

![模型原色映射立体图层]({{ site.baseurl }}/tutorials/skinned/assets/results/mapped-material.png)

单独查看时，这张图会呈现重复、拉伸和断开的模型片段，这是映射纹理算法为匹配视差而生成的正常结果。它不是最终成品，而是稍后叠加到普通立体图上的“皮肤”层。

## 第四步：生成普通纹理的基础立体图

保持当前深度图和输出尺寸不变。切换到“纹理”标签页，把纹理换成一张细节丰富、局部对比适中的普通纹理；可无缝平铺的纹理通常更自然。

回到“立体图”标签页，把 **渲染算法**改为“现代”。为了让两个图层准确重合，继续使用与上一层相同的观看模式、视差和深度系数。本教程示例为：

- **观看模式**：发散。
- **纹理布局**：拉伸。
- **视差**：225 / 1920 像素。
- **深度系数**：35%。
- **纹理起点**：50%。
- **插值**、**去除回声伪影**和**去除噪点**：启用。

点击 **生成**：

![使用普通纹理生成基础立体图]({{ site.baseurl }}/tutorials/skinned/assets/stereogen/04-generate-base-stereogram.png)

点击 **另存为…**，保存为：

```text
base.png
```

![普通纹理的基础立体图]({{ site.baseurl }}/tutorials/skinned/assets/results/base.png)

在进入合成前，最好先确认这张底图能够稳定看出三维形状。映射层只负责增加模型外观，不能修复底图本身不合适的视差或深度设置。

## 第五步：在 Krita 中合成并调色

用 Krita 打开 `base.png`，再把 `mapped-material.png` 作为文件图层或普通图层放在它的上方。两个图层都应保持 1920×1080，并从画布左上角对齐。

把上方的原色映射图层不透明度设为 **85%**：

![在 Krita 中叠加并调整两个立体图层]({{ site.baseurl }}/tutorials/skinned/assets/krita/01-compose-layers.png)

此时模型的眼睛、面部和材质颜色已经进入立体图，但底图的青色与紫色模型不够协调。选中下方的 `base.png` 图层，对底图应用色相曲线调整，把底纹整体调成接近模型的紫色。调整时重点观察两件事：

- 底图与模型皮肤的主色是否协调。
- 明暗对比是否仍足以维持清晰、容易融合的重复纹理。

85% 是本例的起点。如果模型颜色太抢眼，可以继续降低原色映射图层的不透明度；如果皮肤细节太淡，则适当提高。不要缩放、移动或旋转图层。

完成后导出：

```text
composition.png
```

![最终合成的带皮肤三维立体图]({{ site.baseurl }}/tutorials/skinned/assets/results/composition.png)

## 常见问题

### 为什么原色映射层显示成黑色背景？

先确认 Blender 输出的是带 Alpha 通道的 RGBA PNG，然后确认映射纹理选项中的背景色为“无颜色”，最终也保存为 PNG。有些图片查看器会用黑色显示透明区域，可以在 Krita 中检查是否出现透明棋盘格。

### 为什么模型皮肤和三维形状错位？

通常是 Blender 两次输出之间改变了相机或构图，或者某张图片在后期被裁剪、缩放。深度图、原色渲染图、两个 StereoGen 结果和 Krita 画布都必须保持相同尺寸与像素位置。

### 为什么叠加后很难看出立体效果？

先单独检查 `base.png`。如果底图本身就不容易融合，请降低视差或深度系数，或换用细节更均匀的普通纹理。底图稳定后，再调整映射层不透明度。

### 为什么模型颜色不自然？

原色映射层与普通纹理的色相、亮度差距太大时，叠加痕迹会很明显。优先调整底图色相，使它接近模型主色；必要时也可以微调映射层的饱和度和亮度。

### 可以同时加入轮廓吗？

可以。把轮廓图用同一张深度图生成透明轮廓立体图，再作为第三层加入 Krita。务必保持全部图层的尺寸、视差和深度设置一致。具体步骤请参阅[带轮廓的三维立体图教程]({{ site.baseurl }}/tutorials/outline-stereogram/)。

更多参数说明和观看方法，请参阅 [StereoGen 中文用户指南]({{ site.baseurl }}/guide/zh-CN/)。
