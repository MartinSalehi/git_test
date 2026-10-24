# Generic adult male — left hip, buttock and thigh

Open **NX_LEFT_MALE_HIP_THIGH_ASSEMBLY.step** in Siemens NX. It is a STEP AP214 assembly with three named, separate solid components:

| Component | Material group | Geometry |
| --- | --- | --- |
| FEMUR_L | Bone | Complete left femur, including the head and distal condyles |
| HIP_L | Bone | Left hip bone: ilium, ischium and pubis |
| SOFT_TISSUE_L | Combined soft tissue | One solid representing muscle, fat and skin, with fitted femur and hip-bone cavities |

The outer shape includes the left buttock, gluteal fold, groin, thigh and knee region. The top is sectioned above the iliac crest; the medial pelvic boundary is a section through the body's midline. The distal section is below the femoral condyles. The lower leg, complete pelvic girdle and separate patella are outside this model's scope.

## In NX

1. Use **File → Open** and select the assembly STEP file. Retain the assembly structure if your NX version offers that import option.
2. Use **millimetres**. All components share the same coordinates and need no individual positioning or scaling.
3. Hide or make the soft tissue translucent to inspect the skeleton. The separate component STEP files can also be imported individually.
4. Save the imported components and assembly as native NX `.prt` files in your working folder.

Bone and soft tissue have distinct colours and component names. `material_groups.csv` records the two material groups. Mechanical material properties have not been assigned; choose properties appropriate to your application in NX.

These are imported solid B-rep parts. The bone surfaces preserve scan detail with planar faces. The soft tissue has four smooth B-spline outer skin faces, planar end sections and detailed internal bone cavities. The model does not include a native NX feature history or assembly constraints. STEP geometry is checked with OpenCascade; NX is not installed in the generation environment.

## Basis and scale

The external body is an adult male MakeHuman model, approximately **1.748 m** tall before cropping. Its generic hip, buttock and body-volume controls were adjusted to accommodate the anatomy while retaining male proportions. This is a synthetic generic anatomy assembly, not a reconstruction of one person's imaging.

Detailed bone surfaces come from the two user-supplied bone STL files. They were registered to the **left** femur and hip in Z-Anatomy/BodyParts3D, uniformly scaled, positioned using the male model's hip and knee landmarks, and adjusted at the hip joint. The hip has 17° of additional anterior rotation relative to that initial registration and a 0.6% scale adjustment about the hip centre to remove a tiny surface interference.

Coordinate directions: **+X left, +Y posterior, +Z superior**. The origin and height coordinates follow the full body template.

The combined soft-tissue part is a homogeneous continuum. Individual muscles, fat layers and skin thickness are not separately resolved. Rendering colours distinguish the two requested material groups; they are not tissue histology or measured skin pigmentation.

## Checks and included files

- Three separate CAD solids; the tissue solid contains two closed bone cavities.
- All bone vertices and face centres lie within the skin envelope, with minimum sampled cover documented in `assembly_fit_validation.json`.
- No detected bone-to-bone volume overlap.
- Closed meshes with consistent winding; the tissue mesh has an outer shell and two inner cavity shells.
- Smooth skin topology and self-interference checks pass.
- Exported STEP assembly is reopened and checked; see `step_roundtrip_validation.json`.
- Bone CAD simplification distances are recorded in `cad_validation.json`; they are sampled deviations from the dense aligned bone meshes.

The assembly ZIP contains the assembled STEP, matching STL parts, a Blender scene, preview images, validation reports and source credits. Dense bone reference STL files are included separately from the CAD-matched STL files. The three individual component STEP files are supplied in the separate individual-parts ZIP.

## Source credits and licence

- **MakeHuman Community, basemesh hm08 and adult male/hip/buttock target assets**, repository https://github.com/makehumancommunity/makehuman — asset licence CC0 1.0 Universal. The relevant assets explicitly declare CC0. See `MAKEHUMAN_CC0.txt`.
- **Z-Anatomy — The libre 3D atlas of anatomy**, Gauthier Kervyn and collaborators, https://github.com/Z-Anatomy/Models-of-human-anatomy — CC BY-SA 4.0. Its underlying anatomical reference is **BodyParts3D — The Database Center for Life Science**, Kousaku Okubo and collaborators, CC BY-SA 2.1 Japan, as credited by the atlas. See `Z_ANATOMY_LICENSE.txt`.
- Detailed femur and hip scans were supplied by the user in this conversation.

This derivative generic assembly is provided under **CC BY-SA 4.0**, subject to any rights in the user-supplied scans. Preserve these source credits and identify further modifications when redistributing it. No unrelated Z-Anatomy organ models or application code are included.
