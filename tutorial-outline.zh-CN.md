---
layout: page
title: 带轮廓的三维立体图简易教程
permalink: /tutorials/outline-stereogram/
lang: zh-CN
---

# 带轮廓的三维立体图简易教程：Blender + Krita + StereoGen

普通的单图立体画会把三维形状完全藏进重复纹理里，很有“解谜感”，但主体边缘不一定醒目。如果想让隐藏的模型浮现后仍有清晰轮廓，可以把同一份三维场景拆成两层：先生成普通立体图，再生成一张透明背景的轮廓立体图，最后把两层叠在一起。

这篇教程使用 Blender 准备深度图和轮廓图，使用 [StereoGen](https://apps.microsoft.com/detail/9N7Q261JQW8C) 完成两次立体图生成，再用 Krita 合成。整套流程都在本机完成。

最终效果如下：

![带轮廓的三维立体图成品]({{ site.baseurl }}/tutorials/outline/assets/results/composition.png)

## 先理解整个流程

我们需要得到三张图：

1. `base.png`：以普通纹理生成的基础立体图。
2. `outline.png`：以透明轮廓图作为映射纹理生成的轮廓层。
3. `composition.png`：把前两张图叠加后的成品。

成功的关键只有两个：深度图与轮廓图必须使用完全相同的相机和构图；在 StereoGen 中生成两层时，也必须使用同一张深度图。这样合成后，轮廓才会准确落在三维主体的边缘上。

## 需要的软件

- [Blender](https://www.blender.org/)：导入三维模型，输出深度图和轮廓图。
- [Krita](https://krita.org/)：把白底轮廓清理成透明图，并合成最终结果。也可以换用 Photoshop 或其他支持透明图层的图像编辑器。
- [StereoGen](https://apps.microsoft.com/detail/9N7Q261JQW8C)：从深度图和纹理生成单图立体画。

本文还提供一份 Blender 辅助脚本：[下载 `depth.py`]({{ site.baseurl }}/tutorials/outline/depth.py)。它会设置相机、渲染分辨率、Freestyle 描边、合成节点和输出文件。

脚本顶部的常用参数如下：

```python
RESOLUTION_X = 1920
RESOLUTION_Y = 1080
OUTLINE_COLOR = (0.0, 0.0, 0.0)
OUTLINE_THICKNESS = 2.0
PROJECTION_MODE = "HALF_PERSP"
```

第一次尝试可以保持默认值。需要调整时，通常只要修改分辨率、轮廓颜色、轮廓粗细和投影模式。

## 第一步：在 Blender 中输出深度图和轮廓图

打开 Blender，在脚本工作区载入并运行 `depth.py`。脚本会设置场景和输出节点，并把输出目录设为桌面。

接着导入你的三维模型。此后只移动、旋转或缩放模型，让它进入画面，**不要移动相机**。深度图和轮廓图必须来自同一个视角；相机一旦变化，最终叠加的轮廓就会错位。

摆放完成后，在 Blender 脚本区执行：

```python
bpy.ops.render.render(write_still=True)
```

渲染完成后，桌面上会出现：

```text
blender_depth0001.png
blender_outline0001.png
```

深度图用灰度表达距离，通常越亮越靠近观察者：

![Blender 输出的深度图]({{ site.baseurl }}/tutorials/outline/assets/source/blender_depth0001.png)

轮廓图与深度图使用相同的画幅和构图：

![Blender 输出的轮廓图]({{ site.baseurl }}/tutorials/outline/assets/source/blender_outline0001.png)

如果 Blender 已经输出了透明背景的轮廓 PNG，可以直接跳到第三步。如果得到的是白底黑线，先进行下一步清理。

## 第二步（可选）：在 Krita 中去掉轮廓背景

用 Krita 打开 `blender_outline0001.png`，把图层转换为选区蒙版：

![在 Krita 中把图层转换为选区蒙版]({{ site.baseurl }}/tutorials/outline/assets/krita/01-convert-layer-to-selection-mask.png)

对白底黑线的图片反向选择，再用需要的轮廓色填充：

![在 Krita 中反向选择并填充轮廓]({{ site.baseurl }}/tutorials/outline/assets/krita/02-invert-selection-fill-outline.png)

把结果导出为支持透明度的 PNG：

```text
blender_outline0001-clean.png
```

清理后的图片只保留轮廓，其他区域完全透明：

![透明背景的干净轮廓图]({{ site.baseurl }}/tutorials/outline/assets/source/blender_outline0001-clean.png)

不要裁剪或缩放这张图。它必须和深度图具有完全相同的像素尺寸，才能在 StereoGen 的“映射纹理”模式中使用。

## 第三步：用 StereoGen 生成基础立体图

打开 StereoGen，进入“深度图”标签页，点击 **打开深度图…**，选择：

```text
blender_depth0001.png
```

![在 StereoGen 中载入深度图]({{ site.baseurl }}/tutorials/outline/assets/stereogen/01-depth-map-tab.png)

切换到“纹理”标签页，点击 **打开纹理…**，选择一张细节丰富、局部对比适中的纹理。无缝纹理通常更容易获得自然结果。

![在 StereoGen 中载入基础纹理]({{ site.baseurl }}/tutorials/outline/assets/stereogen/02-texture-tab-base-texture.png)

切换到“立体图”标签页，打开 **选项**，建议先这样设置：

- **渲染算法**：选择“现代”。
- **观看模式**：通常选择“发散”（平行眼）；如果作品面向交叉眼观看者，选择“会聚”。
- **视差**和**深度系数**：先使用默认值，再逐步增加。数值太大反而不容易看清立体效果。
- **自动生成**：处理大图时可以先关闭，调整完成后再手动生成。

点击 **生成**。如果三维效果太弱或太难融合，调整视差、深度系数后重新生成。

![使用 StereoGen 的现代算法生成基础立体图]({{ site.baseurl }}/tutorials/outline/assets/stereogen/03-stereogram-options-modern.png)

确认结果后点击 **另存为…**，保存为：

```text
base.png
```

![基础立体图]({{ site.baseurl }}/tutorials/outline/assets/results/base.png)

## 第四步：用 StereoGen 生成透明轮廓层

保持 StereoGen 打开，不要更换深度图，也不要改变输出尺寸。切换到“纹理”标签页，点击 **打开纹理…**，把纹理换成：

```text
blender_outline0001-clean.png
```

![在 StereoGen 中载入透明轮廓纹理]({{ site.baseurl }}/tutorials/outline/assets/stereogen/04-texture-tab-outline-alpha.png)

回到“立体图”标签页，在选项中设置：

- **渲染算法**：选择“映射纹理”。
- **背景色**：选择“无颜色”，保留透明背景。
- **自动填满画布**：建议启用，让 StereoGen 自动重复处理，直到画布不再获得新像素。
- 如果关闭“自动填满画布”，请适当增大 **重复次数**，避免轮廓铺不满。

映射纹理模式要求深度图和纹理的宽、高完全一致。如果 StereoGen 提示尺寸不同，请回到 Krita 检查是否误裁剪或缩放了轮廓图。

点击 **生成**：

![使用 StereoGen 生成透明轮廓立体图]({{ site.baseurl }}/tutorials/outline/assets/stereogen/05-mapped-texture-transparent.png)

点击 **另存为…**，务必保存为支持透明通道的 PNG：

```text
outline.png
```

![透明背景的轮廓立体图]({{ site.baseurl }}/tutorials/outline/assets/results/outline.png)

## 第五步：在 Krita 中合成成品

用 Krita 打开 `base.png`，再把 `outline.png` 作为新图层放到基础图上方：

![在 Krita 中添加轮廓文件图层]({{ site.baseurl }}/tutorials/outline/assets/krita/03-add-outline-as-file-layer.png)

此时轮廓已经跟随隐藏的三维结构排列。你还可以继续调整：

- 降低轮廓图层的不透明度，让线条更自然。
- 尝试不同的图层混合模式。
- 给轮廓重新着色，使它与基础纹理协调。
- 保持 100% 不透明，得到更醒目的黑色描边效果。

最后导出：

```text
composition.png
```

![最终合成的带轮廓三维立体图]({{ site.baseurl }}/tutorials/outline/assets/results/composition.png)

## 常见问题

### 为什么轮廓和立体形状错位？

最常见的原因是两次 Blender 输出之间移动了相机或模型，或者在 Krita 中裁剪、缩放了轮廓图。深度图和轮廓图必须来自同一个构图，并保持相同像素尺寸。

### 为什么轮廓不明显？

可以在 `depth.py` 中增大 `OUTLINE_THICKNESS`，也可以在合成时提高轮廓图层不透明度、改变颜色或混合模式。建议先从较细的轮廓开始，太粗的线条会遮住基础纹理。

### 为什么透明轮廓没有铺满画布？

优先启用 StereoGen 的“自动填满画布”。如果需要手动控制，则关闭该选项并增大“重复次数”。

### 为什么导出的轮廓层变成了实色背景？

确认映射纹理的背景色是“无颜色”，并把结果保存为 PNG。JPEG 不支持透明通道。

### 每次调整都要等很久怎么办？

先关闭“自动生成”，完成一组参数调整后再点击“生成”。调试时也可以先降低 Blender 输出分辨率，确定效果后再生成大图。

## 下一步

熟悉这套流程后，可以尝试彩色轮廓、不同粗细的多层轮廓，或者把文字和图标做成透明映射纹理。只要始终保持深度图与轮廓素材严格对齐，StereoGen 就能把它们变成可独立编辑的立体图层。

更多参数说明和观看方法，请参阅 [StereoGen 中文用户指南]({{ site.baseurl }}/guide/zh-CN/)。
