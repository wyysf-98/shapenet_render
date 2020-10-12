import os
import bpy
import sys
import numpy as np
import os.path as osp
abs_path = os.path.abspath(__file__)
sys.path.append(os.path.dirname(abs_path))
from config import *
sys.path.append(include_path)
from utils import *
from glob import glob
from mathutils import Vector, Matrix


class BlenderRender():
    def __init__(self):
        self.__set_sence()
        self.__set_camera()
        self.__set_lights()
        self.__set_nodes()

    def __clean_cache(self):
        for item in self.scene.objects:
            if item.type == "MESH":
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

    def __set_sence(self):
        bpy.ops.object.delete()

        # Render config
        self.scene = bpy.context.scene
        self.scene.render.engine = render_engine
        self.scene.render.film_transparent = film_transparent

        # Output config
        bpy.context.view_layer.use_pass_normal = True
        bpy.context.view_layer.use_pass_diffuse_color = True

        self.scene.render.image_settings.color_mode = rgb_color_mode
        self.scene.render.image_settings.color_depth = rgb_color_depth
        self.scene.render.image_settings.file_format = rgb_file_format
        self.scene.render.resolution_x = x_res
        self.scene.render.resolution_y = y_res
        self.scene.render.resolution_percentage = res_percentage

    def __set_nodes(self):
        # Set up rendering of depth map.
        self.scene.use_nodes = True
        self.tree = self.scene.node_tree
        links = self.tree.links

        # Clear default nodes
        for n in self.tree.nodes:
            self.tree.nodes.remove(n)

        render_layers = self.tree.nodes.new('CompositorNodeRLayers')

        # Config depth node
        self.depth_file_output = self.tree.nodes.new(
            type="CompositorNodeOutputFile")
        self.depth_file_output.label = 'Depth Output'
        if depth_file_format == 'OPEN_EXR':
            links.new(render_layers.outputs['Depth'],
                      self.depth_file_output.inputs[0])
        else:
            # Remap as other types can not represent the full range of depth.
            remap = self.tree.nodes.new(type="CompositorNodeMapValue")
            remap.offset[0] = -1.0
            remap.use_min = True
            remap.min[0] = depth_min
            remap.use_max = True
            remap.max[0] = depth_max
            links.new(render_layers.outputs['Depth'], remap.inputs[0])
            links.new(remap.outputs[0], self.depth_file_output.inputs[0])
        self.depth_file_output.format.file_format = depth_file_format

        # Config normal node
        self.normal_file_output = self.tree.nodes.new(
            type="CompositorNodeOutputFile")
        self.normal_file_output.label = 'Normal Output'
        if normal_file_format == 'OPEN_EXR':
            links.new(render_layers.outputs['Normal'],
                      self.normal_file_output.inputs[0])
        else:
            scale_normal = self.tree.nodes.new(type="CompositorNodeMixRGB")
            scale_normal.blend_type = 'MULTIPLY'
            scale_normal.use_alpha = normal_use_alpha
            scale_normal.inputs[2].default_value = (0.5, 0.5, 0.5, 1)
            links.new(render_layers.outputs['Normal'], scale_normal.inputs[1])
            bias_normal = self.tree.nodes.new(type="CompositorNodeMixRGB")
            bias_normal.blend_type = 'ADD'
            bias_normal.use_alpha = normal_use_alpha
            bias_normal.inputs[2].default_value = (0.5, 0.5, 0.5, 0)
            links.new(scale_normal.outputs[0], bias_normal.inputs[1])
            links.new(bias_normal.outputs[0],
                      self.normal_file_output.inputs[0])
        self.normal_file_output.format.file_format = normal_file_format

        # Config albedo node
        self.albedo_file_output = self.tree.nodes.new(
            type="CompositorNodeOutputFile")
        self.albedo_file_output.label = 'Albedo Output'
        links.new(render_layers.outputs['DiffCol'],
                  self.albedo_file_output.inputs[0])
        self.albedo_file_output.format.file_format = albedo_file_format

        # Config base path for output
        for output_node in [self.depth_file_output, self.normal_file_output, self.albedo_file_output]:
            output_node.base_path = ''

    def __set_camera(self):
        self.cam = self.scene.objects['Camera']
        self.cam.location = (0, 1, 0)
        self.cam.data.lens = focal_len

        cam_constraint = self.cam.constraints.new(type='TRACK_TO')
        cam_constraint.track_axis = 'TRACK_NEGATIVE_Z'  # TOP DOWN
        cam_constraint.up_axis = 'UP_Y'

    def __set_lights(self):
        for i in range(2):
            azi = np.random.uniform(0, 360)
            ele = np.random.uniform(0, 40)
            dist = np.random.uniform(1, 2)
            x, y, z = obj_location(dist, azi, ele)

            light_name = 'Light{}'.format(i)
            light_data = bpy.data.lights.new(name=light_name, type=light_type)
            light_data.energy = np.random.uniform(1, 10)
            light = bpy.data.objects.new(name=light_name, object_data=light_data)
            bpy.context.collection.objects.link(light)
            bpy.context.view_layer.objects.active = light
            light.location = (x, y, z)
            self.look_at(light, Vector((0, 0, 0)))

    def __import_obj(self, obj_path):
        self.__clean_cache()
        if obj_path.endswith('.obj'):
            print('.obj format may cause artifacts !!!')
            bpy.ops.import_scene.obj(filepath=obj_path)
        elif obj_path.endswith('.glb'):
            bpy.ops.import_scene.gltf(filepath=model_path)
        else:
            raise NotImplementedError('data format not support yet')
        
        for obj in self.scene.objects:
            if obj.type=='MESH':
                obj.active_material.use_backface_culling=use_backface_culling
                obj.active_material.blend_method='OPAQUE'
                obj.data.use_auto_smooth=use_auto_smooth

    def look_at(self, obj, point):
        obj.rotation_mode = 'XYZ'
        loc_obj = obj.location
        direction = point - loc_obj
        # point the cameras '-Z' and use its 'Y' as up
        rot_quat = direction.to_track_quat('-Z', 'Y')

        obj.rotation_euler = rot_quat.to_euler()

    def move_camera(self, cam_loc):
        self.cam.location = cam_loc
        self.look_at(self.cam, Vector((0, 0, 0)))

    def render(self, obj_path):
        obj_cate = obj_path.split('/')[-4]
        obj_name = obj_path.split('/')[-3]

        self.__import_obj(obj_path)

        if sample_type == 'sphere':
            cam_loc = sample_sphere(num_samples, scale, use_half)
        elif sample_type == 'side':
            cam_loc = sample_side(scale)
        else:
            raise NotImplementedError(
                '{} is not implemented !!!'.format(sample_type))

        out_render_paths = []
        for i, loc in enumerate(cam_loc):
            self.move_camera(loc)
            self.scene.render.filepath = osp.join(
                out_path, rgb_out_path, obj_cate, obj_name, '{}.png'.format(i))
            self.depth_file_output.file_slots[0].path = osp.join(
                out_path, depth_out_path, obj_cate, obj_name, str(i))
            self.normal_file_output.file_slots[0].path = osp.join(
                out_path, normal_out_path, obj_cate, obj_name, str(i))
            self.albedo_file_output.file_slots[0].path = osp.join(
                out_path, albedo_out_path, obj_cate, obj_name, str(i))
            out_render_paths.extend([
                osp.join(out_path, depth_out_path, obj_cate, obj_name, str(i)),
                osp.join(out_path, normal_out_path, obj_cate, obj_name, str(i)),
                osp.join(out_path, albedo_out_path, obj_cate, obj_name, str(i)),
            ])
            bpy.ops.render.render(write_still=True)
        return out_render_paths


if __name__ == "__main__":
    if not osp.exists(out_path):
        os.makedirs(out_path)

    my_render = BlenderRender()
    for cate in render_cate:
        obj_models_path = glob(
            osp.join(shapenet_path.replace('glb', 'obj'), shapenet_cate[cate], '*', 'models', 'model_normalized.obj'))

        for obj_model_path in obj_models_path:
            model_path = obj_model_path
            if shapenet_type == 'glb':
                glb_model_path = obj_model_path.replace('obj', 'glb')
                if not osp.exists(glb_model_path):
                    print(".glb model not exsits!!! convert .obj to .glb")
                    convert_obj2glb(obj_model_path, glb_model_path)
                model_path = glb_model_path

            out_paths = my_render.render(model_path)
            prefix_name(out_paths, save_exr)
