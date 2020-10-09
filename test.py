import bpy

import numpy as np
import sys
import os
import os.path as osp
abs_path = os.path.abspath(__file__)
sys.path.append(os.path.dirname(abs_path))
sys.path.append('/opt/anaconda3/lib/python3.7/site-packages/')
import cv2
from config import *
from glob import glob

def clean_cache():
    for item in scene.objects:
        print(item.name)
        if item.type=="MESH":
            item.select_set(True)
        else:
            item.select_set(False)
    bpy.ops.object.delete()
    
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)

    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

    for block in bpy.data.textures:
        if block.users == 0:
            bpy.data.textures.remove(block)

    for block in bpy.data.images:
        if block.users == 0:
            bpy.data.images.remove(block)
# switch on nodes
bpy.context.scene.use_nodes = True
tree = bpy.context.scene.node_tree
links = tree.links
rl = tree.nodes.new('CompositorNodeRLayers')  
alpha_node=tree.nodes.new('CompositorNodeSetAlpha')
depth_output_node = tree.nodes.new('CompositorNodeOutputFile')
color_output_node = tree.nodes.new('CompositorNodeOutputFile')
depth_output_node.format.file_format = 'OPEN_EXR' 
color_output_node.format.file_format = 'PNG' 
# If I cange this to 'OPEN_EXR', I do obtain my output files in the specified folder.
depth_output_node.base_path = ""  
color_output_node.base_path = ""       
scene=bpy.context.scene
scene.render.resolution_x=512
scene.render.resolution_y=512
scene.world.use_nodes=True
scene.render.film_transparent = True
scene.render.image_settings.color_mode = 'RGBA'
#bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
camera=scene.camera
camera.location[0]=1.5
camera.location[1]=-1.5
camera.location[2]=1
camera.rotation_euler[0]=1.1093189716339111
camera.rotation_euler[1]=0
camera.rotation_euler[2]=0.8149281740188599
camera.data.angle=3.14159*50/180
links.new(rl.outputs[0],color_output_node.inputs[0])
links.new(rl.outputs[2],depth_output_node.inputs[0])

for cate in render_cate:
    obj_models_path = glob(
        osp.join(shapenet_path, shapenet_cate[cate], '*', 'models', 'model_normalized.glb'))
    print(obj_models_path)
    for model_path in obj_models_path:
        clean_cache()
        save_dir=os.path.join('./out_test')
        if os.path.exists(save_dir)==False:
            os.makedirs(save_dir)
        save_path1=os.path.join(save_dir,"depth")
        save_path2=os.path.join(save_dir,"color")
        save_path_actual=os.path.join(save_dir,"depth0000.exr")
        if os.path.isfile(save_path_actual)==True:
            print("skipping",save_path1)
            continue
        print("processing",save_path1)

        import_model=bpy.ops.import_scene.gltf(filepath=model_path)
        # for object in scene.objects:
        #     if object.type=='MESH':
        #         object.active_material.use_backface_culling=False
        #         object.data.use_auto_smooth=False
        depth_output_node.file_slots[0].path=save_path1
        color_output_node.file_slots[0].path=save_path2

        # render
        bpy.ops.render.render(write_still=True)
