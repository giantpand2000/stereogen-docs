---
layout: page
title: StereoGen User Guide
permalink: /guide/en-US/
lang: en-US
---

# StereoGen User Guide

StereoGen is a desktop application for creating single-image stereograms
(autostereograms) from a depth map and a texture. Generation runs entirely on
your computer. No account is required, and the app does not upload your input
images or results to the developer's servers.

![A single-image stereogram generated with the Modern algorithm]({{ site.baseurl }}/store-listing/en-US/screenshots/01-modern-stereogram-light.png)

*A single-image stereogram generated with the Modern algorithm.*

## System requirements and installation

- Windows 10 or Windows 11.
- Installation from Microsoft Store is recommended for signed installation and updates.
- The interface uses the system Microsoft WebView2 runtime. Windows 11 normally includes it; follow the Microsoft prompt if installation or an update is required.

After installation, open **StereoGen** from the Start menu.

## Quick start

1. Select the **Depth Map** tab and click **Open Depth Map…**.
2. Select the **Texture** tab and click **Open Texture…**.
3. Switch to the **Stereogram** tab.
4. Keep the default **Modern** algorithm and click **Generate**.
5. Inspect the result with **Fit**, **100%**, minus, and plus.
6. Click **Save As…** to export PNG or JPEG.

You can also drag files into the app. One image loads into the active tab
(Depth Map by default). If two images are dropped together, the first becomes
the depth map and the second becomes the texture.

### Interface examples

![Inspecting an input image in the Depth Map tab]({{ site.baseurl }}/store-listing/en-US/screenshots/03-depth-map-light.png)

*Step 1: load and inspect the depth map.*

![Inspecting an input image in the Texture tab]({{ site.baseurl }}/store-listing/en-US/screenshots/04-texture-light.png)

*Step 2: load the texture that controls the visual style.*

## Preparing input images

### Depth map

A depth map encodes distance in luminance or a selected color channel. In a
typical map, black is farther away, white is nearer, and gray represents
intermediate depth. Clean edges and smooth gradients generally produce stable results.

### Texture

The texture is the pattern repeated to conceal the depth structure. Detailed,
moderately contrasted, seamless textures are usually easiest to view. Large
flat areas or very strong edges can make the repetition more obvious.

### Supported formats

Inputs may be PNG, JPEG, BMP, GIF, or TGA. TIFF is not currently supported.
Outputs can be saved as PNG or JPEG. Use PNG when transparency must be retained.

For a first test, use [`depth-map.png`]({{ site.baseurl }}/test-assets/depth-map.png)
and [`texture.png`]({{ site.baseurl }}/test-assets/texture.png) from this repository.

## Render algorithms

| Algorithm | When to use it |
|---|---|
| Modern | Recommended general-purpose mode for most depth maps and textures. |
| Classic Left-to-Right | Generates with the classic left-to-right propagation rule. |
| Classic Right-to-Left | Reverses classic propagation for comparison or a different edge behavior. |
| Mapped Texture | Uses a pixel-aligned texture/material map; both inputs must have identical dimensions. |

If you are unsure, start with Modern. Click **Generate** again after changing
an option, or enable **Generate automatically** to refresh after changes.

## Viewing modes

### Diverging (parallel or wall-eyed)

Relax your eyes as if focusing behind the display. When the two guide dots
appear as three, keep that eye position and slowly move your attention down to
the stereogram.

### Converging (cross-eyed)

Focus in front of the display so your eyes cross slightly. When the two guide
dots appear as three, keep the alignment and examine the image below.

If depth appears reversed, switch between Diverging and Converging. For easier
practice, reduce Parallax, move slightly farther from the display, and avoid
forcing focus for long periods. Stop and rest if you experience eye discomfort.

## General options

- **Parallax** controls repeat spacing and depth strength. Increase it gradually; large values can be difficult to fuse.
- **Stretch / Tile** controls how the texture covers the output.
- **Use texture size** uses texture width as the repeat size and disables manual Parallax.
- **Depth factor** controls the amount of depth displacement. Lower values are easier to view.
- **Texture start** positions the texture at the start of the Modern repeat cycle.
- **Interpolate** smooths image sampling and is normally left enabled.
- **Remove echo ghosting** reduces repeated silhouette artifacts.
- **Remove noise** cleans isolated noise in the result.
- **Depth channel** reads depth from Luminance, Red, Green, Blue, or Alpha. Luminance is suitable for ordinary grayscale maps.

Use **Reset to defaults** to restore render settings. Options are stored locally
in the application configuration directory for the next launch.

## Mapped Texture mode

Mapped Texture is designed for material maps and inputs with transparent areas.
The depth map and texture must have exactly the same pixel dimensions.

- **Background color** sets the color used outside the mapped texture.
- **No color** creates a transparent background; export as PNG.
- **Tolerance** controls how closely a pixel must match the background color.
- **Clear background** removes matching pixels using the background color and tolerance.
- **Auto fill canvas** repeats scatter/gather passes until no new pixels are written or the safety limit is reached.
- **Repeat count** manually controls the number of passes when auto fill is disabled.

Use [`material-map.png`]({{ site.baseurl }}/test-assets/material-map.png) for a
Mapped Texture test.

![Transparent texture input used by the Mapped Texture example]({{ site.baseurl }}/store-listing/en-US/screenshots/05-mapped-texture-source-dark.png)

*The transparent texture input used by the Mapped Texture example.*

![Mapped Texture result with a transparent background]({{ site.baseurl }}/store-listing/en-US/screenshots/02-mapped-texture-dark.png)

*A Mapped Texture result; transparent areas appear over the checkerboard.*

## Preview and export

- **− / +** zooms the preview out or in.
- **100%** displays actual pixels.
- **Fit** fits the image inside the current window.
- **Save As…** saves the most recently generated result.

Preview zoom does not change the exported image dimensions.

## Language

In **Options → Interface**, select **Auto (system)**, **English**, or **中文**.

## Troubleshooting

### “No depth map loaded” or “No texture loaded”

Open both input images before generating. The bottom tabs show which image is active.

### Mapped Texture reports different dimensions

Crop or resize the depth map and texture to exactly the same width and height,
then open them again.

### The stereogram has no visible depth

Start with the default Modern and Diverging settings, lower Parallax and Depth
factor, and practice with the test assets. First stabilize the guide dots as
three dots, then move your attention down to the image.

### The result is noisy or has repeated silhouettes

Enable Interpolate, Remove echo ghosting, and Remove noise; reduce Depth factor;
or choose a texture with a more even distribution of detail.

### A transparent result saves with a solid background

Select No color in Mapped Texture mode and save as PNG. JPEG does not support transparency.

## Privacy

StereoGen reads only the images you explicitly open and saves results only to a
location you choose. See the [Privacy Policy]({{ site.baseurl }}/privacy-policy/).

## Reporting a problem

Include the StereoGen version, Windows version, render algorithm, viewing mode,
important options, input formats and dimensions, the complete error message,
and the smallest sample files that reproduce the issue. Do not upload private
images or unpublished artwork unless you intend to share them.
