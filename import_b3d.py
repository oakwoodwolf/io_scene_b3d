#!/usr/bin/python3
# by Joric, https://github.com/joric/io_scene_b3d

try:
    from B3DParser import *
except:
    pass

try:
    from .B3DParser import *
    import bpy
    import mathutils
    from bpy_extras.image_utils import load_image
    from bpy_extras.io_utils import unpack_list, unpack_face_list
    import bmesh
except:
    pass

def flip(v):
    return ((v[0],v[2],v[1]) if len(v)<4 else (v[0], v[1],v[3],v[2]))

def flip_all(v):
    return [y for y in [flip(x) for x in v]]

material_mapping = {}
weighting = {}

"""
def make_skeleton(node):

    objName = 'armature'
    a = bpy.data.objects.new(objName, bpy.data.armatures.new(objName))

    armatures.append(a);
    ctx.scene.collection.objects.link(a)

    for i in bpy.context.selected_objects: i.select_set(state=False)

    a.select_set(state=True)
    a.show_in_front = True
    a.data.display_type = 'STICK'

    bpy.context.view_layer.objects.active = a

    bpy.ops.object.mode_set(mode='EDIT',toggle=False)

    bones = {}

    # copy bones positions from precalculated objects
    for bone_id, (name, pos, rot, parent_id) in enumerate(bonesdata):
        if name not in bpy.data.objects:
            return

        ob = bpy.data.objects[name]
        #if parent_id != -1: name = ob.parent.name
        bone = a.data.edit_bones.new(name)
        bones[bone_id] = bone
        v = ob.matrix_world.to_translation()

        # use short segment as a bone (smd-like hierarchy), will convert later
        bone.tail = ob.matrix_world.to_translation()
        bone.head = (v[0]-0.01,v[1],v[2])

        if parent_id != -1:
            bone.parent = bones[parent_id]
            #bone.head = ob.parent.matrix_world.to_translation()

    # delete all objects with the same names as the bones
    for name, pos, rot, parent_id in bonesdata:
        try:
            bpy.data.objects.remove(bpy.data.objects[name])
        except:
            pass

    bpy.ops.object.mode_set(mode='OBJECT')

    #for i in bpy.context.selected_objects: i.select = False #deselect all objects
    for i in bpy.context.selected_objects: i.select_set(state=False) #deselect all objects #2.8 fails

    # get parent mesh (hardcoded so far)
    objName = 'anim'
    if objName in bpy.data.objects.keys():
        ob = bpy.data.objects[objName]
    else:
        return

    # apply armature modifier
    modifier = ob.modifiers.new(type="ARMATURE", name="armature")
    modifier.object = a

    # create vertex groups
    for bone in a.data.bones.values():
        group = ob.vertex_groups.new(name=bone.name)
        if bone.name in weighting.keys():
            for vertex_id, weight in weighting[bone.name]:
                #vertex_id = remaps[objName][vertex_id]
                group_indices = [vertex_id]
                group.add(group_indices, weight, 'REPLACE')


    actionName = 'default_action'
    action = bpy.data.actions.new(actionName)
    action.use_fake_user = True

    a.animation_data_create()
    a.animation_data.action = action


    #action.fps = 30fps if fps else 30
    bpy.context.scene.render.fps = 60
    bpy.context.scene.render.fps_base = 1

    #ops.object.mode_set(mode='POSE')
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = node.frames - 1


    ## ANIMATION!
    bone_string = 'Bip01'

    curvesLoc = None
    curvesRot = None
    bone_string = "pose.bones[\"{}\"].".format(bone.name)
    group = action.groups.new(name=bone_string)

    for bone_id, (name, keys, rot, parent_id) in enumerate(bonesdata):
        for frame in range(node.frames):
            # (unoptimized) walk through all keys and select the frame
            for key in keys:
                if key.frame==frame:
                    pass
                    #print(name, key)
    for keyframe in range(node.frames):
        if curvesLoc and curvesRot: break
        if keyframe.pos and not curvesLoc:
            curvesLoc = []
            for i in range(3):
                curve = action.fcurves.new(data_path=bone_string + "location",index=i)
                curve.group = group
                curvesLoc.append(curve)
        if keyframe.rot and not curvesRot:
            curvesRot = []
            for i in range(3 if smd.rotMode == 'XYZ' else 4):
                curve = action.fcurves.new(data_path=bone_string + "rotation_" + ("euler" if smd.rotMode == 'XYZ' else "quaternion"),index=i)
                curve.group = group
                curvesRot.append(curve)


    for i in range(3):
        curve = action.fcurves.new(data_path=bone_string + "location",index=i)
        group = action.groups.new(name=bone_name)
        curve.group = group

    location = (10,50,100)
    for frame in range(node.frames):
        for i in range(3):
            curve.keyframe_points.add(1)
            curve.keyframe_points[-1].co = [frame, location[i]]

    curve = action.fcurves.new(data_path=bone_string + "rotation_quaternion",index=i)
    group = action.groups.new(name=bone_name)
    curve.group = group

    rotation = (1,0,1,0)
        for i in range(4):
          curvesRot[i].keyframe_points.add(1)
          curvesRot[i].keyframe_points[-1].co = [keyframe.frame, bone.rotation_quaternion[i]]

    #curve = action.fcurves.new(data_path=bone_string + "rotation_quaternion",index=i)
"""

def import_mesh(node, parent):
    global material_mapping

    mesh = bpy.data.meshes.new(node.name)

    # join face arrays
    faces = []
    for face in node.faces:
        faces.extend(face.indices)

    # create mesh from data
    mesh.from_pydata(flip_all(node.vertices), [], flip_all(faces))

    # assign normals
    mesh.vertices.foreach_set('normal', unpack_list(node.normals))

    # create object from mesh
    ob = bpy.data.objects.new(node.name, mesh)

    # assign uv coordinates
    bpymesh = ob.data
    uvs0 = [(0,0) if len(uv) < 2 else (uv[0], 1-uv[1]) for uv in node.uvs]
    uvs1 = [(0,0) if len(uv) < 4 else (uv[2], 1-uv[3]) for uv in node.uvs]

    uvlist0 = [i for poly in bpymesh.polygons for vidx in poly.vertices for i in uvs0[vidx]]
    uvlist1 = [i for poly in bpymesh.polygons for vidx in poly.vertices for i in uvs1[vidx]]
    bpymesh.uv_layers.new(name="UV0").data.foreach_set('uv', uvlist0)
    bpymesh.uv_layers.new(name="UV1").data.foreach_set('uv', uvlist1)
    # assign color attributes
    colors = []
    for poly in bpymesh.polygons:
        for cidx in poly.vertices:
            rgba = node.rgba[cidx] if cidx < len(node.rgba) else (1.0, 1.0, 1.0, 1.0)  # fallback white
            colors.extend(rgba)
    bpymesh.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='CORNER').data.foreach_set("color", colors)
    # adding object materials (insert-ordered)
    for key, value in material_mapping.items():
        ob.data.materials.append(bpy.data.materials[value])

    # assign material_indexes
    poly = 0
    for face in node.faces:
        for _ in face.indices:
            ob.data.polygons[poly].material_index = face.brush_id
            poly += 1

    return ob

def select_recursive(root):
    for c in root.children:
        select_recursive(c)
    root.select_set(state=True)

def make_armature_recursive(root, a, parent_bone):
    bone = a.data.edit_bones.new(root.name)
    v = root.matrix_world.to_translation()
    bone.tail = v
    # bone.head = (v[0]-0.01,v[1],v[2]) # large handles!
    bone.parent = parent_bone
    if bone.parent:
        bone.head = bone.parent.tail
    parent_bone = bone
    for c in root.children:
        make_armature_recursive(c, a, parent_bone)

def make_armatures():
    global ctx
    global imported_armatures, weighting

    for dummy_root in imported_armatures:
        objName = 'armature'
        a = bpy.data.objects.new(objName, bpy.data.armatures.new(objName))
        ctx.scene.collection.objects.link(a)
        for i in bpy.context.selected_objects: i.select_set(state=False)
        a.select_set(state=True)
        a.show_in_front = True
        a.data.display_type = 'OCTAHEDRAL'
        bpy.context.view_layer.objects.active = a

        bpy.ops.object.mode_set(mode='EDIT',toggle=False)
        make_armature_recursive(dummy_root, a, None)
        bpy.ops.object.mode_set(mode='OBJECT',toggle=False)

        # set ob to mesh object
        ob = dummy_root.parent
        a.parent = ob

        # delete dummy objects hierarchy
        for i in bpy.context.selected_objects: i.select_set(state=False)
        select_recursive(dummy_root)
        bpy.ops.object.delete(use_global=True)

        # apply armature modifier
        modifier = ob.modifiers.new(type="ARMATURE", name="armature")
        modifier.object = a

        # create vertex groups
        for bone in a.data.bones.values():
            group = ob.vertex_groups.new(name=bone.name)
            if bone.name in weighting.keys():
                for vertex_id, weight in weighting[bone.name]:
                    group_indices = [vertex_id]
                    group.add(group_indices, weight, 'REPLACE')
        a.parent.data.update()

def import_bone(node, parent=None):
    global imported_armatures, weighting
    # add dummy objects to calculate bone positions later
    ob = bpy.data.objects.new(node.name, None)

    # fill weighting map for later use
    w = []
    for vert_id, weight in node['bones']:
        w.append((vert_id, weight))
    weighting[node.name] = w

    # check parent, add root armature
    if parent and parent.type=='MESH':
        imported_armatures.append(ob)

    return ob

def import_node_recursive(node, parent=None):
    ob = None

    if 'vertices' in node and 'faces' in node:
        ob = import_mesh(node, parent)
    elif 'bones' in node:
        ob = import_bone(node, parent)
    elif node.name:
        ob = bpy.data.objects.new(node.name, None)

    if ob:
        ctx.scene.collection.objects.link(ob)

        if parent:
            ob.parent = parent

        ob.rotation_mode='QUATERNION'
        ob.rotation_quaternion = flip(node.rotation)
        ob.scale = flip(node.scale)
        ob.location = flip(node.position)

    for x in node.nodes:
        import_node_recursive(x, ob)

def load_b3d(filepath,
             context,
             IMPORT_CONSTRAIN_BOUNDS=10.0,
             IMAGE_SEARCH=True,
             APPLY_MATRIX=True,
             global_matrix=None):

    global ctx
    global material_mapping

    ctx = context
    data = B3DTree().parse(filepath)

    # load images
    images = {}
    imageflags = {}
    dirname = os.path.dirname(filepath)
    for i, texture in enumerate(data['textures'] if 'textures' in data else []):
        texture_name = os.path.basename(texture['name'])
        for mat in data.materials:
            for x in range(len(mat.tids)):
                if mat.tids[x]==i:
                    images[i] = (texture_name, load_image(texture_name, dirname, check_existing=True,
                        place_holder=False, recursive=IMAGE_SEARCH))
                    imageflags[i] = texture['flags'] if 'flags' in texture else []

    # create materials
    material_mapping = {}
    for i, mat in enumerate(data.materials if 'materials' in data else []):
        material = bpy.data.materials.new(mat.name)
        material_mapping[i] = material.name
        material.diffuse_color = mat.rgba
        if mat.fx & 16:
            material.use_backface_culling = False
            material.use_backface_culling_shadow = False
        else:
            material.use_backface_culling = True
            material.use_backface_culling_shadow = True
        material.blend_method = 'BLEND' if mat.rgba[3] < 1.0 else 'OPAQUE'

        tid = mat.tids[0] if len(mat.tids) else -1

        if tid in images:
            name, image = images[tid]
            flags = imageflags[tid]

            texture = bpy.data.textures.new(name=name, type='IMAGE')
            material.use_nodes = True
            bsdf = material.node_tree.nodes["Principled BSDF"]
            texImage = material.node_tree.nodes.new('ShaderNodeTexImage')
            texImage.image = image
            if flags & 64:
                texImage.projection = 'SPHERE'
            elif flags & 128:
                texImage.projection = 'BOX'
            if flags & 48:
                texImage.extension = 'EXTEND'
            elif flags & 24576:
                texImage.extension = 'MIRROR'
            material.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
            if (flags & 4):
                material.blend_method = 'CLIP'
                material.node_tree.links.new(bsdf.inputs['Alpha'], texImage.outputs['Alpha'])
            elif (flags & 2):
                material.blend_method = 'BLEND'
                material.node_tree.links.new(bsdf.inputs['Alpha'], texImage.outputs['Alpha'])


    global imported_armatures, weighting
    imported_armatures = []
    weighting = {}

    import_node_recursive(data)
    make_armatures()

def load(operator,
         context,
         filepath="",
         constrain_size=0.0,
         use_image_search=True,
         use_apply_transform=True,
         global_matrix=None,
         ):

    load_b3d(filepath,
             context,
             IMPORT_CONSTRAIN_BOUNDS=constrain_size,
             IMAGE_SEARCH=use_image_search,
             APPLY_MATRIX=use_apply_transform,
             global_matrix=global_matrix,
             )

    return {'FINISHED'}
