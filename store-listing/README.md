# Microsoft Store listing assets

These files are customer-visible publishing metadata uploaded manually to the
Microsoft Store listing. They must not be copied into the MSIX package's
`Assets/` directory.

Screenshots are grouped by Store listing locale. The current `en-US` set uses
English application UI and is ordered with generated results first, followed
by the two input steps.

| Order | File | Suggested Partner Center caption |
|---:|---|---|
| 1 | `en-US/screenshots/01-modern-stereogram-light.png` | Generate detailed single-image stereograms with the Modern renderer. |
| 2 | `en-US/screenshots/02-mapped-texture-dark.png` | Create mapped-texture stereograms with transparent backgrounds and fine-grained controls. |
| 3 | `en-US/screenshots/03-depth-map-light.png` | Load and inspect high-resolution depth maps before rendering. |
| 4 | `en-US/screenshots/04-texture-light.png` | Add a custom texture to control the stereogram's visual style. |
| 5 | `en-US/screenshots/05-mapped-texture-source-dark.png` | See the transparent texture used to create the mapped-texture result. |

The `zh-CN/screenshots/` directory contains the same sequence with Simplified
Chinese application UI:

| Order | File |
|---:|---|
| 1 | `zh-CN/screenshots/01-modern-stereogram-light.png` |
| 2 | `zh-CN/screenshots/02-mapped-texture-dark.png` |
| 3 | `zh-CN/screenshots/03-depth-map-light.png` |
| 4 | `zh-CN/screenshots/04-texture-light.png` |
| 5 | `zh-CN/screenshots/05-mapped-texture-source-dark.png` |

All current screenshots are 2560 x 1600 PNG files. The texture-input image has
substantial empty space; it is valid for submission but is the first candidate
to replace if a stronger texture preview is captured later.
